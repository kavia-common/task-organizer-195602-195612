import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.db import get_engine
from src.api.models import Base
from src.api.routes.tasks import router as tasks_router

openapi_tags = [
    {
        "name": "System",
        "description": "Health checks and system-level endpoints.",
    },
    {
        "name": "Tasks",
        "description": "CRUD operations for tasks.",
    },
]

app = FastAPI(
    title="Task Organizer API",
    description="Backend API for a simple to-do list application (CRUD tasks).",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

allow_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
allow_origins = (
    [o.strip() for o in allow_origins_env.split(",") if o.strip()]
    if allow_origins_env
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    """Initialize DB schema on startup (best-effort).

    For this simple demo app we attempt to create tables automatically.
    In production, use migrations (Alembic).

    Important: the application should still start even if the database is unavailable
    (e.g., missing env vars, DB container not ready). DB-backed endpoints will fail when used,
    but the process stays up (health checks, docs, etc).
    """
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # pragma: no cover
        # Best-effort startup: log and continue so the server can run.
        # Uvicorn/Starlette will capture stdout/stderr.
        print(f"[startup] Database initialization skipped: {exc}")


@app.get(
    "/",
    tags=["System"],
    summary="Health check",
    description="Simple health check endpoint to verify the service is running.",
    operation_id="health_check",
)
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}


app.include_router(tasks_router)
