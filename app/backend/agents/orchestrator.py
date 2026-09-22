"""Orchestratore della pipeline agentica: chiama i 5 agenti in sequenza.

Espone `run_pipeline` come async generator che produce eventi di progresso
(usati per SSE) e infine il risultato completo della Sessione.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from app.backend.agents.categorizer import CategorizerAgent
from app.backend.agents.data_analyzer import DataAnalyzerAgent
from app.backend.agents.document_parser import DocumentParserAgent
from app.backend.agents.educational_coach import EducationalCoachAgent
from app.backend.agents.insight_generator import InsightGeneratorAgent
from app.backend.models import Insight, Transaction

PIPELINE_STAGES = [
    "parsing",
    "categorizing",
    "analyzing",
    "generating_insights",
    "coaching_ready",
]


@dataclass
class PipelineEvent:
    stage: str
    done: bool = False
    result: Any = None


@dataclass
class PipelineResult:
    transactions: list[Transaction] = field(default_factory=list)
    analysis: dict = field(default_factory=dict)
    insights: list[Insight] = field(default_factory=list)
    coach_intro: str = ""


class Orchestrator:
    def __init__(self, llm_client=None):
        self._document_parser = DocumentParserAgent(llm_client=llm_client)
        self._categorizer = CategorizerAgent(llm_client=llm_client)
        self._data_analyzer = DataAnalyzerAgent()
        self._insight_generator = InsightGeneratorAgent(llm_client=llm_client)
        self._educational_coach = EducationalCoachAgent(llm_client=llm_client)

    async def run_pipeline(
        self, files: list[tuple[str, bytes]]
    ) -> AsyncIterator[PipelineEvent]:
        yield PipelineEvent(stage="parsing")
        transactions = await self._document_parser.run(files)

        yield PipelineEvent(stage="categorizing")
        categorized = await self._categorizer.run(transactions)

        yield PipelineEvent(stage="analyzing")
        analysis = await self._data_analyzer.run(categorized)

        yield PipelineEvent(stage="generating_insights")
        insights = await self._insight_generator.run(analysis)

        coach_intro = await self._educational_coach.run(insights)

        yield PipelineEvent(
            stage="coaching_ready",
            done=True,
            result=PipelineResult(
                transactions=categorized,
                analysis=analysis,
                insights=insights,
                coach_intro=coach_intro,
            ),
        )
