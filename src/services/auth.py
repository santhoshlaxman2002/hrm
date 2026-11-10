from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.auth import AuthRepository
from src.core.security import (
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token
)
from src.core.settings import get_settings
from fastapi import HTTPException, status

settings = get_settings()

class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = AuthRepository(db)

    async def login(self, email: str, password: str):
        user = await self.repository.get_user_by_email(email)
        print("user", verify_password(password, user.password_hash))
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )

        access_token = create_access_token(
            user_id=str(user.id),
            role=user.role.value
        )

        refresh_token = generate_refresh_token()

        expires_at = datetime.now(tz=timezone.utc) + timedelta(
            days=settings.REFRESJ_TOKEN_EXPIRE_DAYS
        )

        await self.repository.create_refresh_token(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at
        )

        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    async def refresh(self, refresh_token: str):
        try:
            now = datetime.now(tz=timezone.utc)
            token_hash = hash_refresh_token(refresh_token)

            stored_token = await self.repository.get_refresh_token_for_update(token_hash=token_hash)

            if stored_token is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Refresh Token"
                )

            if stored_token.revoked_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh Token has already been used or revoked"
                )

            if stored_token.expires_at <= now:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh Token has expired"
                )

            user = await self.repository.get_user_by_id(stored_token.user_id)

            if user is None or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Refresh Token",
                )

            await self.repository.revoke_refresh_token(refresh_token=stored_token, revoked_at=now)

            new_refresh_token = generate_refresh_token()

            new_expires_at = now + timedelta(
                days=settings.REFRESJ_TOKEN_EXPIRE_DAYS
            )

            await self.repository.create_refresh_token(
                user_id=user.id,
                expires_at=new_expires_at,
                token_hash=hash_refresh_token(new_refresh_token)
            )

            new_access_token = create_access_token(
                user_id=user.id,
                role=user.role.value
            )

            await self.db.commit()

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        except Exception:
            await self.db.rollback()
            raise

    async def logout(self, refresh_token: str):
        try:
            token_hash = hash_refresh_token(refresh_token)
            now = datetime.now(tz=timezone.utc)

            stored_token = await self.repository.get_refresh_token_for_update(token_hash=token_hash)


            if stored_token is not None and stored_token.revoked_at is None:
                await self.repository.revoke_refresh_token(
                    stored_token,
                    now
                )

            if stored_token.revoked_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Refresh Token"
                )


            await self.db.commit()

        except Exception:
            await self.db.rollback()
            raise