"""
Analytics API routes.
GET /employee/{id}/analytics  — productivity trend, burnout risk, cluster
GET /team/{id}/insights        — team aggregates, at-risk list, cluster distribution
POST /employee/{id}/score      — trigger on-demand scoring for one employee
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import get_current_employee, require_manager
from backend.models.models import Employee
from backend.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/employee/{employee_id}/analytics")
async def get_employee_analytics(
    employee_id: uuid.UUID,
    weeks: int = 12,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_employee),
) -> dict:
    """
    Returns 12-week productivity trend, current burnout risk, cluster label.
    Employees can only view their own data. Managers can view their team.
    """
    if current_user.role.value == "employee" and current_user.employee_id != employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await analytics_service.get_employee_analytics(db, employee_id, weeks)
    if result.get("status") == "no_data":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analytics data yet")
    return result


@router.get("/team/{team_id}/insights")
async def get_team_insights(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_manager),
) -> dict:
    """
    Manager-only. Returns team productivity aggregates, cluster distribution, at-risk list.
    """
    if current_user.team_id != team_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your team")

    result = await analytics_service.get_team_insights(db, team_id)
    if result.get("status") in ("no_employees", "no_data"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["status"])
    return result


@router.post("/employee/{employee_id}/score", status_code=status.HTTP_202_ACCEPTED)
async def trigger_scoring(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_manager),
) -> dict:
    """
    Manager triggers on-demand ML scoring for an employee.
    Normally runs weekly via Lambda — this is the manual trigger.
    """
    try:
        metric = await analytics_service.score_employee(db, employee_id)
        return {
            "employee_id": str(employee_id),
            "productivity_score": metric.productivity_score,
            "burnout_risk": metric.burnout_risk,
            "cluster_label": metric.cluster_label,
            "week_start": metric.week_start.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
