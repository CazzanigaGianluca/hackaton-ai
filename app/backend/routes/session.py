"""GET /api/session/{id} — stato e risultati di una Sessione."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.backend import database

router = APIRouter()


@router.get("/api/session/{session_id}")
async def get_session(session_id: str) -> dict:
    session = await database.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    return session
