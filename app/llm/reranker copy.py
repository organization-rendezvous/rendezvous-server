#보관용
from app.llm.client import get_openai_client
import json

try:
    client = get_openai_client()
except Exception:
    client = None


def rerank_trends(trends: list[dict], topic: str) -> list[dict]:
    simplified = [
        {
            "title": t["title"],
            "keywords": t.get("keywords", []),
            "mention_count": t.get("mention_count", 0),
            "final_score": t.get("scores", {}).get("final_score", 0),
        }
        for t in trends
    ]

    prompt = f"""
너는 트렌드 분석 엔진이다.

주제: {topic}

아래 트렌드를 중요도 기준으로 재정렬하고 점수를 보정해라.

트렌드:
{json.dumps(simplified, ensure_ascii=False)}

출력 형식:
[
  {{
    "title": "...",
    "rerank_score": 0~100
  }}
]
"""

    if client is None:
        return trends

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    content = res.choices[0].message.content

    if not content:
        return trends  # fallback

    if content.startswith("```json"):
        content = content.split("```json")[1].split("```")[0].strip()

    elif content.startswith("```"):
        content = content.split("```")[1].split("```")[0].strip()

    try:
        reranked = json.loads(content)
    except json.JSONDecodeError:
        return trends

    try:
        reranked = json.loads(content)
    except json.JSONDecodeError:
        return trends  # fallback

    score_map = {r["title"]: r["rerank_score"] for r in reranked}

    for t in trends:
        t["scores"]["rerank_score"] = score_map.get(t["title"], t["scores"]["final_score"])
        t["scores"]["final_score"] = (
            t["scores"]["final_score"] * 0.6 +
            t["scores"]["rerank_score"] * 0.4
        )

    return sorted(trends, key=lambda x: x["scores"]["final_score"], reverse=True)