"""
Ingestion layer package.
"""

from .client import BaseIngester, TelegramIngester

__all__ = ["BaseIngester", "TelegramIngester"]
