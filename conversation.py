"""Conversation history management."""

from __future__ import annotations


class ConversationMemory:
    """Stores a limited number of recent conversation messages."""

    def __init__(self, max_messages: int = 8) -> None:
        self.max_messages = max_messages
        self._messages: list[dict[str, str]] = []

    def add_user_message(self, content: str) -> None:
        self._add("user", content)

    def add_assistant_message(self, content: str) -> None:
        self._add("assistant", content)

    def get_messages(self) -> list[dict[str, str]]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def _add(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]
