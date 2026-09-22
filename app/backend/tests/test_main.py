from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.backend import database
from app.backend.main import app

SAMPLE_CSV = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "sample"
    / "estratto_gennaio_2025.csv"
)


@pytest.fixture(autouse=True)
async def _use_temp_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_sessions.db")
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)
    await database.init_db(db_path=db_path)
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_csv_bytes() -> bytes:
    return SAMPLE_CSV.read_bytes()


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_analyze_streams_all_pipeline_stages_and_persists_session(
    client, sample_csv_bytes
):
    files = [("files", ("estratto_gennaio_2025.csv", sample_csv_bytes, "text/csv"))]

    async with client.stream("POST", "/api/analyze", files=files) as response:
        assert response.status_code == 200
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                events.append(line)

    assert len(events) == 5
    assert "coaching_ready" in events[-1]


@pytest.mark.asyncio
async def test_session_not_found_returns_404(client):
    response = await client.get("/api/session/does-not-exist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_full_flow_upload_then_fetch_session_then_chat(client, sample_csv_bytes):
    files = [("files", ("estratto_gennaio_2025.csv", sample_csv_bytes, "text/csv"))]

    session_id = None
    async with client.stream("POST", "/api/analyze", files=files) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: ") and "session_id" in line:
                import json

                session_id = json.loads(line[len("data: ") :])["session_id"]

    assert session_id is not None

    session_response = await client.get(f"/api/session/{session_id}")
    assert session_response.status_code == 200
    session_data = session_response.json()
    assert session_data["status"] == "coaching_ready"
    assert len(session_data["transactions"]) > 0
    assert len(session_data["insights"]) > 0

    coach_response = await client.post(
        f"/api/coach/{session_id}",
        json={"message": "dove dovrei investire i miei risparmi?"},
    )
    assert coach_response.status_code == 200
    reply = coach_response.json()["reply"]
    assert "consulente finanziario" in reply.lower()
