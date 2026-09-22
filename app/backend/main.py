"""FastAPI app: CORS, inizializzazione DB, mount delle route."""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Garantisce che il package top-level `agents/` sia importabile sia quando
# l'app viene lanciata da app/backend (`uvicorn main:app`) sia dalla root
# del repo (`uvicorn app.backend.main:app`).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend import database
from app.backend.routes import coach, session, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    yield


app = FastAPI(title="Inclusione Finanziaria API", lifespan=lifespan)

frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(session.router)
app.include_router(coach.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
