from app.llm.client import get_openai_client
import json
import re


def _safe_json_parse(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass

    return {
        "one_line_summary": text,
        "detail_summary": "",
        "importance_reason": "",
        "keywords": []
    }


def generate_trend_summaries_batch(trends: list[dict], topic: str) -> list[dict]:
    client = get_openai_client()  # ← 함수 호출 시점에 생성
    results = []

    for trend in trends:
        documents = trend.get("documents", [])

        context = "\n".join(
            (d.get("summary") or "") + " " + (d.get("title") or "")
            for d in documents[:5]
        )

        prompt = f"""
            너는 트렌드 분석 엔진이다.
            반드시 한국어로 작성해라.

            토픽: {topic}
            트렌드 제목: {trend.get("title", "")}

            문서:
            {context}

            반드시 아래 JSON 형식만 출력해라. 모든 텍스트 값은 한국어로 작성해라:

            {{
            "title": "",
            "one_line_summary": "",
            "detail_summary": "",
            "importance_reason": "",
            "keywords": []
            }}
        """

        if client is None:
            results.append({
                **trend,
                "title": parsed.get("title", trend.get("title", "")),  
                "llm_summary": parsed.get("one_line_summary", ""),
                "llm_detail_summary": parsed.get("detail_summary", ""),
                "llm_importance_reason": parsed.get("importance_reason", ""),
                "keywords": parsed.get("keywords", trend.get("keywords", []))
            })
            continue

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        content = res.choices[0].message.content

        parsed = _safe_json_parse(content) if content else {
            "one_line_summary": "",
            "detail_summary": "",
            "importance_reason": "",
            "keywords": []
        }

        results.append({
            **trend,
            "llm_summary": parsed.get("one_line_summary", ""),
            "llm_detail_summary": parsed.get("detail_summary", ""),
            "llm_importance_reason": parsed.get("importance_reason", ""),
            "keywords": parsed.get("keywords", trend.get("keywords", []))
        })

    return results