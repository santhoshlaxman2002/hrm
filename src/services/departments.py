from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.repository.departments import DepartmentRepository
from src.schemas.departments import DepartmentCreate, DepartmentUpdate
from src.models.department import Department

class DepartmentService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = DepartmentRepository(db)

    async def create_department(
        self,
        request: DepartmentCreate
    ):
        try:
            existing = await self.repository.get_by_name(request.name)

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Department already exists"
                )

            department = Department(
                name=request.name,
                description=request.description,
                is_active=True,
            )

            department = await self.repository.create(department=department)

            await self.db.commit()
            await self.db.refresh(department)

            return department
            
        except IntegrityError:
            await self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Department Name already exists"
            )
        except Exception:
            await self.db.rollback()
            raise

    async def get_department(self, department_id: UUID):
        department = await self.repository.get_by_id(
            department_id=department_id
        )

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )

        return department

    async def list_departments(
        self,
        skip: int,
        limit: int,
        search: str | None = None
    ):
        items, total = await self.repository.list_departments(skip, limit, search)

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    async def update_department(
        self,
        department_id: UUID,
        request: DepartmentUpdate
    ):
        try:
            department = await self.repository.get_by_id(department_id=department_id)

            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Department not found"
                )
            update_data = request.model_dump(exclude_unset=True)

            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provide at least one field to update",
                )

            if "name" in update_data:
                new_name = update_data["name"]

                if new_name is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="Department name cannot be null"
                    )

                existing = await self.repository.get_by_name(new_name)

                if existing and existing.id != department.id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Departement name already exists"
                    )

            for field, value in update_data.items():
                setattr(department, field, value)

            department = await self.repository.update(department=department)

            await self.db.commit()
            await self.db.refresh(department)

            return department

        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Department name alreay exists"
            )
        except Exception:
            await self.db.rollback()
            raise

    async def deactivate_department(
        self,
        department_id: UUID
    ):
        try:
            department = await self.repository.get_by_id(department_id=department_id)

            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Department not found"
                )

            active_employee_count = await self.repository.count_active_employees(department_id=department_id)

            if active_employee_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Cannot deactivate department while"
                        "active employees are assigned to it"
                    ),
                )

            await self.repository.deactivate(department=department)

            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise