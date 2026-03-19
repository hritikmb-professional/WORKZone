import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import UUID, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


def _uuid():
    return uuid.uuid4()


class RoleEnum(str, PyEnum):
    employee = "employee"
    manager = "manager"


class ActionItemStatus(str, PyEnum):
    open = "open"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


class Team(Base):
    __tablename__ = "teams"
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    department: Mapped[str | None] = mapped_column(String(120))
    manager_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    employees: Mapped[list["Employee"]] = relationship("Employee", back_populates="team", foreign_keys="Employee.team_id")


class Employee(Base):
    __tablename__ = "employees"
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False, default=RoleEnum.employee)
    team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.team_id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    team: Mapped["Team | None"] = relationship("Team", back_populates="employees", foreign_keys=[team_id])
    productivity_metrics: Mapped[list["ProductivityMetric"]] = relationship("ProductivityMetric", back_populates="employee")
    action_items: Mapped[list["ActionItem"]] = relationship("ActionItem", back_populates="assignee")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", back_populates="employee", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    token_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    employee: Mapped["Employee"] = relationship("Employee", back_populates="refresh_tokens")


class Meeting(Base):
    __tablename__ = "meetings"
    meeting_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_mins: Mapped[int | None] = mapped_column(Integer)
    audio_s3_key: Mapped[str | None] = mapped_column(String(512))
    transcript_s3_key: Mapped[str | None] = mapped_column(String(512))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    analysis: Mapped["MeetingAnalysis | None"] = relationship("MeetingAnalysis", back_populates="meeting", uselist=False)
    action_items: Mapped[list["ActionItem"]] = relationship("ActionItem", back_populates="meeting")


class MeetingAnalysis(Base):
    __tablename__ = "meeting_analysis"
    analysis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    meeting_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("meetings.meeting_id"), unique=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    decisions: Mapped[dict | None] = mapped_column(JSONB)
    action_items: Mapped[dict | None] = mapped_column(JSONB)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="analysis")


class ProductivityMetric(Base):
    __tablename__ = "productivity_metrics"
    metric_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=False)
    week_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    meeting_hours: Mapped[float | None] = mapped_column(Float)
    focus_blocks: Mapped[int | None] = mapped_column(Integer)
    tasks_completed: Mapped[int | None] = mapped_column(Integer)
    overdue_tasks: Mapped[float | None] = mapped_column(Float)
    after_hours_activity: Mapped[int | None] = mapped_column(Integer)
    response_time_avg: Mapped[float | None] = mapped_column(Float)
    calendar_fragmentation: Mapped[float | None] = mapped_column(Float)
    consecutive_meeting_ratio: Mapped[float | None] = mapped_column(Float)
    productivity_score: Mapped[float | None] = mapped_column(Float)
    burnout_risk: Mapped[float | None] = mapped_column(Float)
    cluster_label: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    employee: Mapped["Employee"] = relationship("Employee", back_populates="productivity_metrics")


class ActionItem(Base):
    __tablename__ = "action_items"
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    meeting_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("meetings.meeting_id"), nullable=False)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=True)
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[ActionItemStatus] = mapped_column(Enum(ActionItemStatus), default=ActionItemStatus.open)
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="action_items")
    assignee: Mapped["Employee | None"] = relationship("Employee", back_populates="action_items")
