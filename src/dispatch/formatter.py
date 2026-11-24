"""
Dispatch layer: HTML Digest Formatter for Telegram.
"""

from __future__ import annotations

import html
from typing import List, Optional

from ..models import CandidateProfile, DailyDigest, ScoredOpportunity

MAX_TELEGRAM_MESSAGE_LEN = 3900


def _badge_for_score(score: int) -> str:
    if score >= 90:
        return f"🔥 <b>{score}% Match</b> (Prime Fit)"
    elif score >= 75:
        return f"✨ <b>{score}% Match</b> (Strong Alignment)"
    elif score >= 50:
        return f"🔹 <b>{score}% Match</b> (Moderate Fit)"
    return f"▫️ <b>{score}% Match</b>"


def format_opportunity_card(opp: ScoredOpportunity, index: int) -> str:
    """Format an individual opportunity card in HTML."""
    title_escaped = html.escape(opp.title)
    comp = f" | {html.escape(opp.company)}" if opp.company else ""
    role_type = f" [{opp.role_type}]" if opp.role_type else ""

    lines = [
        f"<b>#{index} {title_escaped}</b>{comp}{role_type}",
        f"   └ {_badge_for_score(opp.relevance_score)}",
        f"   └ <i>Domain:</i> {html.escape(opp.domain_name)}",
    ]

    if opp.deadline:
        lines.append(f"   └ ⏰ <i>Deadline / Date:</i> {html.escape(opp.deadline)}")

    if opp.match_reasons:
        for r in opp.match_reasons:
            lines.append(f"   └ 💡 {html.escape(r)}")

    if opp.concerns:
        for c in opp.concerns:
            lines.append(f"   └ ⚠️ <i>Note:</i> {html.escape(c)}")

    if opp.action_links:
        link_strs = [f"<a href='{l_url}'>{html.escape(l_text)}</a>" for l_text, l_url in opp.action_links[:3]]
        lines.append(f"   └ 🔗 {' | '.join(link_strs)}")

    lines.append("")
    return "\n".join(lines)


def format_digest(digest: DailyDigest, profile: Optional[CandidateProfile] = None) -> List[str]:
    """Format the DailyDigest into one or more Telegram HTML messages."""
    date_str = digest.generated_at.strftime("%a, %d %b %Y")
    channel_name = html.escape(digest.channel_title)

    header = (
        f"🤖 <b>Telegram Opportunity Scout — Daily Digest</b>\n"
        f"📢 <i>{channel_name}</i>\n"
        f"📅 <i>{date_str}</i> (Lookback: {digest.lookback_hours}h | Scanned: {digest.total_messages_scanned} posts)\n"
        f"══════════════════════════════════════\n\n"
    )

    if not digest.matched_opportunities and not digest.career_events:
        empty_msg = (
            f"{header}"
            f"ℹ️ <i>No high-relevance opportunities detected in the last {digest.lookback_hours} hours.</i>\n\n"
            f"Active profile criteria remain engaged for the next scan cycle."
        )
        return [empty_msg]

    messages: List[str] = []
    current_chunk = header

    # Matched Opportunities
    if digest.matched_opportunities:
        opp_section = "🎯 <b>Matched Opportunities</b>\n\n"
        current_chunk += opp_section

        for idx, opp in enumerate(digest.matched_opportunities, 1):
            card = format_opportunity_card(opp, idx)
            if len(current_chunk) + len(card) > MAX_TELEGRAM_MESSAGE_LEN:
                messages.append(current_chunk.strip())
                current_chunk = f"🎯 <b>Matched Opportunities (Cont.)</b>\n\n{card}"
            else:
                current_chunk += card

    # Career Events & Hackathons
    if digest.career_events:
        event_section = "\n📅 <b>Tech Events, Talks & Hackathons</b>\n\n"
        if len(current_chunk) + len(event_section) > MAX_TELEGRAM_MESSAGE_LEN:
            messages.append(current_chunk.strip())
            current_chunk = event_section
        else:
            current_chunk += event_section

        for idx, evt in enumerate(digest.career_events, 1):
            card = format_opportunity_card(evt, idx)
            if len(current_chunk) + len(card) > MAX_TELEGRAM_MESSAGE_LEN:
                messages.append(current_chunk.strip())
                current_chunk = f"📅 <b>Events & Talks (Cont.)</b>\n\n{card}"
            else:
                current_chunk += card

    # Footer
    candidate_summary = f"Profile: {html.escape(profile.title)}\n" if profile and profile.title else ""
    footer = (
        f"\n<i>{candidate_summary}"
        f"Automated semantic evaluation by Telegram Opportunity Scout.</i>"
    )

    if len(current_chunk) + len(footer) > MAX_TELEGRAM_MESSAGE_LEN:
        messages.append(current_chunk.strip())
        messages.append(footer.strip())
    else:
        current_chunk += footer
        messages.append(current_chunk.strip())

    return messages
