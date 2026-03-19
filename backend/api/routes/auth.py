import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import (
    create_access_token, create_refresh_token, hash_password,
    rotate_refresh_token, store_refresh_token, verify_password, _hash_token,
)
from backend.models.models import Employee, RefreshToken, RoleEnum

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.employee
    team_id: uuid.UUID | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Employee).where(Employee.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    employee = Employee(
        name=body.name, email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role, team_id=body.team_id,
    )
    db.add(employee)
    await db.flush()
    return await _issue_tokens(db, employee)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.email == body.email))
    employee = result.scalar_one_or_none()
    if not employee or not verify_password(body.password, employee.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not employee.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")
    return await _issue_tokens(db, employee)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    employee, family_id = await rotate_refresh_token(db, body.refresh_token)
    return await _issue_tokens(db, employee, family_id=family_id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = _hash_token(body.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()
    if stored:
        stored.revoked = True
        await db.commit()


async def _issue_tokens(db, employee, family_id=None):
    family_id = family_id or uuid.uuid4()
    access = create_access_token(employee.employee_id, employee.role, employee.team_id)
    raw_refresh, expires_at = create_refresh_token(employee.employee_id, family_id)
    await store_refresh_token(db, employee.employee_id, raw_refresh, family_id, expires_at)
    return TokenResponse(access_token=access, refresh_token=raw_refresh)
