"""Mock Dispatcher for testing and offline simulation."""

from typing import List, Optional

from src.dispatch.sender import BaseDispatcher


class MockDispatcher(BaseDispatcher):
    """In-memory mock dispatcher for testing and offline dry-runs."""

    def __init__(self):
        self.dispatched_target: Optional[str] = None
        self.dispatched_messages: List[str] = []

    async def send_digest(self, target: str, messages: List[str]) -> bool:
        self.dispatched_target = target
        self.dispatched_messages.extend(messages)
        return True
