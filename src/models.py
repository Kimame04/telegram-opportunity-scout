"""
Data models for Telegram Opportunity Scout.
Modular, candidate-agnostic, and tailored for LLM semantic evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class DomainConfig:
    """Configurable domain of interest for LLM evaluation."""
    id: str
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)


@dataclass
class CandidateProfile:
    """Candidate skills, background, and prompt guidance for LLM semantic evaluation."""
    title: str
    summary: str
    preferred_role_types: List[str] = field(default_factory=list)
    domains: List[DomainConfig] = field(default_factory=list)
    negative_filters: List[str] = field(default_factory=list)
    min_threshold: int = 40
    max_results: int = 5
    llm_guidance: Optional[str] = None


@dataclass
class OpportunityPost:
    """Raw message collected from a Telegram channel."""
    message_id: int
    date: datetime
    text: str
    channel_title: str = "Telegram Channel"
    links: List[str] = field(default_factory=list)


@dataclass
class ScoredOpportunity:
    """Opportunity evaluated and scored via LLM semantic analysis."""
    post: OpportunityPost
    title: str
    company: Optional[str]
    domain_name: str
    relevance_score: int  # 0 to 100
    role_type: Optional[str]
    is_event: bool
    deadline: Optional[str]
    match_reasons: List[str]
    concerns: List[str] = field(default_factory=list)
    action_links: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class DailyDigest:
    """Compiled daily digest ready for dispatch."""
    generated_at: datetime
    lookback_hours: int
    total_messages_scanned: int
    matched_opportunities: List[ScoredOpportunity]
    career_events: List[ScoredOpportunity]
    channel_title: str = "Telegram Channel"
