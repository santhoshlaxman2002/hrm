from datetime import date
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.models.attendance import Attendance
from src.models.employee import Employee
from src.models.enums import EmploymentStatus

class AttendanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_employee_by_user_id(self, user_id: UUID):
        result = await self.db.execute(
            select(Employee).where(
                Employee.user_id == user_id,
                Employee.employment_status == EmploymentStatus.ACTIVE,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_employee_and_date(self, employee_id: UUID, attendance_date: date):
        result = await self.db.execute(
            select(Attendance).where(
                Attendance.employee_id == employee_id,
                Attendance.attendance_date == attendance_date
            )
        )

        return result.scalar_one_or_none()

    async def get_by_employee_and_date_for_update(self, employee_id: UUID, attendance_date: date):
        result = await self.db.execute(
            select(Attendance).
            where(
                Attendance.employee_id == employee_id,
                Attendance.attendance_date == attendance_date
            )
            .with_for_update()
        )

        return result.scalar_one_or_none()

    async def create(self, attendance: Attendance):
        self.db.add(attendance)
        await self.db.flush()

        return attendance

    async def get_by_id(self, attendance_id: UUID):
        result = await self.db.execute(
            select(Attendance)
            .options(joinedload(Attendance.employee))
            .where(Attendance.id == attendance_id)
        )

        return result.unique().scalar_one_or_none()

    async def list_attendance(
        self,
        skip: int,
        limit: int,
        employee_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        query = (
            select(Attendance)
            .options(joinedload(Attendance.employee))
        )

        count_query = select(func.count(Attendance.id))

        filters = []

        if employee_id:
            filters.append(Attendance.employee_id == employee_id)

        if start_date:
            filters.append(Attendance.attendance_date >= start_date)

        if end_date:
            filters.append(Attendance.attendance_date <= end_date)

        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)

        query = (
            query
            .order_by(Attendance.attendance_date.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        return (
            result.unique().scalars().all(),
            count_result.scalar_one()
        )

    async def get_team_employee_ids(self, manager_id: UUID) -> list[UUID]:
        result = await self.db.execute(
            select(Employee.id).where(
                Employee.manager_id == manager_id,
                Employee.employment_status == EmploymentStatus.ACTIVE
            )
        )

        return list(result.scalars().all())

    async def get_team_attendance(
        self,
        manager_id: UUID,
        skip: int,
        limit: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        employee_ids = await self.get_team_employee_ids(manager_id=manager_id)

        if not employee_ids:
            return [], 0

        return await self.list_attendance(
            skip=skip,
            limit=limit,
            employee_id=None,
            start_date=start_date,
            end_date=end_date
        ) if False else await self._list_for_employees(
            employee_ids,
            skip,
            limit,
            start_date,
            end_date
        )

    async def _list_for_employees(
        self,
        employee_ids: list[UUID],
        skip: int,
        limit: int,
        start_date: date | None,
        end_date: date | None,
    ):
        query = (
            select(Attendance)
            .options(joinedload(Attendance.employee))
            .where(Attendance.employee_id.in_(employee_ids))
        )

        count_query = select(func.count(Attendance.id)).where(
            Attendance.employee_id.in_(employee_ids)
        )

        if start_date:
            query = query.where(
                Attendance.attendance_date >= start_date
            )
            count_query = count_query.where(
                Attendance.attendance_date >= start_date
            )

        if end_date:
            query = query.where(
                Attendance.attendance_date <= end_date
            )
            count_query = count_query.where(
                Attendance.attendance_date <= end_date
            )

        query = (
            query
            .order_by(Attendance.attendance_date.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        return (
            result.unique().scalars().all(),
            count_result.scalar_one()
        )