from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from src.models.enums import LeaveRequestStatus

class LeaveTypeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    annual_allowance: Decimal = Field(
        ge=0,
        max_digits=6,
        decimal_places=2,
    )

class LeaveTypeUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    annual_allowance: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=6,
        decimal_places=2,
    )
    is_active: bool | None = None


class LeaveTypeResponse(BaseModel):
    id: UUID
    name: str
    annual_allowance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LeaveBalanceAssign(BaseModel):
    leave_type_id: UUID
    year: int = Field(ge=2000, le=2100)
    total_days: Decimal = Field(
        ge=0,
        max_digits=6,
        decimal_places=2,
    )


class LeaveBalanceResponse(BaseModel):
    id: UUID
    employee_id: UUID
    leave_type_id: UUID
    year: int
    total_days: Decimal
    used_days: Decimal
    remaining_days: Decimal

    model_config = ConfigDict(from_attributes=True)

class LeaveRequestCreate(BaseModel):
    leave_type_id: UUID
    start_date: date
    end_date: date
    reason: str = Field(min_length=5, max_length=500)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date > self.end_date:
            raise ValueError(
                "Start date cannot be after end date"
            )

        if self.start_date.year != self.end_date.year:
            raise ValueError(
                "Leave requests across multiple years are not supported"
            )

        return self

class LeaveRequestReview(BaseModel):
    comments: str | None = Field(
        default=None,
        max_length=500,
    )

class LeaveRequestResponse(BaseModel):
    id: UUID
    employee_id: UUID
    leave_type_id: UUID
    start_date: date
    end_date: date
    total_days: Decimal
    reason: str
    status: LeaveRequestStatus
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LeaveRequestListResponse(BaseModel):
    items: list[LeaveRequestResponse]
    total: int
    skip: int
    limit: int