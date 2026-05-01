"""FastAPI entry point.

Run with:
    uvicorn api.main:app --reload --port 8000

The API thinly wraps the CLI modules in `cli/`. It opens a per-request
SQLite connection to `prospects.db` (same file the CLI writes to).
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import _bootstrap  # noqa: F401
from .routes import prospects, searches

app = FastAPI(
    title="ProspectMap API",
    description="Local lead-generation backend — wraps the CLI modules.",
    version="0.1.0",
)

_cors_origins = ["http://localhost:3000"]
if _extra := os.getenv("CORS_ORIGINS"):
    _cors_origins += [o.strip() for o in _extra.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prospects.router)
app.include_router(searches.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
