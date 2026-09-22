"""Modelli Pydantic condivisi dal backend.

Il vocabolario (Transazione, Entrata/Uscita, Categoria, Sessione, Insight) segue
CONTEXT.md — non rinominare questi concetti altrove nel codice.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    ENTRATA = "entrata"
    USCITA = "uscita"


class Category(str, Enum):
    ALIMENTARI = "Alimentari"
    RISTORAZIONE = "Ristorazione"
    TRASPORTI = "Trasporti"
    UTENZE = "Utenze"
    ABBIGLIAMENTO = "Abbigliamento"
    INTRATTENIMENTO = "Intrattenimento"
    SALUTE = "Salute"
    SHOPPING_ONLINE = "Shopping Online"
    COMMISSIONI_BANCARIE = "Commissioni Bancarie"
    STIPENDIO_ENTRATE = "Stipendio/Entrate"
    ALTRO = "Altro"


class Transaction(BaseModel):
    date: date
    description: str
    amount: float
    type: TransactionType
    category: Category | None = None
    source_file: str | None = None


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Insight(BaseModel):
    category: str
    user_pct: float
    istat_pct: float
    trend: str
    severity: Severity


class AnalyzeResponse(BaseModel):
    session_id: str


class SessionStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    CATEGORIZING = "categorizing"
    ANALYZING = "analyzing"
    GENERATING_INSIGHTS = "generating_insights"
    COACHING_READY = "coaching_ready"
    FAILED = "failed"


class SessionData(BaseModel):
    session_id: str
    status: SessionStatus
    transactions: list[Transaction] = Field(default_factory=list)
    analysis: dict | None = None
    insights: list[Insight] = Field(default_factory=list)
    coach_intro: str | None = None


class CoachMessage(BaseModel):
    role: str
    content: str


class CoachRequest(BaseModel):
    message: str
