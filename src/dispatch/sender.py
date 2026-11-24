"""
Dispatch layer: Telegram message delivery using MTProto client.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger("telegram_scout.dispatch")


class BaseDispatcher(ABC):
    """Abstract interface for digest message dispatch."""

    @abstractmethod
    async def send_digest(self, target: str, messages: List[str]) -> bool:
        """Send formatted digest messages to the target recipient."""
        pass


class TelegramDispatcher(BaseDispatcher):
    """Dispatches formatted HTML digests to user handle or Saved Messages via Telethon."""

    def __init__(self, telethon_client):
        self.client = telethon_client

    async def send_digest(self, target: str, messages: List[str]) -> bool:
        """Send formatted HTML messages."""
        dest = "me" if target.lower() in ("me", "self", "saved") else target

        for msg in messages:
            await self.client.send_message(
                dest,
                msg,
                parse_mode="html",
                link_preview=False,
            )

        return True
