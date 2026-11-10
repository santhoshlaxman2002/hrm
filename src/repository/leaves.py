from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.department import Department
from src.models.employee import Employee
from src.models.enums import LeaveRequestStatus
from src.models.leave_balance import LeaveBalance
from src.models.leave_request import LeaveRequest
from src.models.leave_type import LeaveType
from src.models.user import User


class LeaveRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_leave_type_by_id(
        self,
        leave_type_id: UUID,
        active_only: bool = False,
    ):
        query = select(LeaveType).where(
            LeaveType.id == leave_type_id
        )

        if active_only:
            query = query.where(LeaveType.is_active.is_(True))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_leave_type_by_name(self, name: str):
        result = await self.db.execute(
            select(LeaveType).where(
                func.lower(LeaveType.name) == name.strip().lower()
            )
        )
        return result.scalar_one_or_none()

    async def create_leave_type(self, leave_type: LeaveType):
        self.db.add(leave_type)
        await self.db.flush()
        return leave_type

    async def list_leave_types(
        self,
        skip: int,
        limit: int,
        active_only: bool = True,
    ):
        query = select(LeaveType)

        if active_only:
            query = query.where(LeaveType.is_active.is_(True))

        count_query = select(func.count()).select_from(
            query.order_by(None).subquery()
        )

        total = await self.db.scalar(count_query)

        result = await self.db.execute(
            query.order_by(LeaveType.name.asc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all(), total or 0

    async def update_leave_type(self, leave_type: LeaveType):
        await self.db.flush()
        return leave_type

    async def get_employee_by_user_id(
        self,
        user_id: UUID,
        active_only: bool = True,
    ):
        query = (
            select(Employee)
            .join(User, Employee.user_id == User.id)
            .where(Employee.user_id == user_id)
        )

        if active_only:
            query = query.where(
                Employee.employment_status == "ACTIVE",
                User.is_active.is_(True),
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_employee_by_id(
        self,
        employee_id: UUID,
        active_only: bool = True,
    ):
        query = (
            select(Employee)
            .join(User, Employee.user_id == User.id)
            .where(Employee.id == employee_id)
        )

        if active_only:
            query = query.where(
                Employee.employment_status == "ACTIVE",
                User.is_active.is_(True),
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_leave_balance(
        self,
        employee_id: UUID,
        leave_type_id: UUID,
        year: int,
    ):
        result = await self.db.execute(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.year == year,
            )
        )

        return result.scalar_one_or_none()

    async def get_leave_balance_for_update(
        self,
        employee_id: UUID,
        leave_type_id: UUID,
        year: int,
    ):
        result = await self.db.execute(
            select(LeaveBalance)
            .where(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.year == year,
            )
            .with_for_update()
        )

        return result.scalar_one_or_none()

    async def create_leave_balance(
        self,
        leave_balance: LeaveBalance,
    ):
        self.db.add(leave_balance)
        await self.db.flush()
        return leave_balance

    async def update_leave_balance(
        self,
        leave_balance: LeaveBalance,
    ):
        await self.db.flush()
        return leave_balance

    async def list_employee_balances(
        self,
        employee_id: UUID,
        year: int,
    ):
        result = await self.db.execute(
            select(LeaveBalance)
            .where(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.year == year,
            )
            .order_by(LeaveBalance.created_at.asc())
        )

        return result.scalars().all()

    async def create_leave_request(
        self,
        leave_request: LeaveRequest,
    ):
        self.db.add(leave_request)
        await self.db.flush()
        return leave_request

    async def get_leave_request_by_id(
        self,
        request_id: UUID,
        for_update: bool = False,
    ):
        query = select(LeaveRequest).where(
            LeaveRequest.id == request_id
        )

        if for_update:
            query = query.with_for_update()

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_overlapping_requests(
        self,
        employee_id: UUID,
        start_date: date,
        end_date: date,
        exclude_request_id: UUID | None = None,
    ):
        query = select(LeaveRequest).where(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status.in_([
                LeaveRequestStatus.PENDING,
                LeaveRequestStatus.APPROVED,
            ]),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )

        if exclude_request_id:
            query = query.where(
                LeaveRequest.id != exclude_request_id
            )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_leave_request(
        self,
        leave_request: LeaveRequest,
    ):
        await self.db.flush()
        return leave_request

    async def list_employee_requests(
        self,
        employee_id: UUID,
        skip: int,
        limit: int,
        request_status: LeaveRequestStatus | None = None,
    ):
        query = select(LeaveRequest).where(
            LeaveRequest.employee_id == employee_id
        )

        if request_status:
            query = query.where(
                LeaveRequest.status == request_status
            )

        count_query = select(func.count()).select_from(
            query.order_by(None).subquery()
        )
        total = await self.db.scalar(count_query)

        result = await self.db.execute(
            query.order_by(LeaveRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all(), total or 0

    async def list_team_requests(
        self,
        manager_id: UUID,
        skip: int,
        limit: int,
        request_status: LeaveRequestStatus | None = None,
    ):
        query = (
            select(LeaveRequest)
            .join(
                Employee,
                LeaveRequest.employee_id == Employee.id,
            )
            .where(Employee.manager_id == manager_id)
        )

        if request_status:
            query = query.where(
                LeaveRequest.status == request_status
            )

        count_query = select(func.count()).select_from(
            query.order_by(None).subquery()
        )
        total = await self.db.scalar(count_query)

        result = await self.db.execute(
            query.order_by(LeaveRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all(), total or 0

    async def list_all_requests(
        self,
        skip: int,
        limit: int,
        request_status: LeaveRequestStatus | None = None,
        employee_id: UUID | None = None,
    ):
        query = select(LeaveRequest)

        if request_status:
            query = query.where(
                LeaveRequest.status == request_status
            )

        if employee_id:
            query = query.where(
                LeaveRequest.employee_id == employee_id
            )

        count_query = select(func.count()).select_from(
            query.order_by(None).subquery()
        )
        total = await self.db.scalar(count_query)

        result = await self.db.execute(
            query.order_by(LeaveRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all(), total or 0