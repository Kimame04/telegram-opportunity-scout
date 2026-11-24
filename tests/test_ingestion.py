"""Unit tests for the Ingestion layer."""

import unittest
from datetime import datetime, timedelta

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


if __name__ == "__main__":
    unittest.main()
