from app.graph.chat.state import ChatState
import logging
logger = logging.getLogger(__name__)

def card_builder_node(state: ChatState) -> ChatState:

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

