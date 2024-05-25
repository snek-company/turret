import datetime
from typing import Optional, List, AsyncGenerator, Any

# import databases
import sqlalchemy
from sqlalchemy import String, MetaData, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, AsyncSession, async_scoped_session, \
    async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


DATABASE_URL = "sqlite+aiosqlite://"


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
    event_id: Mapped[str] = mapped_column(unique=True)  # for detail
    project_id: Mapped[int] = mapped_column(index=True)  # for list toggle
    timestamp: Mapped[datetime.datetime] = mapped_column(index=True)  # for list order

    # see _extract_row_data
    searchable_strings: Mapped[str] = mapped_column(index=True)  # for list filter

    event: Mapped[dict[str, Any]] = mapped_column()  # for detail, this dict is Event from types

    def __repr__(self) -> str:
        return f"Event(id={self.id!r}, sentry_event_id={self.event_id!r})"


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    async with async_session() as session, session.begin():
        yield session


async def init_models() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
