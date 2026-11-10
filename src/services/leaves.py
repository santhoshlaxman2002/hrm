from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.employee import Employee
from src.models.enums import LeaveRequestStatus, UserRole
from src.models.leave_balance import LeaveBalance
from src.models.leave_request import LeaveRequest
from src.models.leave_type import LeaveType
from src.models.user import User

from src.repository.leaves import LeaveRepository
from src.schemas.leaves import (
    LeaveBalanceAssign,
    LeaveRequestCreate,
    LeaveRequestReview,
    LeaveTypeCreate,
    LeaveTypeUpdate,
)


class LeaveService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = LeaveRepository(db)

    @staticmethod
    def _error(code: int, message: str):
        return HTTPException(
            status_code=code,
            detail=message,
        )

    @staticmethod
    def _build_balance_response(balance: LeaveBalance):
        return {
            "id": balance.id,
            "employee_id": balance.employee_id,
            "leave_type_id": balance.leave_type_id,
            "year": balance.year,
            "total_days": balance.total_days,
            "used_days": balance.used_days,
            "remaining_days": (
                Decimal(balance.total_days)
                - Decimal(balance.used_days)
            ),
        }

    async def _get_active_employee(self, user_id: UUID):
        employee = await self.repository.get_employee_by_user_id(
            user_id
        )

        if not employee:
            raise self._error(
                status.HTTP_404_NOT_FOUND,
                "Active employee profile not found",
            )

        return employee

    async def _get_reviewer_employee(self, reviewer: User):
        employee = await self.repository.get_employee_by_user_id(
            reviewer.id
        )

        if not employee:
            raise self._error(
                status.HTTP_404_NOT_FOUND,
                "Reviewer employee profile not found",
            )

        return employee

    async def _validate_reviewer(
        self,
        leave_request: LeaveRequest,
        reviewer: User,
    ):
        if reviewer.role == UserRole.ADMIN:
            return

        if reviewer.role != UserRole.MANAGER:
            raise self._error(
                status.HTTP_403_FORBIDDEN,
                "You are not allowed to review leave requests",
            )

        manager = await self._get_reviewer_employee(reviewer)

        employee = await self.repository.get_employee_by_id(
            leave_request.employee_id,
            active_only=False,
        )

        if not employee or employee.manager_id != manager.id:
            raise self._error(
                status.HTTP_403_FORBIDDEN,
                "You can review leave requests from your direct reports only",
            )

        if employee.id == manager.id:
            raise self._error(
                status.HTTP_403_FORBIDDEN,
                "You cannot approve your own leave request",
            )

    async def _get_pending_request_for_review(
        self,
        request_id: UUID,
        reviewer: User,
    ):
        leave_request = await self.repository.get_leave_request_by_id(
            request_id,
            for_update=True,
        )

        if not leave_request:
            raise self._error(
                status.HTTP_404_NOT_FOUND,
                "Leave request not found",
            )

        if leave_request.status != LeaveRequestStatus.PENDING:
            raise self._error(
                status.HTTP_409_CONFLICT,
                "Only pending leave requests can be reviewed",
            )

        await self._validate_reviewer(leave_request, reviewer)

        return leave_request

    async def create_leave_type(
        self,
        request: LeaveTypeCreate,
    ):
        try:
            existing = await self.repository.get_leave_type_by_name(
                request.name
            )

            if existing:
                raise self._error(
                    status.HTTP_409_CONFLICT,
                    "Leave type already exists",
                )

            leave_type = LeaveType(
                name=request.name.strip(),
                annual_allowance=request.annual_allowance,
                is_active=True,
            )

            await self.repository.create_leave_type(leave_type)

            await self.db.commit()
            await self.db.refresh(leave_type)

            return leave_type

        except IntegrityError:
            await self.db.rollback()
            raise self._error(
                status.HTTP_409_CONFLICT,
                "Leave type already exists",
            )

        except Exception:
            await self.db.rollback()
            raise

    async def get_leave_type(self, leave_type_id: UUID):
        leave_type = await self.repository.get_leave_type_by_id(
            leave_type_id
        )

        if not leave_type:
            raise self._error(
                status.HTTP_404_NOT_FOUND,
                "Leave type not found",
            )

        return leave_type

    async def list_leave_types(
        self,
        skip: int,
        limit: int,
        active_only: bool = True,
    ):
        items, total = await self.repository.list_leave_types(
            skip=skip,
            limit=limit,
            active_only=active_only,
        )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def update_leave_type(
        self,
        leave_type_id: UUID,
        request: LeaveTypeUpdate,
    ):
        try:
            leave_type = await self.repository.get_leave_type_by_id(
                leave_type_id
            )

            if not leave_type:
                raise self._error(
                    status.HTTP_404_NOT_FOUND,
                    "Leave type not found",
                )

            update_data = request.model_dump(exclude_unset=True)

            if not update_data:
                raise self._error(
                    status.HTTP_400_BAD_REQUEST,
                    "Provide at least one field to update",
                )

            if "name" in update_data:
                name = update_data["name"]

                if name is None:
                    raise self._error(
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                        "Leave type name cannot be null",
                    )

                existing = await self.repository.get_leave_type_by_name(
                    name
                )

                if existing and existing.id != leave_type.id:
                    raise self._error(
                        status.HTTP_409_CONFLICT,
                        "Leave type name already exists",
                    )

                update_data["name"] = name.strip()

            if (
                "annual_allowance" in update_data
                and update_data["annual_allowance"] is None
            ):
                raise self._error(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "Annual allowance cannot be null",
                )

            for field, value in update_data.items():
                setattr(leave_type, field, value)

            await self.repository.update_leave_type(leave_type)

            await self.db.commit()
            await self.db.refresh(leave_type)

            return leave_type

        except IntegrityError:
            await self.db.rollback()
            raise self._error(
                status.HTTP_409_CONFLICT,
                "Leave type name already exists",
            )

        except Exception:
            await self.db.rollback()
            raise

    async def assign_leave_balance(
        self,
        employee_id: UUID,
        request: LeaveBalanceAssign,
    ):
        try:
            employee = await self.repository.get_employee_by_id(
                employee_id
            )

            if not employee:
                raise self._error(
                    status.HTTP_404_NOT_FOUND,
                    "Active employee not found",
                )

            leave_type = await self.repository.get_leave_type_by_id(
                request.leave_type_id,
                active_only=True,
            )

            if not leave_type:
                raise self._error(
                    status.HTTP_404_NOT_FOUND,
                    "Active leave type not found",
                )

            balance = await self.repository.get_leave_balance_for_update(
                employee_id=employee_id,
                leave_type_id=request.leave_type_id,
                year=request.year,
            )

            if balance:
                if request.total_days < balance.used_days:
                    raise self._error(
                        status.HTTP_409_CONFLICT,
                        "Total leave days cannot be less than already used days",
                    )

                balance.total_days = request.total_days

                await self.repository.update_leave_balance(balance)

            else:
                balance = LeaveBalance(
                    employee_id=employee_id,
                    leave_type_id=request.leave_type_id,
                    year=request.year,
                    total_days=request.total_days,
                    used_days=Decimal("0"),
                )

                await self.repository.create_leave_balance(balance)

            await self.db.commit()
            await self.db.refresh(balance)

            return self._build_balance_response(balance)

        except IntegrityError:
            await self.db.rollback()
            raise self._error(
                status.HTTP_409_CONFLICT,
                "Leave balance already exists or conflicts with existing data",
            )

        except Exception:
            await self.db.rollback()
            raise

    async def get_my_leave_balances(
        self,
        user_id: UUID,
        year: int,
    ):
        employee = await self._get_active_employee(user_id)

        balances = await self.repository.list_employee_balances(
            employee_id=employee.id,
            year=year,
        )

        return [
            self._build_balance_response(balance)
            for balance in balances
        ]

    async def get_employee_leave_balances(
        self,
        employee_id: UUID,
        year: int,
    ):
        employee = await self.repository.get_employee_by_id(
            employee_id,
            active_only=False,
        )

        if not employee:
            raise self._error(
                status.HTTP_404_NOT_FOUND,
                "Employee not found",
            )

        balances = await self.repository.list_employee_balances(
            employee_id=employee_id,
            year=year,
        )

        return [
            self._build_balance_response(balance)
            for balance in balances
        ]

    async def apply_leave(
        self,
        user_id: UUID,
        request: LeaveRequestCreate,
    ):
        try:
            employee = await self._get_active_employee(user_id)

            leave_type = await self.repository.get_leave_type_by_id(
                request.leave_type_id,
                active_only=True,
            )

            if not leave_type:
                raise self._error(
                    status.HTTP_404_NOT_FOUND,
                    "Active leave type not found",
                )

            today = date.today()

            if request.start_date < today:
                raise self._error(
                    status.HTTP_400_BAD_REQUEST,
                    "Leave cannot be applied for past dates",
                )

            total_days = Decimal(
                (request.end_date - request.start_date).days + 1
            )

            # Check whether the employee has a balance for this year.
            balance = await self.repository.get_leave_balance(
                employee_id=employee.id,
                leave_type_id=request.leave_type_id,
                year=request.start_date.year,
            )

            if not balance:
                raise self._error(
                    status.HTTP_409_CONFLICT,
                    "Leave balance has not been assigned for this year",
                )

            remaining_days = (
                Decimal(balance.total_days)
                - Decimal(balance.used_days)
            )

            if total_days > remaining_days:
                raise self._error(
                    status.HTTP_409_CONFLICT,
                    "Insufficient leave balance",
                )

            # Check overlapping pending or approved requests.
            overlapping = await self.repository.get_overlapping_requests(
                employee_id=employee.id,
                start_date=request.start_date,
                end_date=request.end_date,
            )

            if overlapping:
                raise self._error(
                    status.HTTP_409_CONFLICT,
                    "You already have a pending or approved leave request for these dates",
                )

            leave_request = LeaveRequest(
                employee_id=employee.id,
                leave_type_id=request.leave_type_id,
                start_date=request.start_date,
                end_date=request.end_date,
                total_days=total_days,
                reason=request.reason.strip(),
                status=LeaveRequestStatus.PENDING,
            )

            await self.repository.create_leave_request(leave_request)

            await self.db.commit()
            await self.db.refresh(leave_request)

            return leave_request

        except IntegrityError:
            await self.db.rollback()
            raise self._error(
                status.HTTP_409_CONFLICT,
                "Leave request conflicts with existing data",
            )

        except Exception:
            await self.db.rollback()
            raise

    async def get_my_requests(
        self,
        user_id: UUID,
        skip: int,
        limit: int,
        request_status: LeaveRequestStatus | None = None,
    ):
        employee = await self._get_active_employee(user_id)

        items, total = await self.repository.list_employee_requests(
            employee_id=employee.id,
            skip=skip,
            limit=limit,
            request_status=request_status,
        )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_team_requests(
        self,
        user_id: UUID,
        skip: int,
        limit: int,
        request_status: LeaveRequestStatus | None = None,
    ):
        manager = await self._get_active_employee(user_id)

        items, total = await self.repository.list_team_requests(
            manager_id=manager.id,
            skip=skip,
            limit=limit,
            request_status=request_status,
        )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_all_requests(
        self,
        skip: int,
        limit: int,
        request_status: LeaveRequestStatus | None = None,
        employee_id: UUID | None = None,
    ):
        items, total = await self.repository.list_all_requests(
            skip=skip,
            limit=limit,
            request_status=request_status,
            employee_id=employee_id,
        )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_leave_request(
        self,
        request_id: UUID,
        current_user: User,
    ):
        leave_request = await self.repository.get_leave_request_by_id(
            request_id
        )

        if not leave_request:
            raise self._error(
                status.HTTP_404_NOT_FOUND,
                "Leave request not found",
            )

        if current_user.role == UserRole.ADMIN:
            return leave_request

        employee = await self.repository.get_employee_by_user_id(
            current_user.id,
            active_only=False,
        )

        if not employee:
            raise self._error(
                status.HTTP_404_NOT_FOUND,
                "Employee profile not found",
            )

        if leave_request.employee_id == employee.id:
            return leave_request

        if (
            current_user.role == UserRole.MANAGER
            and await self.repository.get_employee_by_id(
                leave_request.employee_id,
                active_only=False,
            )
        ):
            requested_employee = await self.repository.get_employee_by_id(
                leave_request.employee_id,
                active_only=False,
            )

            if requested_employee.manager_id == employee.id:
                return leave_request

        raise self._error(
            status.HTTP_403_FORBIDDEN,
            "You cannot access this leave request",
        )

    async def approve_leave(
        self,
        request_id: UUID,
        reviewer: User,
        review: LeaveRequestReview,
    ):
        try:
            leave_request = await self._get_pending_request_for_review(
                request_id,
                reviewer,
            )

            balance = await self.repository.get_leave_balance_for_update(
                employee_id=leave_request.employee_id,
                leave_type_id=leave_request.leave_type_id,
                year=leave_request.start_date.year,
            )

            if not balance:
                raise self._error(
                    status.HTTP_409_CONFLICT,
                    "Leave balance not found",
                )

            remaining_days = (
                Decimal(balance.total_days)
                - Decimal(balance.used_days)
            )

            if leave_request.total_days > remaining_days:
                raise self._error(
                    status.HTTP_409_CONFLICT,
                    "Insufficient leave balance to approve this request",
                )

            balance.used_days = (
                Decimal(balance.used_days)
                + Decimal(leave_request.total_days)
            )

            leave_request.status = LeaveRequestStatus.APPROVED
            leave_request.reviewed_by = reviewer.id
            leave_request.reviewed_at = datetime.now(timezone.utc)

            await self.repository.update_leave_balance(balance)
            await self.repository.update_leave_request(leave_request)

            await self.db.commit()
            await self.db.refresh(leave_request)

            return leave_request

        except IntegrityError:
            await self.db.rollback()
            raise self._error(
                status.HTTP_409_CONFLICT,
                "Unable to approve leave request due to a data conflict",
            )

        except Exception:
            await self.db.rollback()
            raise

    async def reject_leave(
        self,
        request_id: UUID,
        reviewer: User,
        review: LeaveRequestReview,
    ):
        try:
            leave_request = await self._get_pending_request_for_review(
                request_id,
                reviewer,
            )

            leave_request.status = LeaveRequestStatus.REJECTED
            leave_request.reviewed_by = reviewer.id
            leave_request.reviewed_at = datetime.now(timezone.utc)

            await self.repository.update_leave_request(leave_request)

            await self.db.commit()
            await self.db.refresh(leave_request)

            return leave_request

        except Exception:
            await self.db.rollback()
            raise

    async def cancel_leave(
        self,
        request_id: UUID,
        user_id: UUID,
    ):
        try:
            employee = await self._get_active_employee(user_id)

            leave_request = await self.repository.get_leave_request_by_id(
                request_id,
                for_update=True,
            )

            if not leave_request:
                raise self._error(
                    status.HTTP_404_NOT_FOUND,
                    "Leave request not found",
                )

            if leave_request.employee_id != employee.id:
                raise self._error(
                    status.HTTP_403_FORBIDDEN,
                    "You can cancel only your own leave requests",
                )

            if leave_request.status == LeaveRequestStatus.CANCELLED:
                raise self._error(
                    status.HTTP_409_CONFLICT,
                    "Leave request is already cancelled",
                )

            if leave_request.status == LeaveRequestStatus.REJECTED:
                raise self._error(
                    status.HTTP_409_CONFLICT,
                    "Rejected leave requests cannot be cancelled",
                )

            if leave_request.status == LeaveRequestStatus.APPROVED:
                if leave_request.start_date <= date.today():
                    raise self._error(
                        status.HTTP_409_CONFLICT,
                        "Approved leave can only be cancelled before its start date",
                    )

                balance = await self.repository.get_leave_balance_for_update(
                    employee_id=leave_request.employee_id,
                    leave_type_id=leave_request.leave_type_id,
                    year=leave_request.start_date.year,
                )

                if not balance:
                    raise self._error(
                        status.HTTP_409_CONFLICT,
                        "Leave balance not found",
                    )

                new_used_days = (
                    Decimal(balance.used_days)
                    - Decimal(leave_request.total_days)
                )

                if new_used_days < 0:
                    raise self._error(
                        status.HTTP_409_CONFLICT,
                        "Invalid leave balance state",
                    )

                balance.used_days = new_used_days

                await self.repository.update_leave_balance(balance)

            # Pending requests do not affect balance.
            leave_request.status = LeaveRequestStatus.CANCELLED

            await self.repository.update_leave_request(leave_request)

            await self.db.commit()
            await self.db.refresh(leave_request)

            return leave_request

        except Exception:
            await self.db.rollback()
            raise