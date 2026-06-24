from __future__ import annotations
from app.db.repository_factory import repository
from app.graph.chat.workflow import run_chat_workflow
from app.core.config import DEFAULT_USER
import logging
logger = logging.getLogger(__name__)


# Session

def create_session(*, user_id: str = DEFAULT_USER, title: str | None = None) -> dict:
    return repository.create_chat_session(user_id=user_id, title=title)


def list_sessions(*, user_id: str = DEFAULT_USER) -> list[dict]:
    return repository.list_chat_sessions(user_id=user_id)


def get_session_with_messages(session_id: str) -> dict:
    session = repository.get_chat_session(session_id)
    messages = repository.list_chat_messages(session_id)

    message_ids = [m["id"] for m in messages if m["role"] == "assistant"]
    cards_by_msg: dict[str, list[dict]] = {}
    if message_ids:
        all_cards = repository.get_news_cards_by_messages(message_ids)
        for card in all_cards:
            cards_by_msg.setdefault(card["message_id"], []).append(card)

    return {
        **session,
        "messages": [
            {**msg, "news_cards": cards_by_msg.get(msg["id"], [])}
            for msg in messages
        ],
    }


def update_session(session_id: str, *, title: str) -> dict:
    return repository.update_chat_session(session_id, title=title)


def delete_session(session_id: str) -> bool:
    return repository.delete_chat_session(session_id)


# Message
def send_message(*, session_id: str, user_message: str) -> dict:
    """
    1. 사용자 메시지 저장
    2. workflow 실행 (intent → search → LLM → cards)
    3. assistant 메시지 + 뉴스 카드 저장
    4. 세션 제목 자동 생성 (첫 메시지일 때)
    5. 응답 반환
    """
    # 세션 존재 확인 (없으면 NotFoundError)
    repository.get_chat_session(session_id)

    # 사용자 메시지 저장
    repository.save_user_message(session_id=session_id, content=user_message)

    # workflow 실행
    state = run_chat_workflow(
        session_id=session_id,
        user_message=user_message
    )

    # assistant 메시지 저장
    assistant_msg = repository.save_assistant_message(
        session_id=session_id,
        content=state["answer"],
        intent=state.get("intent"),
        verdict=state.get("verdict"),
    )

    # 뉴스 카드 저장
    saved_cards = repository.save_news_cards(
        message_id=assistant_msg["id"],
        cards=state["cited_cards"],
    )

    # 첫 메시지면 제목 자동 생성
    _auto_title(session_id, user_message)

    return {
        "message": {**assistant_msg, "news_cards": saved_cards},
        "news_cards": saved_cards,
    }


def _auto_title(session_id: str, user_message: str) -> None:
    """세션 제목이 없을 때 첫 질문 앞 20자로 자동 설정."""
    try:
        title = user_message[:20] + ("..." if len(user_message) > 20 else "")
        repository.update_session_title_if_empty(session_id, title)
    except Exception as e:
        logger.warning("세션 제목 자동 생성 실패: %s", e)