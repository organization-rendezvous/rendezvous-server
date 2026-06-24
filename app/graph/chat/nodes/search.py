from app.graph.chat.state import ChatState
from app.collectors.web_search import WebSearchCollector

import logging
logger = logging.getLogger(__name__)

def web_search_node(state: ChatState) -> ChatState:
    query = state.get("claim") or state["user_message"]
    web_hits: list[dict] = []

    try:
        collector = WebSearchCollector()
        web_hits = collector.search(query, limit=5)

    except Exception as e:
        logger.warning("웹 검색 실패: %s", e)

    return {**state, "web_hits": web_hits, "next_action": "generate_answer"}