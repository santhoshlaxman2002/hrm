from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.auth import TokenResponse, LoginRequest, UserResponse, RefreshTokenResponse
from src.db.database import get_db
from src.services.auth import AuthService
from src.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    return await service.login(
        email=request.email,
        password=request.password
    )

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user = Depends(get_current_user)
):
    return current_user

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenResponse,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)

    return await service.refresh(refresh_token=request.refresh_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: RefreshTokenResponse,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)

    await service.logout(refresh_token=request.refresh_token)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )