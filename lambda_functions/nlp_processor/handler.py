"""
Lambda: nlp-processor
Trigger: S3 PutObject on transcripts/{meeting_id}/transcript.json
Action:  Runs full NLP pipeline (BART + spaCy/GPT) → stores to RDS → pushes WebSocket event.
IAM:     LambdaNLPRole — s3:GetObject(transcripts/), rds:Connect, dynamodb:PutItem
"""
import json
import os
import urllib.parse
import uuid
from datetime import datetime, timezone

import boto3
import psycopg2

S3_BUCKET = os.environ["S3_BUCKET"]
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_SECRET_ARN = os.environ["DB_SECRET_ARN"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]

s3 = boto3.client("s3")
secrets = boto3.client("secretsmanager")
dynamodb = boto3.resource("dynamodb")


def get_db_password() -> str:
    resp = secrets.get_secret_value(SecretId=DB_SECRET_ARN)
    secret = json.loads(resp["SecretString"])
    return secret["password"]


def handler(event, context):
    for record in event["Records"]:
        s3_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        # transcripts/{meeting_id}/transcript.json
        parts = s3_key.split("/")
        if len(parts) < 3 or parts[0] != "transcripts":
            continue

        meeting_id = parts[1]
        print(f"Processing NLP for meeting: {meeting_id}")

        # Fetch transcript JSON from S3
        resp = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
        raw_transcript = json.loads(resp["Body"].read())

        # Run NLP pipeline
        from meeting_ai.transcription import parse_transcribe_output, TranscriptResult
        from meeting_ai.summarization import summarize
        from meeting_ai.action_item_extractor import extract_action_items, extract_decisions

        transcript: TranscriptResult = parse_transcribe_output(raw_transcript, meeting_id)
        summary_result = summarize(transcript)
        action_items = extract_action_items(transcript)
        decisions = extract_decisions(transcript)

        # Serialize action items
        items_json = [
            {
                "task": ai.task_text,
                "assignee": ai.assignee_raw,
                "due_date": ai.due_date_raw,
                "confidence": ai.confidence,
                "source": ai.source,
                "needs_review": ai.needs_review,
            }
            for ai in action_items
        ]

        avg_confidence = (
            sum(ai.confidence for ai in action_items) / len(action_items)
            if action_items else 0.0
        )

        # Store to RDS
        password = get_db_password()
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=password, port=5432
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO meeting_analysis (analysis_id, meeting_id, summary, decisions, action_items, confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (meeting_id) DO UPDATE
                    SET summary = EXCLUDED.summary,
                        decisions = EXCLUDED.decisions,
                        action_items = EXCLUDED.action_items,
                        confidence_score = EXCLUDED.confidence_score
                """, (
                    str(uuid.uuid4()),
                    meeting_id,
                    summary_result.summary,
                    json.dumps(decisions),
                    json.dumps(items_json),
                    round(avg_confidence, 3),
                ))

                # Insert individual action items
                for item in items_json:
                    cur.execute("""
                        INSERT INTO action_items (item_id, meeting_id, task_text, confidence, status)
                        VALUES (%s, %s, %s, %s, 'open')
                    """, (str(uuid.uuid4()), meeting_id, item["task"], item["confidence"]))

                # Update meeting duration
                duration_mins = int(transcript.duration_seconds / 60) if transcript.duration_seconds else None
                if duration_mins:
                    cur.execute(
                        "UPDATE meetings SET duration_mins = %s WHERE meeting_id = %s",
                        (duration_mins, meeting_id)
                    )
        conn.close()

        # Push WebSocket notification via DynamoDB stream
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(Item={
            "pk": f"meeting#{meeting_id}",
            "sk": f"event#{datetime.now(timezone.utc).isoformat()}",
            "type": "MEETING_READY",
            "meeting_id": meeting_id,
            "ttl": int(datetime.now(timezone.utc).timestamp()) + 3600,
        })

        print(f"NLP complete for meeting {meeting_id}: {len(action_items)} action items, summary={len(summary_result.summary)} chars")

    return {"statusCode": 200}
