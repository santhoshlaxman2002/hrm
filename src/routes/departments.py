from uuid import UUID
from fastapi import APIRouter, Depends, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.dependencies.permissions import require_roles
from src.dependencies.auth import get_current_user
from src.db.database import get_db
from src.models.enums import UserRole
from src.services.departments import DepartmentService
from src.schemas.departments import DepartmentCreate, DepartmentUpdate, DepartmentListResponse, DepartmentResponse

router = APIRouter()

@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    request: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(UserRole.ADMIN))
):
    service = DepartmentService(db=db)
    return await service.create_department(request=request)

@router.get("", response_model=DepartmentListResponse)
async def list_departments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=0, le=100),
    search: str | None = Query(default=None, max_length=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = DepartmentService(db)

    return await service.list_departments(skip=skip, limit=limit, search=search)

@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = DepartmentService(db)

    return await service.get_department(department_id=department_id)

@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    request: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(UserRole.ADMIN))
):
    service = DepartmentService(db=db)

    return await service.update_department(department_id=department_id, request=request)

@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(UserRole.ADMIN))
):
    service = DepartmentService(db=db)

    return await service.deactivate_department(department_id=department_id)