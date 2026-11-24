"""
Evaluation layer: OpenAI or OpenAI-compatible endpoint evaluator.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from ..models import CandidateProfile, OpportunityPost, ScoredOpportunity
from .prompt import build_evaluation_prompt, extract_links

logger = logging.getLogger("telegram_scout.evaluation.openai")


def evaluate_post_openai(
    post: OpportunityPost,
    profile: CandidateProfile,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
) -> Optional[ScoredOpportunity]:
    """Evaluates an opportunity post using OpenAI or compatible endpoint."""
    prompt = build_evaluation_prompt(post, profile)
    endpoint = f"{base_url.rstrip('/')}/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert technical talent scout and career advisor."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data_bytes,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            raw_text = resp_data["choices"][0]["message"]["content"]
            parsed: Dict[str, Any] = json.loads(raw_text)

            if not parsed.get("is_opportunity", True):
                return None

            score = int(parsed.get("relevance_score", 0))
            title = parsed.get("title") or "Opportunity Announcement"
            company = parsed.get("company")
            domain_name = parsed.get("domain_name") or "General Tech"
            role_type = parsed.get("role_type")
            is_event = bool(parsed.get("is_event", False))
            deadline = parsed.get("deadline")
            reasons = parsed.get("reasons") or ["Matched candidate profile."]
            concerns = parsed.get("concerns") or []
            action_links = extract_links(post.text)

            return ScoredOpportunity(
                post=post,
                title=title,
                company=company,
                domain_name=domain_name,
                relevance_score=max(0, min(100, score)),
                role_type=role_type,
                is_event=is_event,
                deadline=deadline,
                match_reasons=reasons,
                concerns=concerns,
                action_links=action_links,
            )
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        logger.error("OpenAI API HTTP Error %d: %s", e.code, error_body)
        raise RuntimeError(f"OpenAI API HTTP {e.code}: {error_body}") from e
    except Exception as e:
        logger.error("OpenAI evaluation error: %s", e)
        raise RuntimeError(f"Failed OpenAI evaluation: {e}") from e
