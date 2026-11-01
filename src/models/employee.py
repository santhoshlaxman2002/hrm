import uuid
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Date,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    String,
    CheckConstraint,
    Index
)
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import BaseModel
from src.models.enums import EmploymentStatus

class Employee(BaseModel):
    __tablename__ = "employees"

    __table_args__ = (
        CheckConstraint(
            "manager_id IS NULL OR manager_id != id",
            name = "ck_employee_not_own_manager"
        ),
        Index(
            "idx_employees_department",
            "department_id"
        ),
        Index(
            "idx_employees_manager",
            "manager_id"
        )
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False
    )

    employee_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )

    first_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    last_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False
    )

    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=True
    )

    designation: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    joining_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    employment_status: Mapped[EmploymentStatus] = mapped_column(
        SQLAlchemyEnum(
            EmploymentStatus,
            name="employment_status",
            values_callable=lambda enum:[
                item.value for item in enum
            ]
        ),
        default=EmploymentStatus.ACTIVE,
        nullable=False
    )

    # User Relationship
    user: Mapped["User"] = relationship(
        "User",
        back_populates="employee"
    )

    #Department Relationship
    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="employees"
    )

    # Self-referencing manager relationship
    manager: Mapped["Employee | None"] = relationship(
        "Employee",
        remote_side="Employee.id",
        back_populates="direct_reports",
        foreign_keys=[manager_id]
    )

    direct_reports: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="manager",
        foreign_keys=[manager_id]
    )

    # Attendance Relationship
    attendance_records: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="employee"
    )

    # Leave request Relationship
    leave_requests: Mapped[list["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="employee",
        foreign_keys="LeaveRequest.employee_id"
    )

    # Leave Balances Relationship
    leave_balances: Mapped[list["LeaveBalance"]] = relationship(
        "LeaveBalance",
        back_populates="employee"
    )

    # Leave requests reviewed by this employee
    reviewed_leave_requests: Mapped[list["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="reviewer",
        foreign_keys="LeaveRequest.reviewed_by"
    )