"""
Meeting service — orchestrates upload, DB record creation, and pipeline trigger.
"""
import uuid
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.models import ActionItem, ActionItemStatus, Meeting, MeetingAnalysis
from backend.services.s3_service import s3_service


class MeetingService:

    async def create_meeting(
        self,
        db: AsyncSession,
        title: str,
        file: UploadFile,
        created_by: uuid.UUID,
    ) -> dict:
        """
        1. Validate + upload audio to S3
        2. Create Meeting DB record
        3. Return meeting_id and job info for Lambda trigger
        """
        meeting_id = str(uuid.uuid4())
        s3_key = await s3_service.upload_audio(file, meeting_id)

        meeting = Meeting(
            meeting_id=uuid.UUID(meeting_id),
            title=title,
            date=datetime.now(timezone.utc),
            audio_s3_key=s3_key,
            created_by=created_by,
        )
        db.add(meeting)
        await db.commit()
        await db.refresh(meeting)

        return {
            "meeting_id": meeting_id,
            "audio_s3_key": s3_key,
            "status": "processing",
            "message": "Audio uploaded. Transcription pipeline started automatically via S3 trigger.",
        }

    async def get_meeting_summary(self, db: AsyncSession, meeting_id: uuid.UUID) -> dict:
        """Return full analysis: transcript, summary, decisions, action items."""
        result = await db.execute(
            select(Meeting).where(Meeting.meeting_id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        if not meeting:
            return None

        analysis = meeting.analysis
        action_items = await db.execute(
            select(ActionItem).where(ActionItem.meeting_id == meeting_id)
        )
        items = action_items.scalars().all()

        return {
            "meeting_id": str(meeting_id),
            "title": meeting.title,
            "date": meeting.date.isoformat(),
            "duration_mins": meeting.duration_mins,
            "status": "ready" if analysis else "processing",
            "summary": analysis.summary if analysis else None,
            "decisions": analysis.decisions if analysis else [],
            "confidence_score": analysis.confidence_score if analysis else None,
            "action_items": [
                {
                    "item_id": str(item.item_id),
                    "task": item.task_text,
                    "assignee_id": str(item.assignee_id) if item.assignee_id else None,
                    "due_date": item.due_date.isoformat() if item.due_date else None,
                    "status": item.status.value,
                    "confidence": item.confidence,
                    "needs_review": item.confidence < 0.7 if item.confidence else True,
                }
                for item in items
            ],
        }

    async def store_analysis(
        self,
        db: AsyncSession,
        meeting_id: uuid.UUID,
        summary: str,
        decisions: list,
        action_items_data: list,
        confidence_score: float,
        duration_mins: int | None = None,
    ) -> None:
        """Called by Lambda nlp-processor after NLP pipeline completes."""
        # Update meeting duration
        result = await db.execute(select(Meeting).where(Meeting.meeting_id == meeting_id))
        meeting = result.scalar_one_or_none()
        if meeting and duration_mins:
            meeting.duration_mins = duration_mins

        # Store analysis
        analysis = MeetingAnalysis(
            meeting_id=meeting_id,
            summary=summary,
            decisions=decisions,
            action_items=action_items_data,
            confidence_score=confidence_score,
        )
        db.add(analysis)

        # Store individual action items for assignment tracking
        for item in action_items_data:
            ai = ActionItem(
                meeting_id=meeting_id,
                task_text=item["task"],
                confidence=item.get("confidence", 0.5),
                status=ActionItemStatus.open,
            )
            db.add(ai)

        await db.commit()


meeting_service = MeetingService()
