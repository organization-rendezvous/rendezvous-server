from app.graph.chat.state import ChatState
from app.llm.client import get_openai_client
from app.llm.news_chat import classify_intent
import logging
logger = logging.getLogger(__name__)


def intent_classification_node(state: ChatState) -> ChatState:
    """
    node wrapper (state 적용)
    """

    client = get_openai_client()
    intent, claim = classify_intent(client,state["user_message"])

    return {
        **state,
        "intent": intent,
        "claim": claim,
        "next_action": "search_web",
    }