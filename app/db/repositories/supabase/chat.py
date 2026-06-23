from __future__ import annotations

from app.core.errors import NotFoundError
from .base import utc_now


class ChatMixin:
    """chat_sessions / chat_messages / chat_news_cards 관련 메서드."""

    # ─────────────────────────────────────────
    # Session
    # ─────────────────────────────────────────

    def create_chat_session(
        self,
        *,
        user_id: str = "personal-user",
        title: str | None = None,
    ) -> dict:
        row = {
            "user_id": user_id,
            "title": title,
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
        }
        res = self.client.table("chat_sessions").insert(row).execute()
        return res.data[0]

    def list_chat_sessions(self, *, user_id: str = "personal-user") -> list[dict]:
        res = (
            self.client.table("chat_sessions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []

    def get_chat_session(self, session_id: str) -> dict:
        res = (
            self.client.table("chat_sessions")
            .select("*")
            .eq("id", session_id)
            .single()
            .execute()
        )
        if not res.data:
            raise NotFoundError("채팅 세션을 찾을 수 없습니다.")
        return res.data

    def update_chat_session(self, session_id: str, *, title: str) -> dict:
        res = (
            self.client.table("chat_sessions")
            .update({"title": title, "updated_at": utc_now().isoformat()})
            .eq("id", session_id)
            .execute()
        )
        if not res.data:
            raise NotFoundError("채팅 세션을 찾을 수 없습니다.")
        return res.data[0]

    def delete_chat_session(self, session_id: str) -> bool:
        self.client.table("chat_sessions").delete().eq("id", session_id).execute()
        return True

    def update_session_title_if_empty(self, session_id: str, title: str) -> None:
        """첫 메시지 기반 자동 제목 생성 — title이 없을 때만 업데이트."""
        session = self.get_chat_session(session_id)
        if not session.get("title"):
            self.update_chat_session(session_id, title=title)

    # ─────────────────────────────────────────
    # Message
    # ─────────────────────────────────────────

    def save_user_message(self, *, session_id: str, content: str) -> dict:
        row = {
            "session_id": session_id,
            "role": "user",
            "content": content,
            "created_at": utc_now().isoformat(),
        }
        res = self.client.table("chat_messages").insert(row).execute()
        return res.data[0]

    def save_assistant_message(
        self,
        *,
        session_id: str,
        content: str,
        intent: str | None = None,
        verdict: str | None = None,
    ) -> dict:
        row = {
            "session_id": session_id,
            "role": "assistant",
            "content": content,
            "intent": intent,
            "verdict": verdict,
            "created_at": utc_now().isoformat(),
        }
        res = self.client.table("chat_messages").insert(row).execute()
        return res.data[0]

    def list_chat_messages(self, session_id: str) -> list[dict]:
        res = (
            self.client.table("chat_messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        return res.data or []

    # ─────────────────────────────────────────
    # News Cards
    # ─────────────────────────────────────────

    def save_news_cards(self, *, message_id: str, cards: list[dict]) -> list[dict]:
        if not cards:
            return []

        rows = [
            {
                "message_id": message_id,
                "trend_id": card.get("trend_id"),
                "title": card["title"],
                "summary": card.get("summary"),
                "url": card["url"],
                "source": card["source"],
                "published_at": card.get("published_at"),
                "created_at": utc_now().isoformat(),
            }
            for card in cards
        ]
        res = self.client.table("chat_news_cards").insert(rows).execute()
        return res.data or []

    def get_news_cards_by_message(self, message_id: str) -> list[dict]:
        res = (
            self.client.table("chat_news_cards")
            .select("*")
            .eq("message_id", message_id)
            .execute()
        )
        return res.data or []

    def get_news_cards_by_messages(self, message_ids: list[str]) -> list[dict]:
        """여러 message_id에 대한 카드를 한 번에 조회."""
        if not message_ids:
            return []
        res = (
            self.client.table("chat_news_cards")
            .select("*")
            .in_("message_id", message_ids)
            .execute()
        )
        return res.data or []