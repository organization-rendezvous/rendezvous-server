from app.graph.chat.state import ChatState
from app.llm.client import get_openai_client
from app.llm.context_builder import build_llm_context
from app.llm.news_chat import (explore,factcheck)
import logging
logger = logging.getLogger(__name__)


def answer_generation_node(state: ChatState) -> ChatState:
    """
    intent에 따라 분기:
    - explore   → 뉴스 기반 일반 답변
    - factcheck → 판정(verdict) 포함 답변
    """
    client = get_openai_client()

    context = build_llm_context(state["web_hits"], limit=6)

    if state["intent"] == "factcheck":
        answer, verdict = factcheck(client, state["claim"] or state["user_message"], state["web_hits"])
    else:
        answer = explore(client, state["user_message"], context)
        verdict = None

    return {**state, "answer": answer, "verdict": verdict, "next_action": "build_cards"}

