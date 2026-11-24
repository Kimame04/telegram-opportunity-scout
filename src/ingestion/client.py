"""
Ingestion layer: Telegram channel message collector using MTProto (Telethon).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

from ..config import AppConfig
from ..models import OpportunityPost

logger = logging.getLogger("telegram_scout.ingestion")


class BaseIngester(ABC):
    """Abstract interface for opportunity post ingestion."""

    @abstractmethod
    async def fetch_recent_messages(self, lookback_hours: int) -> List[OpportunityPost]:
        """Fetch posts within the specified lookback window."""
        pass


class TelegramIngester(BaseIngester):
    """Fetches messages from public or private Telegram channels via Telethon."""

    def __init__(self, config: AppConfig, session_name: str = "telegram_scout"):
        config.validate_for_live_session()

        try:
            from telethon import TelegramClient  # type: ignore
        except ImportError as e:
            raise ImportError(
                "Telethon is required for live Telegram ingestion. "
                "Install it with: pip install telethon"
            ) from e

        session_path = Path(__file__).resolve().parent.parent.parent / session_name
        self.config = config
        self.session_path = str(session_path)
        self.client = TelegramClient(self.session_path, config.api_id, config.api_hash)

    async def _resolve_channel_entity(self):
        """Resolves target channel entity (handles invite links or public @handles)."""
        from telethon.tl.functions.messages import CheckChatInviteRequest, ImportChatInviteRequest  # type: ignore

        channel_id = self.config.channel_identifier.strip()

        if "joinchat/" in channel_id or "t.me/+" in channel_id:
            invite_hash = channel_id.split("joinchat/")[-1] if "joinchat/" in channel_id else channel_id.split("t.me/+")[-1]
            invite_hash = invite_hash.strip("/")
            try:
                return await self.client.get_entity(channel_id)
            except Exception:
                try:
                    updates = await self.client(ImportChatInviteRequest(invite_hash))
                    return updates.chats[0]
                except Exception as ex:
                    logger.debug("Invite import note: %s", ex)
                    return await self.client.get_entity(channel_id)

        return await self.client.get_entity(channel_id)

    async def fetch_recent_messages(self, lookback_hours: int) -> List[OpportunityPost]:
        """Fetch messages from the channel within the lookback window."""
        await self.client.start(phone=self.config.phone)

        entity = await self._resolve_channel_entity()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

        posts: List[OpportunityPost] = []
        async for msg in self.client.iter_messages(entity, limit=200):
            if not msg.text:
                continue

            msg_date = msg.date
            if msg_date and msg_date < cutoff:
                break

            posts.append(
                OpportunityPost(
                    message_id=msg.id,
                    date=msg_date if msg_date else datetime.now(),
                    text=msg.text,
                    channel_title=getattr(entity, "title", "Telegram Channel"),
                )
            )

        return posts
