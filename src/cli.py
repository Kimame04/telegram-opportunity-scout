"""
Command-Line Interface for Telegram Opportunity Scout.

Orchestrates the three-pillar pipeline:
1. Ingestion: Collects channel announcements (Telethon or Mock).
2. Evaluation: Semantically scores opportunities with LLM against CandidateProfile.
3. Dispatch: Formats HTML digest and sends to Telegram handle.

Usage:
    # Offline dry-run with mock ingester & simulated evaluation:
    python -m src.cli --sample --dry-run

    # Live scan and dispatch via Telegram:
    python -m src.cli

    # Live scan dry-run with real Gemini LLM evaluation:
    python -m src.cli --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Ensure parent directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.config import AppConfig, load_config, load_profile
from src.dispatch import BaseDispatcher, TelegramDispatcher, format_digest
from src.evaluation import evaluate_post
from src.ingestion import BaseIngester, TelegramIngester
from src.models import CandidateProfile, DailyDigest, ScoredOpportunity


async def run_pipeline(
    config: AppConfig,
    profile: CandidateProfile,
    ingester: BaseIngester,
    dispatcher: BaseDispatcher,
    dry_run: bool = False,
    is_sample: bool = False,
) -> int:
    """Executes the Ingestion -> Evaluation -> Dispatch pipeline."""

    # 1. INGESTION
    print(f"📡 [Ingestion] Fetching posts from channel (lookback: {config.lookback_hours}h)...")
    try:
        raw_posts = await ingester.fetch_recent_messages(config.lookback_hours)
    except Exception as e:
        print(f"❌ Ingestion failed: {e}", file=sys.stderr)
        return 1

    channel_name = raw_posts[0].channel_title if raw_posts else "Telegram Channel"
    print(f"📊 [Ingestion] Collected {len(raw_posts)} posts from '{channel_name}'.")

    # 2. EVALUATION
    print(f"🧠 [Evaluation] Semantically scoring opportunities for profile: '{profile.title}' using LLM...")
    evaluator_mock = None
    if is_sample and not config.gemini_api_key:
        from tests.mocks import mock_sample_evaluator
        evaluator_mock = mock_sample_evaluator

    scored_items: List[ScoredOpportunity] = []
    for post in raw_posts:
        try:
            res = evaluate_post(
                post,
                profile,
                gemini_key=config.gemini_api_key,
                openai_key=config.openai_api_key,
                provider=config.llm_provider,
                evaluator_fn=evaluator_mock,
            )
            if res is not None:
                scored_items.append(res)
        except Exception as e:
            print(f"⚠️ Error evaluating message {post.message_id}: {e}", file=sys.stderr)

    # Filter opportunities meeting score threshold
    matched_opps = [
        item for item in scored_items
        if item.relevance_score >= config.min_relevance_score
        and not item.is_event
    ]
    matched_opps.sort(key=lambda x: x.relevance_score, reverse=True)
    matched_opps = matched_opps[:profile.max_results]

    # Collect events & hackathons
    career_events = [
        item for item in scored_items
        if item.is_event
        and item.relevance_score >= max(20, config.min_relevance_score - 15)
    ]
    career_events.sort(key=lambda x: x.relevance_score, reverse=True)

    digest = DailyDigest(
        generated_at=datetime.now(),
        lookback_hours=config.lookback_hours,
        total_messages_scanned=len(raw_posts),
        matched_opportunities=matched_opps,
        career_events=career_events,
        channel_title=channel_name,
    )

    # 3. DISPATCH
    formatted_messages = format_digest(digest, profile)

    print("\n" + "=" * 60)
    print("📋 [Dispatch] TELEGRAM OPPORTUNITY SCOUT DIGEST PREVIEW")
    print("=" * 60)
    for idx, msg in enumerate(formatted_messages, 1):
        print(f"--- [Message Part {idx}/{len(formatted_messages)}] ---")
        print(msg)
        print()
    print("=" * 60)

    if dry_run:
        print("\n🧪 [Dispatch] Dry-run enabled: No messages sent to Telegram.")
        return 0

    print(f"\n🚀 [Dispatch] Delivering digest to target handle: '{config.target_handle}'...")
    try:
        success = await dispatcher.send_digest(config.target_handle, formatted_messages)
        if success:
            print("✅ [Dispatch] Digest successfully delivered!")
            return 0
        else:
            print("⚠️ [Dispatch] Delivery completed with warnings.", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"❌ [Dispatch] Delivery failed: {e}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Telegram Opportunity Scout - Modular LLM-Powered Career Digest."
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Path to custom candidate profile JSON file (defaults to profile.json or profile.example.json).",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Use bundled sample posts and simulated LLM evaluation for offline demonstration.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and preview the formatted digest in terminal without dispatching.",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Recipient Telegram handle (e.g. @username or 'me').",
    )
    parser.add_argument(
        "--channel",
        type=str,
        default=None,
        help="Telegram channel URL, invite link, or @handle to monitor.",
    )
    parser.add_argument(
        "--gemini-key",
        type=str,
        default=None,
        help="Google Gemini API key for semantic evaluation (defaults to GEMINI_API_KEY from .env).",
    )
    parser.add_argument(
        "--openai-key",
        type=str,
        default=None,
        help="OpenAI API key for semantic evaluation (defaults to OPENAI_API_KEY from .env).",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["gemini", "openai"],
        default=None,
        help="Force preferred LLM provider ('gemini' or 'openai').",
    )
    parser.add_argument(
        "--lookback-hours",
        type=int,
        default=None,
        help="Lookback window in hours (default: from .env or 24).",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=None,
        help="Minimum relevance score threshold 0-100 (default: from profile or 40).",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to custom .env file.",
    )

    args = parser.parse_args()

    env_path = Path(args.env_file).resolve() if args.env_file else None
    profile_path = Path(args.profile).resolve() if args.profile else None

    profile = load_profile(profile_path)
    config = load_config(env_path, profile_path)

    gemini_key = args.gemini_key or config.gemini_api_key
    openai_key = args.openai_key or config.openai_api_key
    provider = args.provider or config.llm_provider

    # Live evaluation without sample requires an LLM key
    if not args.sample and not (gemini_key or openai_key):
        print(
            "❌ Error: An LLM API key is required for semantic evaluation.\n"
            "   Add GEMINI_API_KEY=your_key or OPENAI_API_KEY=your_key to your .env file.\n"
            "   (To test offline without an API key, use --sample --dry-run)",
            file=sys.stderr,
        )
        sys.exit(1)

    # Apply overrides to config
    config = AppConfig(
        api_id=config.api_id,
        api_hash=config.api_hash,
        phone=config.phone,
        channel_identifier=args.channel or config.channel_identifier,
        target_handle=args.target or config.target_handle,
        lookback_hours=args.lookback_hours if args.lookback_hours is not None else config.lookback_hours,
        min_relevance_score=args.min_score if args.min_score is not None else config.min_relevance_score,
        max_opportunities=config.max_opportunities,
        gemini_api_key=gemini_key,
        openai_api_key=openai_key,
        llm_provider=provider,
    )

    # Determine Ingester and Dispatcher
    if args.sample or (args.dry_run and not (config.api_id and config.api_hash)):
        from tests.mocks import MockDispatcher, MockIngester
        ingester: BaseIngester = MockIngester()
        dispatcher: BaseDispatcher = MockDispatcher()
    else:
        try:
            live_ingester = TelegramIngester(config)
            ingester = live_ingester
            dispatcher = TelegramDispatcher(live_ingester.client)
        except Exception as e:
            if args.dry_run:
                from tests.mocks import MockDispatcher, MockIngester
                print(f"ℹ️ Telegram client connection skipped ({e}). Falling back to sample data for dry-run.")
                ingester = MockIngester()
                dispatcher = MockDispatcher()
            else:
                print(f"❌ Telegram connection error: {e}", file=sys.stderr)
                sys.exit(1)

    code = asyncio.run(
        run_pipeline(
            config,
            profile,
            ingester,
            dispatcher,
            dry_run=args.dry_run,
            is_sample=args.sample,
        )
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
