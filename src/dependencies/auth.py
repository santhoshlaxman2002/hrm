from uuid import UUID
import jwt
from src.core.settings import get_settings
from src.db.database import get_db
from src.repository.auth import AuthRepository
from src.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()

bearer_schema = HTTPBearer(auto_error=False)

async def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_schema),
        db: AsyncSession = Depends(get_db)
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            jwt=credentials.credentials,
            key=settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("type") != "access":
            raise unauthorized

        user_id = UUID(payload["sub"])

    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise unauthorized

    repository = AuthRepository(db)
    user = await repository.get_user_by_id(user_id)

    if user is None or not user.is_active:
        raise unauthorized
    
    return user