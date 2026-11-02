from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.models.refresh_token import RefreshToken

class AuthRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str):
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id):
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_refresh_token(
        self, 
        user_id, 
        token_hash:str, 
        expires_at
    ):
        refresh_token = RefreshToken(
            user_id= user_id,
            token_hash= token_hash,
            expires_at= expires_at
        )
        self.db.add(refresh_token)
        await self.db.flush()

        return refresh_token

    async def get_refresh_token_for_update(
        self,
        token_hash: str
    ):
        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .with_for_update()
        )

        return result.scalar_one_or_none()

    async def revoke_refresh_token(
        self,
        refresh_token: RefreshToken,
        revoked_at
    ):
        refresh_token.revoked_at = revoked_at
        await self.db.flush()

        return refresh_token