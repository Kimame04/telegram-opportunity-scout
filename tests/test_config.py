"""Unit tests for config loading, validation, and modular profile parser."""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.config import AppConfig, load_config, load_profile


class TestConfig(unittest.TestCase):
    def test_credential_masking_in_repr(self):
        cfg = AppConfig(
            api_id=1234567,
            api_hash="abcdef0123456789",
            phone="+6599999999",
            channel_identifier="https://t.me/test",
            target_handle="@testhandle",
            lookback_hours=24,
            min_relevance_score=35,
            max_opportunities=5,
        )
        repr_str = repr(cfg)
        self.assertNotIn("1234567", repr_str)
        self.assertNotIn("abcdef0123456789", repr_str)
        self.assertIn("***67", repr_str)
        self.assertIn("***789", repr_str)

    def test_validation_missing_credentials(self):
        cfg = AppConfig(
            api_id=None,
            api_hash=None,
            phone=None,
            channel_identifier="https://t.me/test",
            target_handle="me",
            lookback_hours=24,
            min_relevance_score=35,
            max_opportunities=5,
        )
        with self.assertRaises(ValueError):
            cfg.validate_for_live_session()

    def test_load_profile_custom_json(self):
        with TemporaryDirectory() as tmpdir:
            profile_file = Path(tmpdir) / "custom_profile.json"
            profile_file.write_text(
                '{\n'
                '  "candidate": {\n'
                '    "title": "Quantum Computing Researcher",\n'
                '    "summary": "Exploring quantum algorithms and Qiskit."\n'
                '  },\n'
                '  "domains": [\n'
                '    {\n'
                '      "id": "quantum",\n'
                '      "name": "Quantum Computing",\n'
                '      "base_weight": 60,\n'
                '      "keywords": ["quantum", "qiskit", "qubit"],\n'
                '      "reason_template": "Matches quantum research."\n'
                '    }\n'
                '  ],\n'
                '  "negative_filters": ["crypto spam"],\n'
                '  "scoring": {\n'
                '    "min_threshold": 40,\n'
                '    "max_results": 3\n'
                '  }\n'
                '}'
            )
            prof = load_profile(profile_file)
            self.assertEqual(prof.title, "Quantum Computing Researcher")
            self.assertEqual(len(prof.domains), 1)
            self.assertEqual(prof.domains[0].id, "quantum")
            self.assertEqual(prof.min_threshold, 40)
            self.assertEqual(prof.max_results, 3)
            self.assertIn("crypto spam", prof.negative_filters)


if __name__ == "__main__":
    unittest.main()
