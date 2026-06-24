from app.graph.chat.state import ChatState
from app.graph.chat.nodes.intent import intent_classification_node
from app.graph.chat.nodes.search import web_search_node
from app.graph.chat.nodes.answer import answer_generation_node
from app.graph.chat.nodes.cards import card_builder_node


def run_chat_workflow(
    *,
    session_id: str,
    user_message: str,
) -> ChatState:

    state: ChatState = initialize_chat_state(
        session_id=session_id,
        user_message=user_message,
    )

    state = intent_classification_node(state)
    state = web_search_node(state)
    state = answer_generation_node(state)
    state = card_builder_node(state)

    return state


def initialize_chat_state(
    session_id: str,
    user_message: str,
) -> ChatState:

    return {
        "session_id": session_id,
        "user_message": user_message,
        "intent": None,
        "claim": None,
        "web_hits": [],
        "answer": "",
        "verdict": None,
        "cited_cards": [],
        "next_action": "classify_intent",
    }