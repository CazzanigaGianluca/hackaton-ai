from pathlib import Path

import pytest

from agents.orchestrator import PIPELINE_STAGES, Orchestrator

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sample"


def _load_sample_files() -> list[tuple[str, bytes]]:
    return [(path.name, path.read_bytes()) for path in sorted(SAMPLE_DIR.glob("*.csv"))]


@pytest.mark.asyncio
async def test_pipeline_emits_all_stages_in_order():
    orchestrator = Orchestrator(llm_client=None)
    files = _load_sample_files()

    stages_seen = []
    final_result = None
    async for event in orchestrator.run_pipeline(files):
        stages_seen.append(event.stage)
        if event.done:
            final_result = event.result

    assert stages_seen == PIPELINE_STAGES
    assert final_result is not None


@pytest.mark.asyncio
async def test_pipeline_produces_categorized_transactions_from_sample_data():
    orchestrator = Orchestrator(llm_client=None)
    files = _load_sample_files()

    final_result = None
    async for event in orchestrator.run_pipeline(files):
        if event.done:
            final_result = event.result

    assert len(final_result.transactions) > 0
    assert all(t.category is not None for t in final_result.transactions)


@pytest.mark.asyncio
async def test_pipeline_produces_insights_and_coach_intro_offline():
    orchestrator = Orchestrator(llm_client=None)
    files = _load_sample_files()

    final_result = None
    async for event in orchestrator.run_pipeline(files):
        if event.done:
            final_result = event.result

    assert len(final_result.insights) > 0
    assert isinstance(final_result.coach_intro, str)
    assert len(final_result.coach_intro) > 0
