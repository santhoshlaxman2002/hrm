from uuid import UUID
from sqlalchemy import select, or_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.models.employee import Employee
from src.models.department import Department
from src.models.enums import EmploymentStatus


class EmployeeRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str):
        result = await self.db.execute(
            select(User).where(
                func.lower(User.email) == email.lower()
            )
        )

        return result.scalar_one_or_none()

    async def get_employee_by_code(self, employee_code: str):
        result = await self.db.execute(
            select(Employee).where(
                func.lower(Employee.employee_code) == employee_code.lower()
            )
        )

        return result.scalar_one_or_none()

    async def get_department(self, department_id: UUID):
        result = await self.db.execute(
            select(Department).where(
                Department.id == department_id,
                Department.is_active.is_(True)
            )
        )

        return result.scalar_one_or_none()

    async def get_employee_by_id(self, employee_id: UUID, active_only: bool = True):
        query = (
            select(Employee)
            .options(
                joinedload(Employee.user),
                joinedload(Employee.department)
            )
            .where(Employee.id == employee_id)
        )

        if active_only:
            query = query.where(
                Employee.employment_status == EmploymentStatus.ACTIVE
            )

        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_employee_by_user_id(self, user_id: UUID):
        result = await self.db.execute(
            select(Employee)
            .options(
                joinedload(Employee.user),
                joinedload(Employee.department),
            )
            .where(Employee.user_id == user_id)
        )

        return result.unique().scalar_one_or_none()

    async def get_manager(self, manager_id: UUID):
        result = await self.db.execute(
            select(Employee)
            .options(joinedload(Employee.user))
            .where(
                Employee.id == manager_id,
                Employee.employment_status == EmploymentStatus.ACTIVE
            )
        )

        return result.scalar_one_or_none()

    async def create_employee(self, employee: Employee):
        self.db.add(employee)
        await self.db.flush()
        return employee

    async def create_user(self, user: User):
        self.db.add(user)
        await self.db.flush()
        return user

    async def list_employees(
        self,
        skip: int,
        limit: int,
        search: str | None = None,
        department_id: UUID | None = None,
        employment_status: EmploymentStatus | None = None
    ):
        query = (
            select(Employee)
            .join(User, Employee.user_id == User.id)
            .options(
                joinedload(Employee.user),
                joinedload(Employee.department)
            )
        )

        count_query = (
            select(func.count(Employee.id))
            .join(User, Employee.user_id == User.id)
        )

        filters = []

        if search:
            pattern = f"%{search}%"

            filters.append(
                or_(
                    Employee.first_name.ilike(pattern),
                    Employee.last_name.ilike(pattern),
                    Employee.employee_code.ilike(pattern),
                    User.email.ilike(pattern)
                )
            )

        if department_id:
            filters.append(
                Employee.department_id == department_id
            )

        if employment_status:
            filters.append(
                Employee.employment_status == employment_status
            )

        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)

        query = (
            query
            .order_by(Employee.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        return (
            result.unique().scalars().all(),
            count_result.scalar_one()
        )

    async def get_direct_reports(
        self,
        manager_id: UUID,
        skip: int,
        limit: int
    ):
        query = (
            select(Employee)
            .options(
                joinedload(Employee.user),
                joinedload(Employee.department)
            )
            .where(
                Employee.manager_id == manager_id,
                Employee.employment_status == EmploymentStatus.ACTIVE
            )
            .order_by(Employee.first_name.desc())
            .offset(skip)
            .limit(limit)
        )

        count_query = (
            select(func.count(Employee.id))
            .where(
                Employee.manager_id == manager_id,
                Employee.employment_status == EmploymentStatus.ACTIVE
            )
        )

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        return (
            result.unique().scalars().all(),
            count_result.scalar_one()
        )

    async def count_direct_reports(self, manager_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(Employee.id)).where(
                Employee.manager_id == manager_id,
                Employee.employment_status == EmploymentStatus.ACTIVE
            )
        )

        return result.scalar_one()

    async def update_employee(self, employee: Employee):
        await self.db.flush()
        await self.db.refresh(employee)

        return employee