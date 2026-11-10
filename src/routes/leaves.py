from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies.auth import get_current_user
from src.dependencies.permissions import require_roles

from src.models.enums import LeaveRequestStatus, UserRole
from src.models.user import User

from src.schemas.leaves import (
    LeaveBalanceAssign,
    LeaveBalanceResponse,
    LeaveRequestCreate,
    LeaveRequestListResponse,
    LeaveRequestResponse,
    LeaveRequestReview,
    LeaveTypeCreate,
    LeaveTypeResponse,
    LeaveTypeUpdate,
)
from src.services.leaves import LeaveService


router = APIRouter()


def get_leave_service(
    db: AsyncSession = Depends(get_db),
):
    return LeaveService(db)

@router.post(
    "/leave-types",
    response_model=LeaveTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_leave_type(
    request: LeaveTypeCreate,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.create_leave_type(request)


@router.get(
    "/leave-types",
)
async def list_leave_types(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    active_only: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.list_leave_types(
        skip=skip,
        limit=limit,
        active_only=active_only,
    )

@router.get(
    "/leave-types/{leave_type_id}",
    response_model=LeaveTypeResponse,
)
async def get_leave_type(
    leave_type_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.get_leave_type(leave_type_id)

@router.patch(
    "/leave-types/{leave_type_id}",
    response_model=LeaveTypeResponse,
)
async def update_leave_type(
    leave_type_id: UUID,
    request: LeaveTypeUpdate,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.update_leave_type(
        leave_type_id,
        request,
    )

@router.put(
    "/leave-balances/{employee_id}",
    response_model=LeaveBalanceResponse,
)
async def assign_leave_balance(
    employee_id: UUID,
    request: LeaveBalanceAssign,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.assign_leave_balance(
        employee_id,
        request,
    )

@router.get(
    "/leave-balances/me",
    response_model=list[LeaveBalanceResponse],
)
async def get_my_leave_balances(
    year: int = Query(
        default_factory=lambda: date.today().year,
        ge=2000,
        le=2100,
    ),
    current_user: User = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.get_my_leave_balances(
        user_id=current_user.id,
        year=year,
    )

@router.get(
    "/leave-balances/{employee_id}",
    response_model=list[LeaveBalanceResponse],
)
async def get_employee_leave_balances(
    employee_id: UUID,
    year: int = Query(
        default_factory=lambda: date.today().year,
        ge=2000,
        le=2100,
    ),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.get_employee_leave_balances(
        employee_id=employee_id,
        year=year,
    )

@router.post(
    "/leave-requests",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply_leave(
    request: LeaveRequestCreate,
    current_user: User = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.apply_leave(
        user_id=current_user.id,
        request=request,
    )

@router.get(
    "/leave-requests/me",
    response_model=LeaveRequestListResponse,
)
async def get_my_leave_requests(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    request_status: LeaveRequestStatus | None = Query(
        default=None,
        alias="status",
    ),
    current_user: User = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.get_my_requests(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        request_status=request_status,
    )

@router.get(
    "/leave-requests/team",
    response_model=LeaveRequestListResponse,
)
async def get_team_leave_requests(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    request_status: LeaveRequestStatus | None = Query(
        default=None,
        alias="status",
    ),
    current_user: User = Depends(
        require_roles(UserRole.MANAGER)
    ),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.get_team_requests(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        request_status=request_status,
    )

@router.get(
    "/leave-requests",
    response_model=LeaveRequestListResponse,
)
async def get_all_leave_requests(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    request_status: LeaveRequestStatus | None = Query(
        default=None,
        alias="status",
    ),
    employee_id: UUID | None = Query(default=None),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.get_all_requests(
        skip=skip,
        limit=limit,
        request_status=request_status,
        employee_id=employee_id,
    )

@router.get(
    "/leave-requests/{request_id}",
    response_model=LeaveRequestResponse,
)
async def get_leave_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.get_leave_request(
        request_id=request_id,
        current_user=current_user,
    )

@router.patch(
    "/leave-requests/{request_id}/approve",
    response_model=LeaveRequestResponse,
)
async def approve_leave(
    request_id: UUID,
    request: LeaveRequestReview,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.approve_leave(
        request_id=request_id,
        reviewer=current_user,
        review=request,
    )


@router.patch(
    "/leave-requests/{request_id}/reject",
    response_model=LeaveRequestResponse,
)
async def reject_leave(
    request_id: UUID,
    request: LeaveRequestReview,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.reject_leave(
        request_id=request_id,
        reviewer=current_user,
        review=request,
    )

@router.patch(
    "/leave-requests/{request_id}/cancel",
    response_model=LeaveRequestResponse,
)
async def cancel_leave(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    return await service.cancel_leave(
        request_id=request_id,
        user_id=current_user.id,
    )