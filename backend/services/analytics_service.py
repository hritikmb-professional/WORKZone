"""
Analytics service — weekly scoring pipeline.
Reads employee meeting/task data from DB, runs all 3 ML models, stores results.
Called by: Lambda analytics-pipeline (weekly) + on-demand after new meetings.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.models import ActionItem, ActionItemStatus, Meeting, ProductivityMetric


class AnalyticsService:

    async def compute_employee_features(
        self,
        db: AsyncSession,
        employee_id: uuid.UUID,
        week_start: datetime,
    ) -> dict:
        """
        Compute all 8 ML features for a given employee-week from DB data.
        """
        week_end = week_start + timedelta(days=7)

        # meeting_hours — sum of meeting durations that week
        meetings_result = await db.execute(
            select(func.sum(Meeting.duration_mins))
            .where(Meeting.created_by == employee_id)
            .where(Meeting.date >= week_start)
            .where(Meeting.date < week_end)
        )
        total_mins = meetings_result.scalar() or 0
        meeting_hours = round(total_mins / 60, 2)

        # tasks_completed — action items marked done that week
        done_result = await db.execute(
            select(func.count(ActionItem.item_id))
            .where(ActionItem.assignee_id == employee_id)
            .where(ActionItem.status == ActionItemStatus.done)
        )
        tasks_completed = done_result.scalar() or 0

        # overdue_tasks ratio
        total_assigned = await db.execute(
            select(func.count(ActionItem.item_id))
            .where(ActionItem.assignee_id == employee_id)
        )
        total = total_assigned.scalar() or 1

        overdue = await db.execute(
            select(func.count(ActionItem.item_id))
            .where(ActionItem.assignee_id == employee_id)
            .where(ActionItem.status != ActionItemStatus.done)
            .where(ActionItem.due_date < datetime.now(timezone.utc))
        )
        overdue_count = overdue.scalar() or 0
        overdue_ratio = round(overdue_count / total, 3)

        # Remaining features — estimated from meeting patterns
        # In production these come from calendar API integration
        focus_blocks = max(0, 10 - int(meeting_hours / 2))
        after_hours = max(0, int((meeting_hours - 15) / 3)) if meeting_hours > 15 else 0
        response_time_avg = round(max(1.0, 8.0 - tasks_completed * 0.3), 2)
        calendar_fragmentation = round(min(1.0, meeting_hours / 35), 3)
        consecutive_meeting_ratio = round(min(1.0, meeting_hours / 40), 3)

        return {
            "meeting_hours": meeting_hours,
            "focus_blocks": focus_blocks,
            "tasks_completed": tasks_completed,
            "overdue_tasks": overdue_ratio,
            "after_hours_activity": after_hours,
            "response_time_avg": response_time_avg,
            "calendar_fragmentation": calendar_fragmentation,
            "consecutive_meeting_ratio": consecutive_meeting_ratio,
        }

    async def score_employee(
        self,
        db: AsyncSession,
        employee_id: uuid.UUID,
        week_start: datetime | None = None,
    ) -> ProductivityMetric:
        """Run all 3 models for one employee-week. Stores result to DB."""
        from ml_models.productivity_model import predict as rf_predict
        from ml_models.burnout_model import predict as if_predict
        from ml_models.clustering import predict as km_predict

        if week_start is None:
            today = datetime.now(timezone.utc)
            week_start = today - timedelta(days=today.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        features = await self.compute_employee_features(db, employee_id, week_start)

        productivity_score = rf_predict(features)
        burnout_result     = if_predict(features)
        cluster_label      = km_predict(features)

        metric = ProductivityMetric(
            employee_id=employee_id,
            week_start=week_start,
            productivity_score=productivity_score,
            burnout_risk=burnout_result["burnout_risk"],
            cluster_label=cluster_label,
            **features,
        )
        db.add(metric)
        await db.commit()
        await db.refresh(metric)
        return metric

    async def get_employee_analytics(
        self,
        db: AsyncSession,
        employee_id: uuid.UUID,
        weeks: int = 12,
    ) -> dict:
        """Return productivity trend + current burnout risk + cluster."""
        result = await db.execute(
            select(ProductivityMetric)
            .where(ProductivityMetric.employee_id == employee_id)
            .order_by(ProductivityMetric.week_start.desc())
            .limit(weeks)
        )
        metrics = result.scalars().all()

        if not metrics:
            return {"employee_id": str(employee_id), "status": "no_data"}

        latest = metrics[0]
        return {
            "employee_id": str(employee_id),
            "current_week": {
                "productivity_score": latest.productivity_score,
                "burnout_risk": latest.burnout_risk,
                "cluster_label": latest.cluster_label,
                "meeting_hours": latest.meeting_hours,
                "focus_blocks": latest.focus_blocks,
                "consecutive_meeting_ratio": latest.consecutive_meeting_ratio,
            },
            "trend": [
                {
                    "week_start": m.week_start.isoformat(),
                    "productivity_score": m.productivity_score,
                    "burnout_risk": m.burnout_risk,
                    "cluster_label": m.cluster_label,
                }
                for m in reversed(metrics)
            ],
        }

    async def get_team_insights(self, db: AsyncSession, team_id: uuid.UUID) -> dict:
        """Aggregated team metrics + cluster distribution + at-risk list."""
        from sqlalchemy import and_
        from backend.models.models import Employee

        # Get all employees in team
        emp_result = await db.execute(
            select(Employee).where(Employee.team_id == team_id)
        )
        employees = emp_result.scalars().all()
        if not employees:
            return {"team_id": str(team_id), "status": "no_employees"}

        emp_ids = [e.employee_id for e in employees]

        # Latest metric per employee
        latest_metrics = []
        for emp_id in emp_ids:
            result = await db.execute(
                select(ProductivityMetric)
                .where(ProductivityMetric.employee_id == emp_id)
                .order_by(ProductivityMetric.week_start.desc())
                .limit(1)
            )
            m = result.scalar_one_or_none()
            if m:
                latest_metrics.append(m)

        if not latest_metrics:
            return {"team_id": str(team_id), "status": "no_data"}

        scores = [m.productivity_score for m in latest_metrics if m.productivity_score]
        risks = [m.burnout_risk for m in latest_metrics if m.burnout_risk]

        # Cluster distribution
        from collections import Counter
        cluster_dist = Counter(m.cluster_label for m in latest_metrics if m.cluster_label)

        # At-risk employees (burnout_risk > 0.6)
        at_risk = [
            {"employee_id": str(m.employee_id), "burnout_risk": m.burnout_risk, "cluster": m.cluster_label}
            for m in latest_metrics
            if m.burnout_risk and m.burnout_risk > 0.6
        ]

        return {
            "team_id": str(team_id),
            "team_size": len(employees),
            "avg_productivity_score": round(sum(scores) / len(scores), 2) if scores else None,
            "avg_burnout_risk": round(sum(risks) / len(risks), 3) if risks else None,
            "cluster_distribution": dict(cluster_dist),
            "at_risk_employees": sorted(at_risk, key=lambda x: -x["burnout_risk"]),
            "at_risk_count": len(at_risk),
        }


analytics_service = AnalyticsService()
