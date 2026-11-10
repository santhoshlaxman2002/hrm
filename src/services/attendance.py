from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.utils import get_attendance_time
from src.models.attendance import Attendance
from src.models.enums import UserRole
from src.models.user import User
from src.repository.attendance import AttendanceRepository


class AttendanceService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = AttendanceRepository(db)

    async def check_in(self, current_user: User):
        try:
            employee = (
                await self.repository.get_employee_by_user_id(
                    current_user.id
                )
            )

            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active employee profile not found",
                )

            now_utc, attendance_date = get_attendance_time()

            existing = (
                await self.repository.get_by_employee_and_date(
                    employee.id,
                    attendance_date,
                )
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already checked in today",
                )

            attendance = Attendance(
                employee_id=employee.id,
                attendance_date=attendance_date,
                check_in=now_utc,
            )

            await self.repository.create(attendance)

            await self.db.commit()
            await self.db.refresh(attendance)

            return attendance

        except IntegrityError:
            await self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attendance already exists for today",
            )

        except Exception:
            await self.db.rollback()
            raise

    async def check_out(self, current_user: User):
        try:
            employee = (
                await self.repository.get_employee_by_user_id(
                    current_user.id
                )
            )

            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active employee profile not found",
                )

            now_utc, attendance_date = get_attendance_time()

            attendance = (
                await self.repository.get_by_employee_and_date_for_update(
                    employee.id,
                    attendance_date,
                )
            )

            if not attendance:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Please check in before checking out",
                )

            if attendance.check_out is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already checked out today",
                )

            if now_utc <= attendance.check_in:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Checkout time must be after check-in time",
                )

            attendance.check_out = now_utc

            await self.db.commit()
            await self.db.refresh(attendance)

            return attendance

        except Exception:
            await self.db.rollback()
            raise

    async def get_my_attendance(
        self,
        user_id: UUID,
        skip: int,
        limit: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        employee = await self.repository.get_employee_by_user_id(
            user_id
        )

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee profile not found",
            )

        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Start date cannot be after end date",
            )

        items, total = await self.repository.list_attendance(
            skip=skip,
            limit=limit,
            employee_id=employee.id,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_team_attendance(
        self,
        user_id: UUID,
        skip: int,
        limit: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        manager = await self.repository.get_employee_by_user_id(
            user_id
        )

        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager employee profile not found",
            )

        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Start date cannot be after end date",
            )

        items, total = await self.repository.get_team_attendance(
            manager_id=manager.id,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def list_all_attendance(
        self,
        skip: int,
        limit: int,
        employee_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Start date cannot be after end date",
            )

        items, total = await self.repository.list_attendance(
            skip=skip,
            limit=limit,
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_attendance_by_id(
        self,
        attendance_id: UUID,
        current_user: User,
    ):
        attendance = await self.repository.get_by_id(
            attendance_id
        )

        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found",
            )

        if current_user.role == UserRole.ADMIN:
            return attendance

        if current_user.role == UserRole.MANAGER:
            manager = await self.repository.get_employee_by_user_id(
                current_user.id
            )

            if (
                not manager
                or attendance.employee.manager_id != manager.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this attendance record",
                )

            return attendance

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this record",
        )