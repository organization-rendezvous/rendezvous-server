from __future__ import annotations

from typing import TypedDict


class ChatState(TypedDict):
    # 입력
    session_id: str
    user_message: str

    # intent 분류 결과
    intent: str | None           # "explore" | "factcheck"
    claim: str | None            # 팩트체크 대상 주장 (factcheck일 때만)

    # 검색 결과
    internal_hits: list[dict]    # 내부 DB (trends + trend_links)
    web_hits: list[dict]         # 웹 검색 결과 (fallback)

    # 답변 생성 결과
    answer: str
    verdict: str | None          # "true" | "false" | "unclear" (factcheck 전용)

    # 인라인 카드용 정리된 인용 목록
    cited_cards: list[dict]

    # workflow 흐름 제어
    next_action: str