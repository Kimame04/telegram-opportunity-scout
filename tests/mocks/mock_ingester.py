"""Mock Ingester for testing and offline simulation."""

from datetime import datetime, timedelta
from typing import List, Optional

from src.ingestion.client import BaseIngester
from src.models import OpportunityPost
from tests.fixtures.sample_posts import get_sample_posts


class MockIngester(BaseIngester):
    """Offline mock ingester for dry-runs and automated unit tests."""

    def __init__(self, sample_posts: Optional[List[OpportunityPost]] = None):
        self.posts = sample_posts if sample_posts is not None else get_sample_posts()

    async def fetch_recent_messages(self, lookback_hours: int) -> List[OpportunityPost]:
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        return [p for p in self.posts if p.date >= cutoff]
