from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies.auth import get_current_user
from src.dependencies.permissions import require_roles
from src.models.enums import UserRole

from src.schemas.attendance import (
    AttendanceResponse,
    AttendanceListResponse,
)
from src.services.attendance import AttendanceService


router = APIRouter()


@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def check_in(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AttendanceService(db)

    return await service.check_in(current_user)


@router.post(
    "/check-out",
    response_model=AttendanceResponse,
)
async def check_out(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AttendanceService(db)

    return await service.check_out(current_user)


@router.get(
    "/me",
    response_model=AttendanceListResponse,
)
async def get_my_attendance(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AttendanceService(db)

    return await service.get_my_attendance(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/team",
    response_model=AttendanceListResponse,
)
async def get_team_attendance(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(UserRole.MANAGER)),
):
    service = AttendanceService(db)

    return await service.get_team_attendance(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "",
    response_model=AttendanceListResponse,
)
async def list_all_attendance(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    employee_id: UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(UserRole.ADMIN)),
):
    service = AttendanceService(db)

    return await service.list_all_attendance(
        skip=skip,
        limit=limit,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/{attendance_id}",
    response_model=AttendanceResponse,
)
async def get_attendance(
    attendance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
):
    service = AttendanceService(db)

    return await service.get_attendance_by_id(
        attendance_id=attendance_id,
        current_user=current_user,
    )