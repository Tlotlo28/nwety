"""Nwety — FastAPI entry point."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import select

from app.config import get_settings
from app.database import Base, async_session_maker, engine
from app.models.user import User
from app.routers import chat, content, words
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
import os

settings = get_settings()


async def _seed_users() -> None:
    """Create the two fixed users on first startup."""
    async with async_session_maker() as db:
        result = await db.execute(select(User))
        if result.scalars().first() is not None:
            return  # Already seeded

        db.add_all([
            User(id=1, name=settings.user_one_name, language=settings.user_one_language),
            User(id=2, name=settings.user_two_name, language=settings.user_two_language),
        ])
        await db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Startup: optionally reset DB (one-shot for schema changes), seed users."""
    if os.getenv("RESET_DB_ON_START", "").lower() == "true":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        # Print loud so it's obvious in logs
        print("⚠ RESET_DB_ON_START=true — dropped all tables. "
              "Set this to 'false' in Render after deploy succeeds.")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_users()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
# Allow any host in development; tighten in production via RENDER_EXTERNAL_HOSTNAME
_allowed_hosts = ["*"] if settings.debug else [
     os.getenv("RENDER_EXTERNAL_HOSTNAME", "*"),
    "localhost",
    "127.0.0.1",
]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)

# CORS — permissive here because the frontend and backend are the same origin.
# Kept explicit so that if you ever split them (e.g. a separate React frontend),
# you only change this one block.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(chat.router)
app.include_router(words.router)
app.include_router(content.router)


@app.get("/api/users")
async def list_users():
    """Expose the two fixed users so the frontend knows who's who."""
    async with async_session_maker() as db:
        result = await db.execute(select(User))
        return [
            {"id": u.id, "name": u.name, "language": u.language}
            for u in result.scalars().all()
        ]


@app.get("/api/health")
def health():
    """Deep health check — confirms the translation engine is loaded."""
    from app.services import translator
    try:
        # Cheap round-trip. If this works, everything downstream works.
        sample = translator.translate("hello", "en", "pt")
        ready = bool(sample)
    except Exception as exc:  # noqa: BLE001
        return {"status": "degraded", "app": settings.app_name, "error": str(exc)}
    return {"status": "ok", "app": settings.app_name, "translator_ready": ready}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "app_name": settings.app_name})


@app.get("/chat/{user_id}", response_class=HTMLResponse)
async def chat_page(request: Request, user_id: int):
    return templates.TemplateResponse("chat.html", {"request": request, "user_id": user_id})


@app.get("/discover/{user_id}", response_class=HTMLResponse)
async def discover_page(request: Request, user_id: int):
    return templates.TemplateResponse("discover.html", {"request": request, "user_id": user_id})