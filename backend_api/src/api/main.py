import os
import time
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

# CORS configuration
# - Default to allowing local dev + this platform's preview host.
# - IMPORTANT: If allow_credentials=True, allow_origins cannot be ["*"] (browser will reject).
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # The preview URL host for this environment (frontend runs on :3000).
    "https://vscode-internal-10540-qa.qa01.cloud.kavia.ai:3000",
]
allow_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
allow_origins = (
    [o.strip() for o in allow_origins_env.split(",") if o.strip()]
    if allow_origins_env
    else default_origins
)

# If user explicitly configured wildcard, disable credentials to remain spec-compliant.
allow_credentials = True
if len(allow_origins) == 1 and allow_origins[0] == "*":
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Minimal request logging + timing (helps diagnose "Failed to fetch" and 5xx issues)
@app.middleware("http")
async def _log_requests(request: Request, call_next: Callable):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:  # pragma: no cover
        duration_ms = int((time.time() - start) * 1000)
        print(
            f"[error] {request.method} {request.url.path} -> 500 in {duration_ms}ms: {exc}"
        )
        # Ensure errors are returned as JSON (frontend expects JSON) and are debuggable.
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
                # Keep message high-level; avoid leaking secrets.
                "hint": "Check backend logs for details. If DB is down/misconfigured, set POSTGRES_URL/DATABASE_URL.",
            },
        )

    duration_ms = int((time.time() - start) * 1000)
    print(f"[request] {request.method} {request.url.path} -> {response.status_code} in {duration_ms}ms")
    return response


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
