"""
Evaluation layer: Google Gemini LLM API client for semantic evaluation.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from ..models import CandidateProfile, OpportunityPost, ScoredOpportunity
from .prompt import build_evaluation_prompt, extract_links

logger = logging.getLogger("telegram_scout.evaluation")


class LLMEvaluationError(Exception):
    """Raised when LLM API request or JSON parsing fails."""
    pass


def evaluate_post_gemini(
    post: OpportunityPost,
    profile: CandidateProfile,
    api_key: str,
    model: str = "gemini-3.5-flash-lite",
) -> Optional[ScoredOpportunity]:
    """Evaluates an opportunity post using Google Gemini API with fallback retry."""
    import time
    prompt = build_evaluation_prompt(post, profile)
    candidate_models = [model, "gemini-3.8-flash", "gemini-flash-latest"]

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }
    data_bytes = json.dumps(payload).encode("utf-8")

    last_error = None
    for attempt_model in candidate_models:
        clean_model = attempt_model.replace("models/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
        )

        for retry in range(2):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    raw_text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
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
                last_error = LLMEvaluationError(f"Gemini API ({clean_model}) HTTP {e.code}: {error_body}")
                if e.code in (429, 503):
                    time.sleep(2)
                    continue
                break
            except Exception as e:
                last_error = LLMEvaluationError(f"Failed Gemini evaluation ({clean_model}): {e}")
                time.sleep(1)

    if last_error:
        raise last_error
    return None
