"""
Meeting Intelligence API routes.
POST /upload-meeting — upload audio, trigger pipeline
GET  /meeting/{id}/summary — return full NLP analysis
GET  /meetings/search — full-text search across transcripts
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import get_current_employee
from backend.models.models import Employee
from backend.services.meeting_service import meeting_service

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/upload-meeting", status_code=status.HTTP_202_ACCEPTED)
async def upload_meeting(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_employee),
) -> dict:
    """
    Upload audio file → S3 → Lambda trigger → AWS Transcribe → NLP pipeline.
    Returns immediately with meeting_id. Frontend polls or waits for WebSocket push.
    """
    try:
        result = await meeting_service.create_meeting(
            db=db,
            title=title,
            file=file,
            created_by=current_user.employee_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}")


@router.get("/meeting/{meeting_id}/summary")
async def get_meeting_summary(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_employee),
) -> dict:
    """Return full meeting analysis: transcript, summary, decisions, action items."""
    result = await meeting_service.get_meeting_summary(db, meeting_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return result


@router.get("/meetings/search")
async def search_meetings(
    q: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_employee),
) -> dict:
    """
    Full-text search across meeting summaries via PostgreSQL tsvector.
    Uses GIN index on meeting_analysis.summary_tsv for fast search.
    """
    if len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query too short")

    sql = text("""
        SELECT
            m.meeting_id,
            m.title,
            m.date,
            m.duration_mins,
            ma.summary,
            ts_rank(to_tsvector('english', COALESCE(ma.summary, '')),
                    plainto_tsquery('english', :query)) AS rank
        FROM meetings m
        JOIN meeting_analysis ma ON ma.meeting_id = m.meeting_id
        WHERE to_tsvector('english', COALESCE(ma.summary, '')) @@ plainto_tsquery('english', :query)
        ORDER BY rank DESC
        LIMIT :limit
    """)

    rows = await db.execute(sql, {"query": q, "limit": limit})
    results = [
        {
            "meeting_id": str(r.meeting_id),
            "title": r.title,
            "date": r.date.isoformat(),
            "duration_mins": r.duration_mins,
            "summary_excerpt": r.summary[:300] + "..." if r.summary and len(r.summary) > 300 else r.summary,
            "relevance_score": round(float(r.rank), 4),
        }
        for r in rows
    ]
    return {"query": q, "results": results, "count": len(results)}


@router.patch("/action-items/{item_id}/status")
async def update_action_item_status(
    item_id: uuid.UUID,
    status_value: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_employee),
) -> dict:
    """Update action item status: open | in_progress | done | cancelled."""
    from sqlalchemy import select
    from backend.models.models import ActionItem, ActionItemStatus

    allowed = {s.value for s in ActionItemStatus}
    if status_value not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {allowed}")

    result = await db.execute(select(ActionItem).where(ActionItem.item_id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")

    item.status = ActionItemStatus(status_value)
    await db.commit()
    return {"item_id": str(item_id), "status": status_value}
