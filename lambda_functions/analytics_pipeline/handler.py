"""
Lambda: analytics-pipeline
Trigger: CloudWatch Events — every Monday 00:00 UTC
         + on-demand after new meeting NLP completes
Action:  Re-scores all employees using Random Forest + Isolation Forest + KMeans
IAM:     LambdaAnalyticsRole — s3:GetObject(model-artifacts/), rds:Connect, dynamodb:PutItem
"""
import json
import os
import boto3
import psycopg2
import uuid
from datetime import datetime, timedelta, timezone

DB_HOST      = os.environ["DB_HOST"]
DB_NAME      = os.environ["DB_NAME"]
DB_USER      = os.environ["DB_USER"]
DB_SECRET_ARN = os.environ["DB_SECRET_ARN"]
S3_BUCKET    = os.environ["S3_BUCKET"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]

secrets  = boto3.client("secretsmanager")
dynamodb = boto3.resource("dynamodb")


def get_db_password() -> str:
    resp = secrets.get_secret_value(SecretId=DB_SECRET_ARN)
    return json.loads(resp["SecretString"])["password"]


def handler(event, context):
    password = get_db_password()
    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=password, port=5432
    )

    today = datetime.now(timezone.utc)
    week_start = (today - timedelta(days=today.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT employee_id FROM employees WHERE is_active = TRUE")
            employee_ids = [row[0] for row in cur.fetchall()]

    print(f"Scoring {len(employee_ids)} employees for week {week_start.date()}")

    from ml_models.productivity_model import predict as rf_predict
    from ml_models.burnout_model import predict as if_predict
    from ml_models.clustering import predict as km_predict

    scored = 0
    flagged = 0

    with conn:
        with conn.cursor() as cur:
            for emp_id in employee_ids:
                # Fetch features from DB
                cur.execute("""
                    SELECT
                        COALESCE(SUM(duration_mins), 0) / 60.0 as meeting_hours,
                        COUNT(*) as meeting_count
                    FROM meetings
                    WHERE created_by = %s
                    AND date >= %s AND date < %s
                """, (str(emp_id), week_start, week_start + timedelta(days=7)))
                row = cur.fetchone()
                meeting_hours = float(row[0]) if row else 0.0

                cur.execute("""
                    SELECT COUNT(*) FROM action_items
                    WHERE assignee_id = %s AND status = 'done'
                """, (str(emp_id),))
                tasks_completed = cur.fetchone()[0] or 0

                cur.execute("""
                    SELECT COUNT(*) FROM action_items WHERE assignee_id = %s
                """, (str(emp_id),))
                total_tasks = max(cur.fetchone()[0] or 1, 1)

                cur.execute("""
                    SELECT COUNT(*) FROM action_items
                    WHERE assignee_id = %s AND status != 'done' AND due_date < NOW()
                """, (str(emp_id),))
                overdue = cur.fetchone()[0] or 0

                features = {
                    "meeting_hours": meeting_hours,
                    "focus_blocks": max(0, 10 - int(meeting_hours / 2)),
                    "tasks_completed": tasks_completed,
                    "overdue_tasks": round(overdue / total_tasks, 3),
                    "after_hours_activity": max(0, int((meeting_hours - 15) / 3)) if meeting_hours > 15 else 0,
                    "response_time_avg": round(max(1.0, 8.0 - tasks_completed * 0.3), 2),
                    "calendar_fragmentation": round(min(1.0, meeting_hours / 35), 3),
                    "consecutive_meeting_ratio": round(min(1.0, meeting_hours / 40), 3),
                }

                prod_score    = rf_predict(features)
                burnout_data  = if_predict(features)
                cluster_label = km_predict(features)

                cur.execute("""
                    INSERT INTO productivity_metrics
                        (metric_id, employee_id, week_start,
                         meeting_hours, focus_blocks, tasks_completed, overdue_tasks,
                         after_hours_activity, response_time_avg, calendar_fragmentation,
                         consecutive_meeting_ratio, productivity_score, burnout_risk, cluster_label)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (employee_id, week_start) DO UPDATE SET
                        productivity_score = EXCLUDED.productivity_score,
                        burnout_risk = EXCLUDED.burnout_risk,
                        cluster_label = EXCLUDED.cluster_label
                """, (
                    str(uuid.uuid4()), str(emp_id), week_start,
                    features["meeting_hours"], features["focus_blocks"],
                    features["tasks_completed"], features["overdue_tasks"],
                    features["after_hours_activity"], features["response_time_avg"],
                    features["calendar_fragmentation"], features["consecutive_meeting_ratio"],
                    prod_score, burnout_data["burnout_risk"], cluster_label,
                ))
                scored += 1
                if burnout_data["flagged"]:
                    flagged += 1

    conn.close()
    print(f"Scored {scored} employees | {flagged} flagged for burnout review")

    # Notify via DynamoDB
    table = dynamodb.Table(DYNAMODB_TABLE)
    table.put_item(Item={
        "pk": f"analytics#weekly",
        "sk": f"run#{week_start.isoformat()}",
        "type": "ANALYTICS_COMPLETE",
        "scored": scored,
        "flagged": flagged,
        "ttl": int(datetime.now(timezone.utc).timestamp()) + 86400,
    })

    return {"statusCode": 200, "scored": scored, "flagged": flagged}
