"""Bot Telegram (aiogram, polling): stesso backend/pipeline della web app.

Un utente manda un Estratto Conto (CSV o PDF) al bot -> la pipeline gira
in-process (stesso Orchestrator usato da `routes/upload.py`) -> il bot
risponde con il link alla dashboard web. I messaggi di testo successivi sono
instradati all'EducationalCoach sulla Sessione piu' recente di quell'utente.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from aiogram.types import Message

from agents.educational_coach import EducationalCoachAgent
from agents.orchestrator import Orchestrator
from app.backend import database
from app.backend.llm import get_llm_client
from app.backend.models import Insight

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")


async def handle_file(message: Message) -> None:
    document = message.document
    bot = message.bot
    session_id = str(uuid.uuid4())

    await database.create_session(session_id)
    await database.set_telegram_session(
        session_id, telegram_user_id=message.from_user.id
    )

    file = await bot.get_file(document.file_id)
    file_bytes = await bot.download_file(file.file_path)
    content = file_bytes.read()

    await message.reply("📄 Ho ricevuto il tuo Estratto Conto, sto analizzando...")

    orchestrator = Orchestrator(llm_client=get_llm_client())
    try:
        async for event in orchestrator.run_pipeline([(document.file_name, content)]):
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
            else:
                # Stessi stage intermedi persistiti da routes/upload.py, cosi' una
                # Sessione creata da Telegram non resta bloccata su 'pending' mentre
                # la pipeline gira (es. se una dashboard aperta in parallelo la legge).
                await database.update_session_status(session_id, event.stage)
    except Exception:
        logger.exception("Pipeline fallita per la sessione %s", session_id)
        await database.mark_session_failed(session_id)
        await message.reply(
            "⚠️ Non sono riuscito ad analizzare il file. Verifica che sia un Estratto "
            "Conto in formato CSV o PDF supportato e riprova."
        )
        return

    await message.reply(
        "✅ Analisi completata!\n"
        f"🔗 {FRONTEND_URL}/dashboard/{session_id}\n\n"
        "Puoi anche chiedermi qui in chat cosa significano i tuoi Pattern di Spesa."
    )


async def handle_text(message: Message) -> None:
    session_id = await database.get_latest_session_for_telegram_user(
        message.from_user.id
    )
    if session_id is None:
        await message.reply(
            "Mandami prima un Estratto Conto (CSV o PDF) così posso analizzare le tue spese "
            "e risponderti in modo utile."
        )
        return

    session = await database.get_session(session_id)
    insights = [Insight.model_validate(item) for item in session["insights"]]

    agent = EducationalCoachAgent(llm_client=get_llm_client())
    reply = await agent.chat(insights, session["conversation"], message.text)

    await database.append_conversation_message(session_id, "user", message.text)
    await database.append_conversation_message(session_id, "assistant", reply)

    await message.reply(reply)


def build_dispatcher():
    """Costruisce il Dispatcher e registra gli handler.

    Va chiamato dopo che un event loop e' attivo (es. dentro `main()`): la
    creazione della Dispatcher aiogram alloca un asyncio.Lock che con uvloop
    richiede un loop gia' in esecuzione.
    """
    from aiogram import Dispatcher, F

    dp = Dispatcher()
    dp.message.register(handle_file, F.document)
    dp.message.register(handle_text, F.text)
    return dp


async def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN non configurato")

    from aiogram import Bot

    await database.init_db()
    dp = build_dispatcher()
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
