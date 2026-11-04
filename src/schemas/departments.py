from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from uuid import UUID

class DepartmentCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Department name cannot be empty")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        if value is not None:
            value = value.strip()
            return value or None

        return value

class DepartmentUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Department name cannot be empty")

        return value

    @field_validator("description")
    @classmethod
    def validate_descriptiom(cls, value: str) -> str:
        if value is not None:
            value = value.strip()
            return value or None

        return value

class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DepartmentListResponse(BaseModel):
    items: list[DepartmentResponse]
    total: int
    skip: int
    limit: int