from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.core.settings import get_settings

settings = get_settings()

organization_timezone = ZoneInfo(
    settings.ORGANIZATION_TIMEZONE
)


def get_attendance_time():
    now_utc = datetime.now(timezone.utc)

    local_now = now_utc.astimezone(
        organization_timezone
    )

    return now_utc, local_now.date()