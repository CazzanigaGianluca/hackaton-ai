"""POST /api/analyze — riceve uno o piu' Estratti Conto e avvia la pipeline.

La risposta e' un flusso SSE (`text/event-stream`) con un evento per ogni
stage della pipeline (`agents/orchestrator.py:PIPELINE_STAGES`), cosi' il
frontend puo' mostrare l'AgentProgress in tempo reale.
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

from app.backend.agents.orchestrator import Orchestrator
from app.backend import database
from app.backend.llm import get_llm_client

router = APIRouter()


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.post("/api/analyze")
async def analyze(files: list[UploadFile] = File(...)) -> StreamingResponse:  # noqa: B008 - idioma FastAPI
    session_id = str(uuid.uuid4())
    await database.create_session(session_id)
    file_payloads = [(f.filename or "estratto", await f.read()) for f in files]

    async def event_stream():
        orchestrator = Orchestrator(llm_client=get_llm_client())
        try:
            async for event in orchestrator.run_pipeline(file_payloads):
                if event.done:
                    result = event.result
                    await database.save_pipeline_result(
                        session_id,
                        transactions=[
                            t.model_dump(mode="json") for t in result.transactions
                        ],
                        analysis=result.analysis,
                        insights=[i.model_dump(mode="json") for i in result.insights],
                        coach_intro=result.coach_intro,
                    )
                    yield _sse(
                        {"stage": event.stage, "done": True, "session_id": session_id}
                    )
                else:
                    await database.update_session_status(session_id, event.stage)
                    yield _sse(
                        {"stage": event.stage, "done": False, "session_id": session_id}
                    )
        except Exception as exc:  # noqa: BLE001 - riportato come evento SSE al client
            await database.mark_session_failed(session_id)
            yield _sse({"stage": "failed", "done": True, "error": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
