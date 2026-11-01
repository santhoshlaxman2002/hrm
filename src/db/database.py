from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from src.core.settings import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL.get_secret_value(),
    echo=True,
    pool_size=10,
    max_overflow=20
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with async_session_factory() as session:
        yield session

class Base(DeclarativeBase):
    pass