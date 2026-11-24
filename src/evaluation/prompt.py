"""
Evaluation layer: Prompt engineering and link extraction utilities.
"""

from __future__ import annotations

import re
from typing import List, Set, Tuple

from ..models import CandidateProfile, OpportunityPost


def extract_links(text: str) -> List[Tuple[str, str]]:
    """Extract URLs and assign readable labels."""
    url_pattern = r"(https?://[^\s\)]+)"
    raw_urls = re.findall(url_pattern, text)
    results: List[Tuple[str, str]] = []
    seen: Set[str] = set()

    for url in raw_urls:
        clean_url = url.rstrip(".,;!?:\"')]>")
        # Handle markdown link syntax like [url](url)
        if "](" in clean_url:
            clean_url = clean_url.split("](")[0]
        if clean_url in seen:
            continue
        seen.add(clean_url)

        lower = clean_url.lower()
        if "forms.gle" in lower or "docs.google.com/forms" in lower:
            label = "Register via Google Form"
        elif "linkedin.com" in lower:
            label = "Apply on LinkedIn"
        elif "github.com" in lower:
            label = "GitHub Repository / Spec"
        elif "bit.ly" in lower or "tinyurl" in lower:
            label = "Application / Event Link"
        elif "talentconnect" in lower or "nus.edu" in lower:
            label = "University Career Portal"
        else:
            label = "Application / Details Link"

        results.append((label, clean_url))

    return results


def build_evaluation_prompt(post: OpportunityPost, profile: CandidateProfile) -> str:
    """Builds the comprehensive semantic evaluation prompt for the LLM."""
    domains_str = "\n".join(
        f"- {d.name}: {d.description} (Key signals: {', '.join(d.keywords)})"
        for d in profile.domains
    )
    role_types_str = ", ".join(profile.preferred_role_types) if profile.preferred_role_types else "Any relevant technical roles"
    negatives_str = ", ".join(profile.negative_filters) if profile.negative_filters else "None"
    guidance_str = f"\nAdditional Candidate Guidance:\n{profile.llm_guidance}" if profile.llm_guidance else ""

    prompt = f"""You are an expert technical career advisor and talent scout.
Your job is to semantically analyze this Telegram announcement and assess its relevance for the candidate.

=== CANDIDATE PROFILE ===
Headline: {profile.title}
Summary & Background: {profile.summary}

Target Domains of Interest:
{domains_str}

Preferred Role Types: {role_types_str}
Negative Filters (Strictly penalize or disqualify): {negatives_str}
{guidance_str}

=== TELEGRAM ANNOUNCEMENT ===
{post.text}

=== INSTRUCTIONS ===
1. Determine if this message is a genuine career opportunity, job opening, internship, competition/hackathon, or tech talk/webinar.
   (If it's channel banter, unrelated admin announcement, or spam, mark "is_opportunity": false).
2. Semantically score the relevance (0 to 100) based on alignment with the candidate's skills, aspirations, and experience.
   - 80-100: Exceptional direct match (core target skills, ideal role type, strong technical alignment).
   - 60-79: Strong fit (relevant domain, adjacent tech stack, or solid growth opportunity).
   - 40-59: Moderate fit (general tech role, partial skill overlap).
   - 0-39: Poor match, non-technical, or matches negative filters.
3. Extract the accurate role title and company/organization name.
4. Categorize under one of the target domains or "General Tech".
5. Detect if it is a career event/talk/hackathon ("is_event": true/false).
6. Provide 1 to 3 personalized bullet points explaining WHY this fits (or conflicts with) the candidate's profile.
7. Note any application deadlines if mentioned.

Respond ONLY with valid JSON matching this schema:
{{
  "is_opportunity": true,
  "title": "Clean Role or Event Title",
  "company": "Company / Organization Name or null",
  "domain_name": "Matched Domain Name",
  "relevance_score": 85,
  "role_type": "Internship | Full-time | Hackathon | Tech Talk | Other",
  "is_event": false,
  "deadline": "Extracted deadline string or null",
  "reasons": [
    "Personalized explanation of why this matches candidate's specific background and skills."
  ],
  "concerns": [
    "Any potential gaps, strict requirements, or caveats to consider."
  ]
}}
"""
    return prompt.strip()
