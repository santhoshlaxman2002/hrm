from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.department import Department
from src.models.employee import Employee
from src.models.enums import EmploymentStatus

class DepartmentRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str):
        result = await self.db.execute(
            select(Department)
            .where(
                func.lower(Department.name) == name.lower()
            )
        )

        return result.scalar_one_or_none()

    async def get_by_id(self, department_id: UUID, active_only:bool = True):
        query = select(Department).where(
            Department.id == department_id
        )

        if active_only:
            query = query.where(Department.is_active.is_(True))

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def create(self, department: Department):
        self.db.add(department)
        await self.db.flush()

        return department

    async def list_departments(
        self,
        skip: int,
        limit: int,
        search: str | None = None
    ):
        query = select(Department).where(
            Department.is_active.is_(True)
        )

        count_query = select(func.count(Department.id)).where(
            Department.is_active.is_(True)
        )

        if search:
            search_filter = Department.name.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        query = (
            query
            .order_by(Department.name.asc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        return result.scalars().all(), count_result.scalar_one()

    async def count_active_employees(
        self,
        department_id: UUID
    ) -> int:
        result = await self.db.execute(
            select(func.count(Employee.id)).where(
                Employee.department_id == department_id,
                Employee.employment_status == EmploymentStatus.ACTIVE
            )
        )

        return result.scalar_one()

    async def update(self, department: Department):
        await self.db.flush()
        return department

    async def deactivate(self, department: Department):
        department.is_active = False
        await self.db.flush()

        return department