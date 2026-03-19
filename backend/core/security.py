import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.models.models import Employee, RefreshToken, RoleEnum

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()
ALGORITHM = "RS256"


def hash_password(plain: str) -> str:
    # bcrypt hard limit is 72 bytes
    plain = plain[:72]
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    plain = plain[:72]
    return pwd_context.verify(plain, hashed)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def create_access_token(employee_id: uuid.UUID, role: RoleEnum, team_id) -> str:
    expire = _now() + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MINUTES)
    payload = {
        "sub": str(employee_id),
        "role": role.value,
        "team_id": str(team_id) if team_id else None,
        "exp": expire,
        "iat": _now(),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm=ALGORITHM)


def create_refresh_token(employee_id: uuid.UUID, family_id: uuid.UUID):
    expire = _now() + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS)
    payload = {
        "sub": str(employee_id),
        "family": str(family_id),
        "exp": expire,
        "iat": _now(),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm=ALGORITHM)
    return token, expire


async def get_current_employee(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Employee:
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_PUBLIC_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    emp_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(Employee).where(Employee.employee_id == emp_id))
    employee = result.scalar_one_or_none()
    if not employee or not employee.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return employee


async def require_manager(employee: Employee = Depends(get_current_employee)) -> Employee:
    if employee.role != RoleEnum.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager role required")
    return employee


async def store_refresh_token(db, employee_id, raw_token, family_id, expires_at):
    rt = RefreshToken(
        employee_id=employee_id,
        token_hash=_hash_token(raw_token),
        family_id=family_id,
        expires_at=expires_at,
    )
    db.add(rt)
    await db.commit()


async def rotate_refresh_token(db, raw_token):
    try:
        payload = jwt.decode(raw_token, settings.JWT_PUBLIC_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    token_hash = _hash_token(raw_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()

    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found")

    if stored.revoked:
        family_tokens = (await db.execute(
            select(RefreshToken).where(RefreshToken.family_id == stored.family_id)
        )).scalars().all()
        for t in family_tokens:
            t.revoked = True
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token reuse detected")

    if stored.expires_at.replace(tzinfo=timezone.utc) < _now():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    stored.revoked = True
    await db.flush()

    emp_result = await db.execute(select(Employee).where(Employee.employee_id == stored.employee_id))
    employee = emp_result.scalar_one_or_none()
    if not employee or not employee.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

    await db.commit()
    return employee, stored.family_id