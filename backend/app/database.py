from datetime import datetime, timezone
from datetime import datetime as dt
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings

# Configure engine based on database type
engine_kwargs = {"echo": settings.app_env == "dev"}

# SQLite specific configuration
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Type annotations for common columns
uuid_pk = Annotated[UUID, mapped_column(primary_key=True, default=uuid4)]

# Use default instead of server_default for SQLite compatibility


def utc_now() -> datetime:
    """Get current UTC time."""
    return dt.now(timezone.utc)

created_at = Annotated[
    datetime, mapped_column(DateTime(timezone=True), default=utc_now)
]
updated_at = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now),
]


class Base(DeclarativeBase):
    """Base model with common fields."""

    id: Mapped[uuid_pk]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
