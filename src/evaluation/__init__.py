"""
Evaluation layer package.
"""

from typing import Any, Optional

from ..models import CandidateProfile, OpportunityPost, ScoredOpportunity
from .gemini import LLMEvaluationError, evaluate_post_gemini
from .openai_client import evaluate_post_openai
from .prompt import build_evaluation_prompt, extract_links


def evaluate_post(
    post: OpportunityPost,
    profile: CandidateProfile,
    gemini_key: Optional[str] = None,
    openai_key: Optional[str] = None,
    provider: Optional[str] = None,
    evaluator_fn: Optional[Any] = None,
    mock_evaluator: Optional[Any] = None,
    gemini_model: str = "gemini-3.5-flash-lite",
    openai_model: str = "gpt-4o-mini",
) -> Optional[ScoredOpportunity]:
    """
    Evaluates a post exclusively using LLM semantic reasoning.
    Supports Gemini API or OpenAI / compatible endpoints.
    """
    fn = evaluator_fn or mock_evaluator
    if fn is not None:
        return fn(post, profile)

    # Determine provider preference
    chosen_provider = (provider or "").lower()
    if chosen_provider == "openai" or (not gemini_key and openai_key):
        if not openai_key:
            raise ValueError("OPENAI_API_KEY is required when using the OpenAI provider.")
        return evaluate_post_openai(post, profile, api_key=openai_key, model=openai_model)

    if gemini_key:
        return evaluate_post_gemini(post, profile, api_key=gemini_key, model=gemini_model)

    if openai_key:
        return evaluate_post_openai(post, profile, api_key=openai_key, model=openai_model)

    raise ValueError(
        "An LLM API key (GEMINI_API_KEY or OPENAI_API_KEY) is required for semantic evaluation."
    )


__all__ = [
    "evaluate_post",
    "evaluate_post_gemini",
    "evaluate_post_openai",
    "build_evaluation_prompt",
    "extract_links",
    "LLMEvaluationError",
]
