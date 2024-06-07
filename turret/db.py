import os
import datetime
import logging
from typing import Optional, List, AsyncGenerator, Any

import aiosqlite
import sqlalchemy
from sqlalchemy import String, MetaData, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///turret.db")

# Configure database engine with connection pooling
async_engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


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
    # Create the database file if it doesn't exist
    async with aiosqlite.connect(DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")) as conn:
        pass

    # Then create the tables within the newly created database
    async with async_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)