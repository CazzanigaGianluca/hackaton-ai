"""Factory per il client LLM condiviso dagli agenti.

Ordine di risoluzione:
1. ANTHROPIC_API_KEY presente -> client Anthropic diretto (SDK ufficiale).
2. Nessuna API key ma il CLI `claude` (Claude Code) e' installato -> lo si
   invoca come sottoprocesso non interattivo (`claude -p`), riusando
   l'autenticazione gia' attiva sulla macchina (abbonamento Claude, non una
   chiave API separata).
3. Nessuno dei due -> None: gli agenti ricorrono ai propri fallback
   deterministici (utile per demo locali e per i test).

`ClaudeCliClient` espone la stessa interfaccia minima usata dagli agenti
(`client.messages.create(model=..., max_tokens=..., system=..., messages=[...])`
-> oggetto con `.content[0].text`), cosi' nessun agente deve sapere quale dei
due backend e' effettivamente in uso.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
from dataclasses import dataclass
from functools import lru_cache

_CODE_FENCE_RE = re.compile(r"^```[a-zA-Z]*\n?|\n?```\s*$")


def _strip_code_fences(text: str) -> str:
    """Il CLI, a differenza dell'API diretta, a volte avvolge il JSON richiesto in un
    code fence markdown (```json ... ```): gli agenti fanno `json.loads` sul testo
    grezzo, quindi va ripulito qui per non rompere il parsing lato agente."""
    return _CODE_FENCE_RE.sub("", text.strip()).strip()

_MODEL_TO_CLI_ALIAS = {
    "claude-sonnet-4-5": "sonnet",
    "claude-haiku-4-5-20251001": "haiku",
}


@dataclass
class _TextBlock:
    text: str


@dataclass
class _CliResponse:
    content: list[_TextBlock]


def _render_conversation(messages: list[dict]) -> str:
    """Il CLI in modalita' print e' single-turn: appiattisce l'history in testo.

    Con un solo messaggio (il caso comune) ritorna il contenuto cosi' com'e',
    senza introdurre prefissi "Utente:"/"Assistente:" che sporcherebbero
    prompt gia' pensati per essere JSON puro (es. insight_generator).
    """
    if len(messages) == 1:
        return str(messages[0]["content"])

    lines = []
    for message in messages:
        speaker = "Utente" if message["role"] == "user" else "Assistente"
        lines.append(f"{speaker}: {message['content']}")
    return "\n\n".join(lines)


class _Messages:
    async def create(
        self, *, model: str, max_tokens: int, system: str, messages: list[dict]
    ) -> _CliResponse:
        del max_tokens  # il CLI non espone un limite di output configurabile
        cli_model = _MODEL_TO_CLI_ALIAS.get(model, model)
        prompt = _render_conversation(messages)

        proc = await asyncio.create_subprocess_exec(
            "claude",
            "-p",
            "--model",
            cli_model,
            "--system-prompt",
            system,
            "--tools",
            "",
            "--output-format",
            "json",
            "--no-session-persistence",
            "--setting-sources",
            "",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(input=prompt.encode("utf-8"))
        if proc.returncode != 0:
            raise RuntimeError(
                f"claude CLI terminato con exit code {proc.returncode}: "
                f"{stderr.decode('utf-8', errors='replace')}"
            )

        payload = json.loads(stdout.decode("utf-8"))
        if payload.get("is_error"):
            raise RuntimeError(f"claude CLI ha risposto con errore: {payload}")

        text = _strip_code_fences(payload.get("result", ""))
        return _CliResponse(content=[_TextBlock(text=text)])


class ClaudeCliClient:
    """Adapter che imita l'interfaccia `AsyncAnthropic.messages.create`."""

    def __init__(self) -> None:
        self.messages = _Messages()


@lru_cache(maxsize=1)
def get_llm_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        from anthropic import AsyncAnthropic

        return AsyncAnthropic(api_key=api_key)

    if shutil.which("claude"):
        return ClaudeCliClient()

    return None
