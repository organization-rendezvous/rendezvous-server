from __future__ import annotations

import json
import logging

from app.graph.chat_state import ChatState
from app.llm.client import get_openai_client
from app.llm.context_builder import build_llm_context
from app.collectors.web_search import WebSearchCollector

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Node 1 : Intent 분류
# ─────────────────────────────────────────────────────────────────────────────

def intent_classification_node(state: ChatState) -> ChatState:
    """
    사용자 메시지에서 intent(explore / factcheck)와
    factcheck인 경우 검증 대상 claim을 한 번의 LLM 호출로 추출한다.
    """
    client = get_openai_client()

    if client is None:
        logger.warning("OpenAI client is None — intent 분류 스킵, explore 로 기본 처리")
        return {**state, "intent": "explore", "claim": None, "next_action": "search_web"}

    prompt = f"""
너는 뉴스 채팅 의도 분류 엔진이다.

사용자 메시지: "{state['user_message']}"

아래 두 가지 중 하나로 분류하라.
- explore : 최근 뉴스/트렌드를 알고 싶은 일반 질문
- factcheck : 특정 소문/주장이 사실인지 확인하려는 질문

출력 형식 (JSON):
{{
  "intent": "explore" | "factcheck",
  "claim": "검증할 주장 (factcheck일 때만, 아니면 null)"
}}
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        content = res.choices[0].message.content or ""
        content = _strip_code_block(content)
        parsed = json.loads(content)
        intent = parsed.get("intent", "explore")
        claim = parsed.get("claim")
    except Exception as e:
        logger.warning("intent 분류 실패 — explore fallback: %s", e)
        intent = "explore"
        claim = None

    return {**state, "intent": intent, "claim": claim, "next_action": "search_web"}


# ─────────────────────────────────────────────────────────────────────────────
# Node 2 : 웹 검색 (항상 실행)
# ─────────────────────────────────────────────────────────────────────────────

def web_search_node(state: ChatState) -> ChatState:
    query = state.get("claim") or state["user_message"]
    web_hits: list[dict] = []

    try:
        collector = WebSearchCollector()
        web_hits = collector.search(query, limit=5)

        print("[WEB SEARCH DEBUG] query =", query)
        print("[WEB SEARCH DEBUG] hits =", json.dumps(web_hits, ensure_ascii=False, indent=2))

    except Exception as e:
        logger.warning("웹 검색 실패: %s", e)
        print("[WEB SEARCH DEBUG] error =", str(e))

    return {**state, "web_hits": web_hits, "next_action": "generate_answer"}


# ─────────────────────────────────────────────────────────────────────────────
# Node 3 : 답변 생성
# ─────────────────────────────────────────────────────────────────────────────

def answer_generation_node(state: ChatState) -> ChatState:
    print("[DEBUG] web_hits =", json.dumps(state["web_hits"], ensure_ascii=False, indent=2))
    """
    intent에 따라 분기:
    - explore   → 뉴스 기반 일반 답변
    - factcheck → 판정(verdict) 포함 답변
    """
    client = get_openai_client()

    context = build_llm_context(state["web_hits"], limit=6)

    if state["intent"] == "factcheck":
        answer, verdict = _run_factcheck(client, state["claim"] or state["user_message"], state["web_hits"])
    else:
        answer = _run_explore(client, state["user_message"], context)
        verdict = None

    return {**state, "answer": answer, "verdict": verdict, "next_action": "build_cards"}


def _run_explore(client, user_message: str, context: str) -> str:
    if client is None:
        return "현재 AI 서비스를 사용할 수 없습니다."

    prompt = f"""
너는 최신 뉴스와 트렌드를 알려주는 AI 어시스턴트다.

사용자 질문: {user_message}

아래 뉴스/트렌드 자료를 참고해 자연스럽게 답변하라.
자료가 부족해도 아는 범위 내에서 답변하라.

참고 자료:
{context}
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        return res.choices[0].message.content or "답변을 생성할 수 없습니다."
    except Exception as e:
        logger.error("explore 답변 생성 실패: %s", e)
        return "답변 생성 중 오류가 발생했습니다."


def _run_factcheck(client, claim: str, evidence: list[dict]) -> tuple[str, str]:
    """판정 결과 (answer 텍스트, verdict 문자열) 반환."""
    if client is None:
        return "현재 AI 서비스를 사용할 수 없습니다.", "unclear"

    prompt = f"""
너는 사실 검증 엔진이다.

확인할 주장: {claim}

아래는 관련 뉴스/문서 자료다:
{json.dumps(evidence[:6], ensure_ascii=False)}

위 자료를 근거로 주장이 사실인지 판단하라.
자료가 부족해 판단할 수 없으면 "unclear"로 답하라.
신뢰도 점수는 제공하지 말 것.

출력 형식 (JSON):
{{
  "verdict": "true" | "false" | "unclear",
  "reason": "판단 근거 한 문단 설명",
  "used_evidence_index": [0, 1]
}}
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        content = res.choices[0].message.content or ""
        content = _strip_code_block(content)
        parsed = json.loads(content)
        verdict = parsed.get("verdict", "unclear")
        reason = parsed.get("reason", "판단 근거를 확인할 수 없습니다.")
        return reason, verdict
    except Exception as e:
        logger.warning("factcheck 판정 실패: %s", e)
        return "사실 여부를 확인할 수 없습니다.", "unclear"


# ─────────────────────────────────────────────────────────────────────────────
# Node 4 : 카드 빌더
# ─────────────────────────────────────────────────────────────────────────────

def card_builder_node(state: ChatState) -> ChatState:
    print("[DEBUG] final web_hits =", json.dumps(state["web_hits"], ensure_ascii=False, indent=2))
    """
    web_hits에서 뉴스 카드를 구성한다.
    - url 없는 항목 제외
    - 제목 기준 중복 제거
    """
    cards: list[dict] = []
    seen_titles: set[str] = set()

    for hit in state["web_hits"]:
        if len(cards) >= 5:
            break
        url = hit.get("url", "")
        if not url:
            continue
        title = hit.get("title", "")
        norm_title = title.strip().lower()
        if norm_title in seen_titles:
            continue
        seen_titles.add(norm_title)
        cards.append({
            "trend_id": None,
            "title": title,
            "summary": hit.get("summary"),
            "url": url,
            "source": "web",
            "published_at": hit.get("published_at"),
        })

    return {**state, "cited_cards": cards, "next_action": "done"}


# ─────────────────────────────────────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────────────────────────────────────

def run_chat_workflow(
    *,
    session_id: str,
    user_message: str,
    repository=None,  # 웹 검색 전용이므로 repository는 선택적
) -> ChatState:
    """
    Chat workflow 전체를 실행하고 최종 state를 반환한다.
    내부 DB 없이 웹 검색만 사용한다.
    """
    state: ChatState = {
        "session_id": session_id,
        "user_message": user_message,
        "intent": None,
        "claim": None,
        "internal_hits": [],
        "web_hits": [],
        "answer": "",
        "verdict": None,
        "cited_cards": [],
        "next_action": "classify_intent",
    }

    state = intent_classification_node(state)
    state = web_search_node(state)
    state = answer_generation_node(state)
    state = card_builder_node(state)

    return state


# ─────────────────────────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────────────────────────

def _strip_code_block(content: str) -> str:
    if content.startswith("```json"):
        content = content.split("```json")[1].split("```")[0].strip()
    elif content.startswith("```"):
        content = content.split("```")[1].split("```")[0].strip()
    return content