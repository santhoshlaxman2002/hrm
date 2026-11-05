from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.security import hash_password
from src.models.employee import Employee
from src.models.user import User
from src.models.enums import EmploymentStatus, UserRole
from src.repository.employees import EmployeeRepository
from src.schemas.employees import EmployeeCreate, EmployeeUpdate

class EmployeeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = EmployeeRepository(db=db)

    async def create_employee(self, request: EmployeeCreate):
        try:
            existing_user = await self.repository.get_user_by_email(request.email)

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email address already exists"
                )

            existing_employee = await self.repository.get_employee_by_code(request.employee_code)

            if existing_employee:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Employee code already exists"
                )

            department = await self.repository.get_department(request.department_id)

            if not department:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department does not exists or is inactive",
                )

            if request.manager_id:
                manager = await self.repository.get_manager(request.manager_id)

                if not manager:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Manager does not exists or is inactive"
                    )

                if not manager.user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Manager account is inactive"
                    )

                if manager.user.role != UserRole.MANAGER:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Assigned employee is not a manager"
                    )

            user = User(
                email= request.email.strip().lower(),
                password_hash= hash_password(request.password),
                role= request.role,
                is_active= True
            )

            await self.repository.create_user(user)

            employee = Employee(
                user_id= user.id,
                employee_code= request.employee_code,
                first_name = request.first_name,
                last_name= request.last_name,
                department_id= request.department_id,
                manager_id= request.manager_id,
                designation= request.designation,
                joining_date= request.joining_date,
                employment_status= EmploymentStatus.ACTIVE
            )

            await self.repository.create_employee(employee)

            await self.db.commit()

            result = await self.repository.get_employee_by_id(employee_id=employee.id)

            return result
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Employee could not be created. "
                    "Check duplicate email, employee_code, "
                    "or invalid references."
                )
            )
        except Exception:
            await self.db.rollback()
            raise

    async def get_my_profile(self, user_id: UUID):
        employee = await self.repository.get_employee_by_user_id(user_id=user_id)

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee profile not found"
            )

        return employee

    async def get_employee(
        self,
        employee_id: UUID,
        current_user: User
    ):
        employee = await self.repository.get_employee_by_id(employee_id=employee_id)

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )

        if current_user.role == UserRole.ADMIN:
            return employee

        if current_user.role == UserRole.MANAGER:
            manager = self.repository.get_employee_by_user_id(current_user.id)

            if not manager or employee.manager_id != manager.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this employee"
                )

            return employee

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this employee"
        )

    async def list_employees(
        self,
        skip: int,
        limit: int,
        search: str | None = None,
        department_id: UUID | None = None,
        employment_status: EmploymentStatus | None = None
    ):
        items, total = await self.repository.list_employees(
            skip=skip,
            limit=limit,
            search=search,
            department_id=department_id,
            employment_status=employment_status
        )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    async def get_team(
        self,
        user_id: UUID,
        skip: int,
        limit: int
    ):
        manager = await self.repository.get_employee_by_user_id(user_id=user_id)

        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager employee profile not found"
            )

        items, total = await self.repository.get_direct_reports(manager_id=manager.id, skip=skip, limit=limit)

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    async def update_employee(
        self,
        employee_id: UUID,
        request: EmployeeUpdate
    ):
        try:
            employee = await self.repository.get_employee_by_id(employee_id=employee_id, active_only=False)
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found",
                )

            update_data = request.model_dump(exclude_unset=True)

            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provide at least one field to update"
                )

            if "department_id" in update_data:
                department_id = update_data["department_id"]

                if department_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="Department cannot be null",
                    )

                department = await self.repository.get_department(department_id)

                if not department:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Department does not exist or is inactive",
                    )

            if "manager_id" in update_data:
                manager_id = update_data["manager_id"]

                if manager_id == employee.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="An employee cannot be their own manager"
                    )

                if manager_id is not None:
                    manager = await self.repository.get_manager(manager_id)

                    if not manager or not manager.user.is_active:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Manager does not exist or is inactive",
                        )

                    if manager.user.role != UserRole.MANAGER:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Assigned Employee is not a Manager"
                        )

                    ancestor = manager

                    while ancestor is not None:
                        if ancestor.id == manager.id:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Manager assignment created a reporting cycle"
                            )

                        if ancestor.manager_id is None:
                            break

                        ancestor = await self.repository.get_manager(ancestor.manager_id)

            new_role = update_data.pop("role", None)

            if new_role is not None:
                if(
                    new_role == UserRole.EMPLOYEE
                    and await self.repository.count_direct_reports(employee_id) > 0
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "Cannot change manager role while "
                            "active direct reports are assigned"
                        )
                    )
                employee.user.role = new_role

            for field, value in update_data.items():
                setattr(employee, field, value)

            await self.repository.update_employee(employee=employee)

            await self.db.commit()

            return await self.repository.get_employee_by_id(employee_id=employee.id, active_only=False)

        except IntegrityError:
            await self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee update conflicts with existing data"
            )
        except Exception:
            await self.db.rollback()
            raise

    async def update_employee_status(
        self,
        employee_id: UUID,
        employment_status: EmploymentStatus
    ):
        try:
            employee = await self.repository.get_employee_by_id(employee_id=employee_id, active_only=False)

            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )

            if employment_status == EmploymentStatus.ACTIVE:
                department = await self.repository.get_department(department_id=employee.department_id)

                if not department:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Cannot activate a employee from a inactive department"
                    )

            if employment_status == EmploymentStatus.INACTIVE:
                direct_reports = await self.repository.count_direct_reports(manager_id=employee.id)

                if direct_reports > 0:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "Reassign active direct reports before"
                            "deactivating this manager"
                        )
                    )

            employee.employment_status = employment_status
            employee.user.is_active = (employment_status == EmploymentStatus.ACTIVE)

            await self.db.commit()

            return await self.repository.get_employee_by_id(employee_id=employee.id, active_only=False)
        except Exception:
            await self.db.rollback()
            raise