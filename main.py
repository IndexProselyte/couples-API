from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from admin.router import router as admin_router
from auth.router import router as auth_router
from config import get_settings
from couple.router import router as couple_router
from database import Base, engine, seed_db
from integrations.router import router as integrations_router
from messages.router import router as messages_router
from mood.router import router as mood_router
from timeline.router import router as timeline_router
from upload.router import router as upload_router
from ws.router import router as ws_router

settings = get_settings()

# Ensure the uploads directory exists before FastAPI tries to mount it.
_upload_path = Path(settings.upload_dir)
_upload_path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_db()
    yield


app = FastAPI(
    title="Couples API",
    lifespan=lifespan,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files as static assets at /uploads/<filename>.
app.mount("/uploads", StaticFiles(directory=str(_upload_path)), name="uploads")

app.include_router(auth_router,         prefix="/auth",   tags=["auth"])
app.include_router(admin_router,        prefix="/admin",  tags=["admin"])
app.include_router(couple_router,                         tags=["couple"])
app.include_router(mood_router,                           tags=["mood"])
app.include_router(messages_router,                       tags=["messages"])
app.include_router(timeline_router,                       tags=["timeline"])
app.include_router(upload_router,                         tags=["upload"])
app.include_router(ws_router,                             tags=["websocket"])
app.include_router(integrations_router,                   tags=["integrations"])


@app.get("/health", tags=["health"])
def health():
    return {"ok": True}
