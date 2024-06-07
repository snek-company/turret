import contextlib
import datetime
import json
import logging
from typing import AsyncGenerator, Any, Optional

from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Path, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, NoResultFound
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from turret.db import init_models, get_db, TurretEvent
from turret.types import Event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:
    await init_models()
    yield


api_router = APIRouter(
    prefix="/api",
    tags=["api"],
    responses={404: {"description": "Not found"}},
)


# Dependency for event retrieval
async def get_event(event_id: str, session: AsyncSession = Depends(get_db)) -> TurretEvent:
    try:
        return await session.get(TurretEvent, event_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Event not found")


# Function to extract and format event data
async def _extract_row_data(request: Request, project_id: int):
    try:
        sentry_event: Event = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    searchable_strings = " ".join(
        [
            sentry_event.get("message", ""),
            json.dumps(sentry_event.get("exception", {})),
        ]
    )

    return {
        "event_id": sentry_event["event_id"],
        "project_id": project_id,
        "timestamp": sentry_event["timestamp"],
        "searchable_strings": searchable_strings,
        "event": sentry_event,
    }


@api_router.post("/{project_id}/store/")
async def store_event(
        request: Request,
        project_id: int,
        session: AsyncSession = Depends(get_db),
):
    try:
        data = await _extract_row_data(request, project_id=project_id)
        event = TurretEvent(**data)
        session.add(event)
        await session.commit()
        return JSONResponse(
            status_code=201, content={"message": "Event created successfully", "id": event.id}
        )
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Event ID already exists")


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/{event_id}", response_class=HTMLResponse)
async def event_detail(request: Request, event: TurretEvent = Depends(get_event)):
    return templates.TemplateResponse(
        request=request, name="events/detail.html", context={"event": event}
    )


# Event list view with filtering and pagination (placeholder)
@app.get("/", response_class=HTMLResponse)
async def events_list(
        request: Request,
        project_id: Optional[int] = Query(None),
        start_time: Optional[datetime.datetime] = Query(None),
        end_time: Optional[datetime.datetime] = Query(None),
        search: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1),
        session: AsyncSession = Depends(get_db),
):
    query = session.query(TurretEvent)

    # Add filtering conditions based on query parameters

    # Add pagination logic

    events = query.all()  # Replace with paginated query

    return templates.TemplateResponse(
        request=request, name="events/list.html", context={"events": events}
    )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host='127.0.0.1', port=8001)
