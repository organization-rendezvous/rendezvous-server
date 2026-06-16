import pytest
from app.analyzers import clean_documents, generate_candidates
from app.collectors import collect_documents
from app.scorers import score_trends

@pytest.mark.asyncio
async def test_collect_clean_candidate_score_pipeline():
    collected = await collect_documents("AI", "24h", ["rss", "official_blog", "news"])
    cleaned = clean_documents(collected["documents"])
    candidates = generate_candidates(cleaned)
    scored = score_trends(candidates, 3)

    assert collected["errors"] == []
    assert len(cleaned) >= 9
    assert len(candidates) >= 3
    assert len(scored) == 3

    assert scored[0].scores.final_score >= scored[-1].scores.final_score