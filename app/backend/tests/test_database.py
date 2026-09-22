import asyncio
import uuid

import pytest

from app.backend import database


@pytest.fixture
async def db_path(tmp_path):
    path = str(tmp_path / "test_sessions.db")
    await database.init_db(db_path=path)
    return path


@pytest.mark.asyncio
async def test_create_session_starts_with_pending_status(db_path):
    session_id = str(uuid.uuid4())
    await database.create_session(session_id, db_path=db_path)

    session = await database.get_session(session_id, db_path=db_path)
    assert session["status"] == "pending"
    assert session["transactions"] == []


@pytest.mark.asyncio
async def test_update_session_status_changes_status(db_path):
    session_id = str(uuid.uuid4())
    await database.create_session(session_id, db_path=db_path)
    await database.update_session_status(session_id, "parsing", db_path=db_path)

    session = await database.get_session(session_id, db_path=db_path)
    assert session["status"] == "parsing"


@pytest.mark.asyncio
async def test_save_pipeline_result_persists_all_fields(db_path):
    session_id = str(uuid.uuid4())
    await database.create_session(session_id, db_path=db_path)

    await database.save_pipeline_result(
        session_id,
        transactions=[{"description": "CONAD", "amount": -10.0}],
        analysis={"by_category": {}},
        insights=[{"category": "Alimentari", "user_pct": 20, "istat_pct": 19.2}],
        coach_intro="Ciao! Ecco la tua analisi.",
        db_path=db_path,
    )

    session = await database.get_session(session_id, db_path=db_path)
    assert session["status"] == "coaching_ready"
    assert session["transactions"] == [{"description": "CONAD", "amount": -10.0}]
    assert session["analysis"] == {"by_category": {}}
    assert session["coach_intro"] == "Ciao! Ecco la tua analisi."
    assert session["conversation"] == [
        {"role": "assistant", "content": "Ciao! Ecco la tua analisi."}
    ]


@pytest.mark.asyncio
async def test_get_session_returns_none_for_unknown_id(db_path):
    session = await database.get_session("does-not-exist", db_path=db_path)
    assert session is None


@pytest.mark.asyncio
async def test_append_conversation_message_grows_history(db_path):
    session_id = str(uuid.uuid4())
    await database.create_session(session_id, db_path=db_path)
    await database.save_pipeline_result(
        session_id, [], {}, [], "Intro", db_path=db_path
    )

    await database.append_conversation_message(
        session_id, "user", "Come posso risparmiare?", db_path=db_path
    )
    session = await database.get_session(session_id, db_path=db_path)
    assert session["conversation"][-1] == {
        "role": "user",
        "content": "Come posso risparmiare?",
    }
    assert len(session["conversation"]) == 2


@pytest.mark.asyncio
async def test_append_conversation_message_raises_for_unknown_session(db_path):
    with pytest.raises(ValueError):
        await database.append_conversation_message(
            "unknown", "user", "hello", db_path=db_path
        )


@pytest.mark.asyncio
async def test_telegram_session_linking(db_path):
    session_id = str(uuid.uuid4())
    await database.create_session(session_id, db_path=db_path)
    await database.set_telegram_session(
        session_id, telegram_user_id="12345", db_path=db_path
    )

    latest = await database.get_latest_session_for_telegram_user(
        "12345", db_path=db_path
    )
    assert latest == session_id


@pytest.mark.asyncio
async def test_mark_session_failed_sets_status(db_path):
    session_id = str(uuid.uuid4())
    await database.create_session(session_id, db_path=db_path)
    await database.mark_session_failed(session_id, db_path=db_path)

    session = await database.get_session(session_id, db_path=db_path)
    assert session["status"] == "failed"


@pytest.mark.asyncio
async def test_append_conversation_message_does_not_lose_concurrent_writes(db_path):
    session_id = str(uuid.uuid4())
    await database.create_session(session_id, db_path=db_path)
    await database.save_pipeline_result(
        session_id, [], {}, [], "Intro", db_path=db_path
    )

    await asyncio.gather(
        *(
            database.append_conversation_message(
                session_id, "user", f"messaggio {i}", db_path=db_path
            )
            for i in range(10)
        )
    )

    session = await database.get_session(session_id, db_path=db_path)
    # 1 messaggio iniziale (l'intro) + 10 append concorrenti = 11, nessuno perso.
    assert len(session["conversation"]) == 11
