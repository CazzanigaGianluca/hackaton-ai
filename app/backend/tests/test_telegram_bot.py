from __future__ import annotations

import io
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.backend import database, telegram_bot


@pytest.fixture(autouse=True)
async def _use_temp_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_sessions.db")
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)
    monkeypatch.setattr(telegram_bot.database, "DATABASE_PATH", db_path)
    await database.init_db(db_path=db_path)
    yield


def _make_message(
    text: str | None = None, document=None, user_id: int = 42
) -> MagicMock:
    message = MagicMock()
    message.from_user.id = user_id
    message.text = text
    message.document = document
    message.reply = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_handle_text_without_prior_session_asks_for_a_file():
    message = _make_message(text="ciao", user_id=999)

    await telegram_bot.handle_text(message)

    message.reply.assert_awaited_once()
    assert "estratto conto" in message.reply.call_args.args[0].lower()


@pytest.mark.asyncio
async def test_handle_text_routes_investment_question_to_deflection(monkeypatch):
    session_id = str(uuid.uuid4())
    await database.create_session(session_id)
    await database.save_pipeline_result(session_id, [], {}, [], "Intro")
    await database.set_telegram_session(session_id, telegram_user_id=123)

    message = _make_message(text="dove dovrei investire i miei risparmi?", user_id=123)

    await telegram_bot.handle_text(message)

    message.reply.assert_awaited_once()
    reply_text = message.reply.call_args.args[0]
    assert "consulente finanziario" in reply_text.lower()


@pytest.mark.asyncio
async def test_handle_file_runs_pipeline_and_replies_with_dashboard_link(monkeypatch):
    csv_content = (
        b"Data,Descrizione,Importo,Valuta\n15/01/2025,CONAD SUPERMERCATI,-85.40,EUR\n"
    )

    document = MagicMock()
    document.file_id = "file-1"
    document.file_name = "estratto.csv"

    message = _make_message(document=document, user_id=555)
    bot = AsyncMock()
    bot.get_file.return_value = MagicMock(file_path="path/to/file")
    bot.download_file.return_value = io.BytesIO(csv_content)
    message.bot = bot

    await telegram_bot.handle_file(message)

    assert message.reply.await_count == 2
    final_reply = message.reply.call_args.args[0]
    assert "dashboard" in final_reply.lower()

    session_id = await database.get_latest_session_for_telegram_user(555)
    assert session_id is not None
    session = await database.get_session(session_id)
    assert session["status"] == "coaching_ready"


@pytest.mark.asyncio
async def test_handle_file_persists_intermediate_pipeline_stages(monkeypatch):
    csv_content = (
        b"Data,Descrizione,Importo,Valuta\n15/01/2025,CONAD SUPERMERCATI,-85.40,EUR\n"
    )

    document = MagicMock()
    document.file_id = "file-2"
    document.file_name = "estratto.csv"

    message = _make_message(document=document, user_id=777)
    bot = AsyncMock()
    bot.get_file.return_value = MagicMock(file_path="path/to/file")
    bot.download_file.return_value = io.BytesIO(csv_content)
    message.bot = bot

    observed_stages: list[str] = []
    original_update_status = database.update_session_status

    async def _spy_update_status(session_id, status, db_path=None):
        observed_stages.append(status)
        await original_update_status(session_id, status, db_path=db_path)

    monkeypatch.setattr(
        telegram_bot.database, "update_session_status", _spy_update_status
    )

    await telegram_bot.handle_file(message)

    # Le Sessioni create da Telegram devono passare dagli stessi stage intermedi
    # della pipeline web, non restare bloccate su 'pending' fino al risultato finale.
    assert "parsing" in observed_stages
    assert "categorizing" in observed_stages
    assert "analyzing" in observed_stages
