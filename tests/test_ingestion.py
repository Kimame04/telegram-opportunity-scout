"""Unit tests for the Ingestion layer."""

import sys
import types
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.config import AppConfig
from src.ingestion.client import TelegramIngester
from src.models import OpportunityPost
from tests.fixtures import get_sample_posts
from tests.mocks import MockIngester


class TestIngestion(unittest.IsolatedAsyncioTestCase):
    async def test_sample_posts_generation(self):
        posts = get_sample_posts()
        self.assertGreaterEqual(len(posts), 4)
        for p in posts:
            self.assertIsInstance(p, OpportunityPost)
            self.assertGreater(len(p.text), 10)

    async def test_mock_ingester_lookback_filtering(self):
        now = datetime.now()
        posts = [
            OpportunityPost(message_id=1, date=now - timedelta(hours=2), text="Recent post"),
            OpportunityPost(message_id=2, date=now - timedelta(hours=30), text="Old post"),
        ]
        ingester = MockIngester(sample_posts=posts)

        # 24-hour lookback should only return post 1
        res = await ingester.fetch_recent_messages(lookback_hours=24)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].message_id, 1)

        # 48-hour lookback should return both posts
        res_48 = await ingester.fetch_recent_messages(lookback_hours=48)
        self.assertEqual(len(res_48), 2)

    def _make_config(self) -> AppConfig:
        return AppConfig(
            api_id=12345,
            api_hash="hash",
            phone="+6500000000",
            channel_identifier="@chan",
            target_handle="me",
            lookback_hours=24,
            min_relevance_score=40,
            max_opportunities=5,
        )

    def _make_ingester_with_mock_client(self, mock_client: MagicMock) -> TelegramIngester:
        fake_telethon = types.SimpleNamespace(TelegramClient=MagicMock(return_value=mock_client))
        with patch.dict(sys.modules, {"telethon": fake_telethon}):
            return TelegramIngester(self._make_config())

    async def test_connect_with_retry_succeeds_after_transient_errors(self):
        mock_client = MagicMock()
        mock_client.start = AsyncMock(
            side_effect=[OSError(51, "Network is unreachable"), ConnectionError("Connection failed"), None]
        )
        mock_client.disconnect = AsyncMock()

        ingester = self._make_ingester_with_mock_client(mock_client)
        await ingester._connect_with_retry(max_attempts=4, base_delay=0)

        self.assertEqual(mock_client.start.await_count, 3)
        self.assertEqual(mock_client.disconnect.await_count, 2)

    async def test_connect_with_retry_exhausts_attempts(self):
        mock_client = MagicMock()
        mock_client.start = AsyncMock(side_effect=ConnectionError("Network unreachable"))
        mock_client.disconnect = AsyncMock()

        ingester = self._make_ingester_with_mock_client(mock_client)
        with self.assertRaises(ConnectionError):
            await ingester._connect_with_retry(max_attempts=3, base_delay=0)

        self.assertEqual(mock_client.start.await_count, 3)

    async def test_connect_with_retry_does_not_retry_non_network_error(self):
        mock_client = MagicMock()
        mock_client.start = AsyncMock(side_effect=ValueError("Bad credentials"))
        mock_client.disconnect = AsyncMock()

        ingester = self._make_ingester_with_mock_client(mock_client)
        with self.assertRaises(ValueError):
            await ingester._connect_with_retry(max_attempts=3, base_delay=0)

        self.assertEqual(mock_client.start.await_count, 1)


if __name__ == "__main__":
    unittest.main()
