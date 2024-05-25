import contextlib
import json
from typing import AsyncGenerator, Any

from fastapi import FastAPI, APIRouter, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.templating import Jinja2Templates

from turret.db import init_models, get_db, TurretEvent
from turret._types import Event


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


async def _extract_row_data(request: Request, project_id: int):
    sentry_event: Event = await request.json()
    searchable_strings = ' '.join([
        sentry_event['message'],
        json.dumps(sentry_event['exception'])
    ])

    return {
        'event_id': sentry_event['event_id'],
        'project_id': project_id,
        'timestamp': sentry_event['timestamp'],
        'searchable_strings': searchable_strings,
        'raw': sentry_event
    }


@api_router.post("{project_id}/store/")
async def store_event(request: Request, session: AsyncSession = Depends(get_db)):
    project_id = request.path_params['project_id']
    data = await _extract_row_data(request, project_id=project_id)
    event = TurretEvent(**data)
    session.add(event)
    return Response(status_code=204)


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/{event_id}", response_class=HTMLResponse)
async def event_detail(request: Request, event_id: str):
    print("foo")
    return templates.TemplateResponse(
        request=request, name="events/detail.html", context={"event_id": event_id}
    )


@app.get("/", response_class=HTMLResponse)
async def events_list(request: Request):
    print("bar")
    return templates.TemplateResponse(
        request=request, name="events/list.html"
    )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host='127.0.0.1', port=8001)
