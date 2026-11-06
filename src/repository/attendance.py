from datetime import date
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.models.attendance import Attendance
from src.models.employee import Employee
from src.models.enums import EmploymentStatus

class AttendanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    