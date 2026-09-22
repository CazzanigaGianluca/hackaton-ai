"""Factory per il client Anthropic condiviso dagli agenti.

Ritorna None se ANTHROPIC_API_KEY non e' configurata: gli agenti sanno
ricorrere ai propri fallback deterministici in quel caso (utile per demo
locali e per i test, che devono girare senza una chiave API reale).
"""

from __future__ import annotations

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_llm_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    from anthropic import AsyncAnthropic

    return AsyncAnthropic(api_key=api_key)
