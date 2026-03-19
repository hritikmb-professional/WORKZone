"""
Lambda: transcription-trigger
Trigger: S3 PutObject event on meetings/{meeting_id}/audio.*
Action:  Submits async AWS Transcribe job with speaker diarization.
IAM:     LambdaTranscribeRole — s3:GetObject(meetings/), transcribe:StartTranscriptionJob, s3:PutObject(transcripts/)
"""
import json
import os
import urllib.parse
import boto3

transcribe = boto3.client("transcribe", region_name=os.environ["AWS_REGION"])
S3_BUCKET = os.environ["S3_BUCKET"]


def handler(event, context):
    for record in event["Records"]:
        s3_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        # Extract meeting_id from key: meetings/{meeting_id}/audio.mp3
        parts = s3_key.split("/")
        if len(parts) < 3 or parts[0] != "meetings":
            print(f"Skipping unexpected key: {s3_key}")
            continue

        meeting_id = parts[1]
        ext = s3_key.rsplit(".", 1)[-1].lower()
        format_map = {"mp3": "mp3", "mp4": "mp4", "wav": "wav", "flac": "flac", "ogg": "ogg", "webm": "webm", "m4a": "mp4"}
        media_format = format_map.get(ext, "mp3")

        job_name = f"meeting-{meeting_id}"
        media_uri = f"s3://{S3_BUCKET}/{s3_key}"

        try:
            transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={"MediaFileUri": media_uri},
                MediaFormat=media_format,
                LanguageCode="en-US",
                Settings={
                    "ShowSpeakerLabels": True,
                    "MaxSpeakerLabels": 10,
                },
                OutputBucketName=S3_BUCKET,
                OutputKey=f"transcripts/{meeting_id}/transcript.json",
            )
            print(f"Submitted transcription job: {job_name}")
        except transcribe.exceptions.ConflictException:
            print(f"Job {job_name} already exists — skipping")

    return {"statusCode": 200}
