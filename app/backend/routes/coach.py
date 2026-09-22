"""POST /api/coach/{id} — chat conversazionale con l'Assistente Educativo.

Usato sia dalla web app che dal bot Telegram (stesso Agent 5, stessa
Sessione). La guardia anti-consulenza (`is_investment_advice_request`) e'
applicata dentro `EducationalCoachAgent.chat` prima di qualunque chiamata LLM.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agents.educational_coach import EducationalCoachAgent
from app.backend import database
from app.backend.llm import get_llm_client
from app.backend.models import CoachRequest, Insight

router = APIRouter()


@router.post("/api/coach/{session_id}")
async def coach_chat(session_id: str, payload: CoachRequest) -> dict:
    session = await database.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessione non trovata")

    insights = [Insight.model_validate(item) for item in session["insights"]]
    agent = EducationalCoachAgent(llm_client=get_llm_client())
    reply = await agent.chat(insights, session["conversation"], payload.message)

    await database.append_conversation_message(session_id, "user", payload.message)
    await database.append_conversation_message(session_id, "assistant", reply)

    return {"reply": reply}
