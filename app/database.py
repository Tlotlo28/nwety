"""Async SQLAlchemy database setup."""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class all database models inherit from."""
    pass


async def get_session() -> AsyncSession:
    """FastAPI dependency that yields a database session per request."""
    async with async_session_maker() as session:
        yield session