"""Unit tests for the Evaluation layer."""

import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.config import load_profile
from src.evaluation import (
    LLMEvaluationError,
    build_evaluation_prompt,
    evaluate_post,
    evaluate_post_gemini,
    extract_links,
)
from src.models import OpportunityPost, ScoredOpportunity


class TestEvaluation(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile()

    def test_build_evaluation_prompt(self):
        post = OpportunityPost(
            message_id=1,
            date=datetime.now(),
            text="Autonomous vehicle robotics perception internship at Motional.",
        )
        prompt = build_evaluation_prompt(post, self.profile)

        self.assertIn("CANDIDATE PROFILE", prompt)
        self.assertIn(self.profile.title, prompt)
        self.assertIn("Autonomous vehicle robotics perception", prompt)
        self.assertIn("INSTRUCTIONS", prompt)
        self.assertIn("is_opportunity", prompt)

    def test_extract_links(self):
        text = "Register via https://forms.gle/test1234 or portal https://jobs.example.com/posting"
        links = extract_links(text)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0][0], "Register via Google Form")
        self.assertEqual(links[0][1], "https://forms.gle/test1234")

    def test_evaluate_post_missing_key(self):
        post = OpportunityPost(message_id=1, date=datetime.now(), text="test")
        with self.assertRaises(ValueError):
            evaluate_post(post, self.profile, gemini_key=None)

    def test_mock_evaluator_dispatch(self):
        post = OpportunityPost(message_id=1, date=datetime.now(), text="test")

        def mock_eval(p, prof):
            return ScoredOpportunity(
                post=p,
                title="Mocked Role",
                company="Mocked Corp",
                domain_name="Robotics",
                relevance_score=92,
                role_type="Internship",
                is_event=False,
                deadline="01 Jan 2027",
                match_reasons=["Direct semantic alignment with robotics."],
                concerns=[],
                action_links=[],
            )

        res = evaluate_post(post, self.profile, mock_evaluator=mock_eval)
        self.assertIsNotNone(res)
        self.assertEqual(res.title, "Mocked Role")
        self.assertEqual(res.relevance_score, 92)

    @patch("urllib.request.urlopen")
    def test_evaluate_post_gemini_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_json_content = json.dumps({
            "is_opportunity": True,
            "title": "Perception Engineer Intern",
            "company": "Autonomous AI Labs",
            "domain_name": "Robotics & Autonomous Systems",
            "relevance_score": 90,
            "role_type": "Internship",
            "is_event": False,
            "deadline": "15 Dec 2026",
            "reasons": ["Direct match for sensor fusion and ROS 2."],
            "concerns": ["Requires C++ proficiency."],
        })
        api_payload = {
            "candidates": [
                {"content": {"parts": [{"text": mock_json_content}]}}
            ]
        }
        mock_response.read.return_value = json.dumps(api_payload).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        post = OpportunityPost(
            message_id=10,
            date=datetime.now(),
            text="Autonomous AI Labs hiring Perception Engineer Intern. Apply at https://example.com/apply",
        )

        res = evaluate_post_gemini(post, self.profile, api_key="fake_key")
        self.assertIsNotNone(res)
        self.assertEqual(res.title, "Perception Engineer Intern")
        self.assertEqual(res.company, "Autonomous AI Labs")
        self.assertEqual(res.relevance_score, 90)
        self.assertEqual(res.deadline, "15 Dec 2026")
        self.assertIn("Requires C++ proficiency.", res.concerns)
        self.assertEqual(len(res.action_links), 1)

    @patch("urllib.request.urlopen")
    def test_evaluate_post_gemini_non_opportunity(self, mock_urlopen):
        mock_response = MagicMock()
        mock_json_content = json.dumps({
            "is_opportunity": False,
            "title": "Channel Announcement",
            "relevance_score": 0,
        })
        api_payload = {
            "candidates": [
                {"content": {"parts": [{"text": mock_json_content}]}}
            ]
        }
        mock_response.read.return_value = json.dumps(api_payload).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        post = OpportunityPost(
            message_id=11,
            date=datetime.now(),
            text="Reminder: channel maintenance tonight at 10pm.",
        )

        res = evaluate_post_gemini(post, self.profile, api_key="fake_key")
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
