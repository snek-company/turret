import os
import datetime
import logging
from typing import Optional, List, AsyncGenerator, Any

import sqlalchemy
from sqlalchemy import String, MetaData, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from pydantic import BaseModel, Field, validator, field_validator  # Import Pydantic for data validation

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite://")  # Default to SQLite if not set

# Configure database engine with connection pooling
async_engine = create_async_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=10)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


class BasePydanticModel(BaseModel):
    class Config:
        orm_mode = True


class TurretEventPydantic(BasePydanticModel):
    event_id: str = Field(..., min_length=1, max_length=255)
    project_id: int
    timestamp: datetime.datetime
    searchable_strings: str
    event: dict


class BaseModel(AsyncAttrs, DeclarativeBase):
    type_annotation_map = {
        dict[str, Any]: JSON
    }
    metadata = MetaData()


class TurretEvent(BaseModel):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(unique=True)
    project_id: Mapped[int] = mapped_column(index=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(index=True)
    searchable_strings: Mapped[str] = mapped_column(index=True)
    event: Mapped[dict[str, Any]] = mapped_column()

    def __repr__(self) -> str:
        return f"Event(id={self.id!r}, sentry_event_id={self.event_id!r})"


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    async with async_session() as session, session.begin():
        yield session


async def init_models() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
