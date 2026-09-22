"""Schema SQLite e helper aiosqlite per la persistenza delle Sessioni.

Una Sessione raggruppa Transazioni, Pattern di Spesa, Insight e la storia
della conversazione con l'Assistente Educativo (vedi CONTEXT.md).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import aiosqlite

DATABASE_PATH = os.environ.get("DATABASE_PATH", "sessions.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    transactions_json TEXT NOT NULL DEFAULT '[]',
    analysis_json TEXT,
    insights_json TEXT NOT NULL DEFAULT '[]',
    coach_intro TEXT,
    conversation_json TEXT NOT NULL DEFAULT '[]'
);
"""


async def init_db(db_path: str | None = None) -> None:
    async with aiosqlite.connect(db_path or DATABASE_PATH) as db:
        await db.execute(_SCHEMA)
        await db.commit()


async def create_session(session_id: str, db_path: str | None = None) -> None:
    async with aiosqlite.connect(db_path or DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO sessions (session_id, status, created_at) VALUES (?, ?, ?)",
            (session_id, "pending", datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def update_session_status(
    session_id: str, status: str, db_path: str | None = None
) -> None:
    async with aiosqlite.connect(db_path or DATABASE_PATH) as db:
        await db.execute(
            "UPDATE sessions SET status = ? WHERE session_id = ?", (status, session_id)
        )
        await db.commit()


async def save_pipeline_result(
    session_id: str,
    transactions: list[dict],
    analysis: dict,
    insights: list[dict],
    coach_intro: str,
    db_path: str | None = None,
) -> None:
    async with aiosqlite.connect(db_path or DATABASE_PATH) as db:
        await db.execute(
            """UPDATE sessions
               SET status = 'coaching_ready',
                   transactions_json = ?,
                   analysis_json = ?,
                   insights_json = ?,
                   coach_intro = ?,
                   conversation_json = ?
               WHERE session_id = ?""",
            (
                json.dumps(transactions),
                json.dumps(analysis),
                json.dumps(insights),
                coach_intro,
                json.dumps([{"role": "assistant", "content": coach_intro}]),
                session_id,
            ),
        )
        await db.commit()


async def mark_session_failed(session_id: str, db_path: str | None = None) -> None:
    await update_session_status(session_id, "failed", db_path=db_path)


async def get_session(session_id: str, db_path: str | None = None) -> dict | None:
    async with aiosqlite.connect(db_path or DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "session_id": row["session_id"],
            "status": row["status"],
            "created_at": row["created_at"],
            "transactions": json.loads(row["transactions_json"]),
            "analysis": json.loads(row["analysis_json"])
            if row["analysis_json"]
            else None,
            "insights": json.loads(row["insights_json"]),
            "coach_intro": row["coach_intro"],
            "conversation": json.loads(row["conversation_json"]),
        }


async def append_conversation_message(
    session_id: str, role: str, content: str, db_path: str | None = None
) -> None:
    """Aggiunge un messaggio alla conversazione della Sessione.

    Il read-modify-write (leggi conversation_json, appendi, riscrivi) avviene dentro
    un'unica transazione SQLite con `BEGIN IMMEDIATE`, che acquisisce subito il lock di
    scrittura: senza questo, due richieste quasi simultanee (es. doppio invio dalla chat)
    potrebbero leggere lo stesso stato di partenza e la seconda `UPDATE` sovrascriverebbe
    silenziosamente il messaggio della prima (lost update).
    """
    async with aiosqlite.connect(db_path or DATABASE_PATH, isolation_level=None) as db:
        await db.execute("BEGIN IMMEDIATE")
        try:
            cursor = await db.execute(
                "SELECT conversation_json FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                raise ValueError(f"Sessione non trovata: {session_id}")

            conversation = json.loads(row[0])
            conversation.append({"role": role, "content": content})
            await db.execute(
                "UPDATE sessions SET conversation_json = ? WHERE session_id = ?",
                (json.dumps(conversation), session_id),
            )
        except Exception:
            await db.execute("ROLLBACK")
            raise
        else:
            await db.execute("COMMIT")
