"""Unit tests for the Dispatch layer."""

import unittest
from datetime import datetime

from src.dispatch import format_digest, format_opportunity_card
from src.models import CandidateProfile, DailyDigest, OpportunityPost, ScoredOpportunity
from tests.mocks import MockDispatcher


class TestDispatch(unittest.IsolatedAsyncioTestCase):
    def test_format_empty_digest(self):
        digest = DailyDigest(
            generated_at=datetime.now(),
            lookback_hours=24,
            total_messages_scanned=10,
            matched_opportunities=[],
            career_events=[],
            channel_title="Announcements",
        )
        msgs = format_digest(digest)
        self.assertEqual(len(msgs), 1)
        self.assertIn("No high-relevance opportunities detected", msgs[0])

    def test_format_single_opportunity(self):
        post = OpportunityPost(message_id=1, date=datetime.now(), text="sample")
        opp = ScoredOpportunity(
            post=post,
            title="AV Software Intern <C++ & ROS>",
            company="Motional",
            domain_name="Robotics & Autonomous Systems",
            relevance_score=85,
            role_type="Internship",
            is_event=False,
            deadline="15 Jan 2027",
            match_reasons=["Direct fit for ROS 2"],
            concerns=["Requires embedded C++ knowledge."],
            action_links=[("Apply", "https://example.com")],
        )
        card = format_opportunity_card(opp, 1)
        self.assertIn("&lt;C++ &amp; ROS&gt;", card)
        self.assertIn("85% Match", card)
        self.assertIn("15 Jan 2027", card)
        self.assertIn("Requires embedded C++ knowledge.", card)

    def test_message_splitting(self):
        opps = []
        for i in range(25):
            post = OpportunityPost(message_id=i, date=datetime.now(), text=f"Long description {i} " * 20)
            opps.append(
                ScoredOpportunity(
                    post=post,
                    title=f"Role #{i} " + "A" * 50,
                    company=f"Company #{i}",
                    domain_name="Robotics",
                    relevance_score=80,
                    role_type="Internship",
                    is_event=False,
                    deadline=None,
                    match_reasons=[f"Reason #{i}"],
                    concerns=[],
                    action_links=[("Link", f"https://example.com/{i}")],
                )
            )

        digest = DailyDigest(
            generated_at=datetime.now(),
            lookback_hours=24,
            total_messages_scanned=25,
            matched_opportunities=opps,
            career_events=[],
            channel_title="Announcements",
        )
        msgs = format_digest(digest)
        self.assertGreater(len(msgs), 1)
        for msg in msgs:
            self.assertLessEqual(len(msg), 4000)

    async def test_mock_dispatcher_delivery(self):
        dispatcher = MockDispatcher()
        success = await dispatcher.send_digest("@test_user", ["<b>Message 1</b>", "<b>Message 2</b>"])
        self.assertTrue(success)
        self.assertEqual(dispatcher.dispatched_target, "@test_user")
        self.assertEqual(len(dispatcher.dispatched_messages), 2)


if __name__ == "__main__":
    unittest.main()
