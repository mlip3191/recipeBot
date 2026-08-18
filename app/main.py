from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.db import create_db_and_tables, engine
from app.routers.api import router as api_router
from app.seed import seed

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Recipe Vault")

app.include_router(api_router)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()
    with Session(engine) as session:
        seed(session)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")
