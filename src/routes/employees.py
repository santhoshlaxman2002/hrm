from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db
from src.dependencies.audit import get_audit_service
from src.dependencies.auth import get_current_user
from src.dependencies.permissions import require_roles
from src.models.enums import UserRole, EmploymentStatus
from src.schemas.employees import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeStatusUpdate,
    EmployeeResponse,
    EmployeeListResponse
)
from src.services.employees import EmployeeService

router = APIRouter()

@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    request: EmployeeCreate,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(UserRole.ADMIN)),
    audit_service = Depends(get_audit_service)
):
    service = EmployeeService(db=db)

    employee = await service.create_employee(request=request)

    await audit_service.log_event(
        actor_user_id= str(current_user.id),
        action= "EMPLOYEE_CREATED",
        entity_type= "EMPLOYEE",
        entity_id= str(employee.id),
        metadata= {
            "employee_code": employee.employee_code,
            "department_id": str(employee.department_id),
        },
        request=http_request,
    )

    return employee

@router.get(
    "",
    response_model=EmployeeListResponse
)
async def list_employee(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
    department_id: UUID | None = None,
    employment_status: EmploymentStatus | None = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(UserRole.ADMIN))
):
    service = EmployeeService(db=db)

    return await service.list_employees(
        skip=skip,
        limit=limit,
        search=search,
        department_id=department_id,
        employment_status=employment_status
    )

@router.get(
    "/me/team",
    response_model=EmployeeListResponse
)
async def get_my_team(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=1, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(UserRole.MANAGER))
):
    service = EmployeeService(db=db)

    return await service.get_team(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

@router.get(
    "/me",
    response_model=EmployeeResponse
)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = EmployeeService(db=db)

    return await service.get_my_profile(user_id=current_user.id)

@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse
)
async def get_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))
):
    service = EmployeeService(db=db)

    return await service.get_employee(employee_id=employee_id, current_user=current_user)

@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse
)
async def update_employee(
    employee_id: UUID,
    request: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(UserRole.ADMIN))
):
    service = EmployeeService(db=db)

    return await service.update_employee(employee_id=employee_id, request=request)

@router.patch(
    "/{employee_id}/status",
    response_model=EmployeeResponse
)
async def update_employee_status(
    employee_id: UUID,
    request: EmployeeStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(UserRole.ADMIN))
):
    service = EmployeeService(db=db)

    return await service.update_employee_status(employee_id=employee_id, employment_status=request.employment_status)