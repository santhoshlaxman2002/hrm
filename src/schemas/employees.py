from uuid import UUID
from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator
)
from src.models.enums import EmploymentStatus, UserRole

class EmployeeCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

    employee_code:str = Field(min_length=2, max_length=30)
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    department_id: UUID
    manager_id: UUID | None = None

    designation: str = Field(min_length=2, max_length=100)
    joining_date: date

    role: UserRole = UserRole.EMPLOYEE

    @field_validator(
        "employee_code",
        "first_name",
        "last_name",
        "designation"
    )
    @classmethod
    def strip_values(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty")

        return value

    @field_validator("role")
    @classmethod
    def validate_employee_role(cls, value: UserRole) -> UserRole:
        if value not in (UserRole.EMPLOYEE, UserRole.MANAGER):
            raise ValueError(
                "Employee role must be EMPLOYEE or MANAGER"
            )
        return value

class EmployeeUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )
    department_id: UUID | None = None
    manager_id: UUID | None = None
    designation: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    joining_date: date | None = None
    role: UserRole | None = None

    @field_validator(
        "first_name",
        "last_name",
        "designation"
    )
    @classmethod
    def strip_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty")

        return value

    @field_validator("role")
    @classmethod
    def validate_employee_role(cls, value: UserRole | None) -> UserRole | None:
        if value is not None and value not in (UserRole.EMPLOYEE, UserRole.MANAGER):
            raise ValueError(
                "Employee role must be EMPLOYEE or MANAGER"
            )

        return value

class EmployeeStatusUpdate(BaseModel):
    employment_status: EmploymentStatus

class UserSummary(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class DepartmentSummary(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)

class EmployeeResponse(BaseModel):
    id: UUID
    user_id: UUID
    employee_code: str
    first_name: str
    last_name: str
    department_id: UUID
    manager_id: UUID | None
    designation: str
    joining_date: date
    employment_status: EmploymentStatus
    created_at: datetime
    updated_at: datetime

    user: UserSummary
    department: DepartmentSummary

    model_config = ConfigDict(from_attributes=True)

class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]
    total: int
    skip: int
    limit: int