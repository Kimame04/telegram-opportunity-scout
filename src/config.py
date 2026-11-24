"""
Configuration loader and credential sanitization for Opportunity Scout.

Reads configuration strictly from environment variables or a local `.env` file.
Loads modular profile configurations from `profile.json` (or `profile.example.json`).
Never leaks credentials in logs, string representations, or exception traces.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import CandidateProfile, DomainConfig


def _load_dotenv_file(filepath: Path) -> None:
    """Lightweight pure-Python .env file parser (zero-dependency)."""
    if not filepath.is_file():
        return

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key not in os.environ and val:
                    os.environ[key] = val


def load_profile(profile_path: Optional[Path] = None) -> CandidateProfile:
    """Load modular candidate profile from JSON file."""
    project_root = Path(__file__).resolve().parent.parent

    target_path = profile_path
    if target_path is None:
        candidates = [
            project_root / "profile.json",
            project_root / "profile.local.json",
            project_root / "profile.example.json",
        ]
        for c in candidates:
            if c.is_file():
                target_path = c
                break

    if target_path is None or not target_path.is_file():
        # Fallback minimal profile
        return CandidateProfile(
            title="Software Engineering Candidate",
            summary="General software engineering and technology opportunities.",
            preferred_role_types=["Internship", "Full-time", "Hackathon"],
            domains=[
                DomainConfig(
                    id="general_tech",
                    name="Software Engineering",
                    description="General software engineering and systems opportunities.",
                    keywords=["software engineer", "developer", "backend", "python", "programming"],
                )
            ],
            negative_filters=["sales representative", "telemarketing", "tuition teacher"],
        )

    with open(target_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    cand_data = data.get("candidate", {})
    scoring_data = data.get("scoring", {})

    domains = [
        DomainConfig(
            id=d.get("id", f"domain_{i}"),
            name=d.get("name", "Domain"),
            description=d.get("description", d.get("reason_template", "Matches domain skills.")),
            keywords=[k.strip() for k in d.get("keywords", []) if k.strip()],
        )
        for i, d in enumerate(data.get("domains", []))
    ]

    return CandidateProfile(
        title=cand_data.get("title", "Engineering Candidate"),
        summary=cand_data.get("summary", ""),
        preferred_role_types=cand_data.get("preferred_role_types", ["Internship"]),
        domains=domains,
        negative_filters=[f.strip().lower() for f in data.get("negative_filters", []) if f.strip()],
        min_threshold=int(scoring_data.get("min_threshold", 40)),
        max_results=int(scoring_data.get("max_results", 5)),
        llm_guidance=cand_data.get("llm_guidance", data.get("llm_guidance")),
    )


@dataclass(frozen=True)
class AppConfig:
    api_id: Optional[int]
    api_hash: Optional[str]
    phone: Optional[str]
    channel_identifier: str
    target_handle: str
    lookback_hours: int
    min_relevance_score: int
    max_opportunities: int
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    llm_provider: Optional[str] = None
    profile_path: Optional[str] = None

    def __repr__(self) -> str:
        # Obfuscate sensitive credentials
        masked_id = f"***{str(self.api_id)[-2:]}" if self.api_id else "None"
        masked_hash = f"***{self.api_hash[-3:]}" if self.api_hash else "None"
        return (
            f"AppConfig(api_id={masked_id}, api_hash={masked_hash}, "
            f"target_handle='{self.target_handle}', "
            f"channel='{self.channel_identifier}', "
            f"lookback_hours={self.lookback_hours}, "
            f"min_relevance_score={self.min_relevance_score})"
        )

    def validate_for_live_session(self) -> None:
        """Validate that essential MTProto credentials exist before connecting."""
        if not self.api_id:
            raise ValueError(
                "Missing TELEGRAM_API_ID in environment or .env. "
                "Get it from https://my.telegram.org."
            )
        if not self.api_hash:
            raise ValueError(
                "Missing TELEGRAM_API_HASH in environment or .env. "
                "Get it from https://my.telegram.org."
            )
        if not self.target_handle:
            raise ValueError(
                "Missing TELEGRAM_TARGET_HANDLE in environment or .env. "
                "Set to your handle (e.g. @your_username) or 'me'."
            )


def load_config(env_path: Optional[Path] = None, profile_path: Optional[Path] = None) -> AppConfig:
    """Load configuration from environment or specified .env path."""
    project_root = Path(__file__).resolve().parent.parent

    if env_path is None:
        env_path = project_root / ".env"

    if env_path.is_file():
        _load_dotenv_file(env_path)

    raw_api_id = os.environ.get("TELEGRAM_API_ID", "").strip()
    api_id = int(raw_api_id) if raw_api_id.isdigit() else None
    api_hash = os.environ.get("TELEGRAM_API_HASH", "").strip() or None
    phone = os.environ.get("TELEGRAM_PHONE", "").strip() or None

    channel_identifier = os.environ.get(
        "TELEGRAM_CHANNEL_IDENTIFIER",
        "https://t.me/joinchat/AAAAAEicCfFUq5kgF_xttg",
    ).strip()

    target_handle = os.environ.get("TELEGRAM_TARGET_HANDLE", "me").strip()

    try:
        lookback_hours = int(os.environ.get("LOOKBACK_HOURS", "24"))
    except ValueError:
        lookback_hours = 24

    try:
        min_relevance_score = int(os.environ.get("MIN_RELEVANCE_SCORE", "35"))
    except ValueError:
        min_relevance_score = 35

    try:
        max_opportunities = int(os.environ.get("MAX_OPPORTUNITIES", "5"))
    except ValueError:
        max_opportunities = 5

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip() or None
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip() or None
    llm_provider = os.environ.get("LLM_PROVIDER", "").strip().lower() or None

    return AppConfig(
        api_id=api_id,
        api_hash=api_hash,
        phone=phone,
        channel_identifier=channel_identifier,
        target_handle=target_handle,
        lookback_hours=lookback_hours,
        min_relevance_score=min_relevance_score,
        max_opportunities=max_opportunities,
        gemini_api_key=gemini_key,
        openai_api_key=openai_key,
        llm_provider=llm_provider,
        profile_path=str(profile_path) if profile_path else None,
    )
