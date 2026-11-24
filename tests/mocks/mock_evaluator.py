"""Mock Evaluator simulating LLM semantic evaluation for test fixtures."""

from typing import Optional

from src.models import CandidateProfile, OpportunityPost, ScoredOpportunity


def mock_sample_evaluator(
    post: OpportunityPost,
    profile: CandidateProfile,
) -> Optional[ScoredOpportunity]:
    """Simulates LLM semantic evaluation for bundled sample posts during testing."""
    mid = post.message_id

    if mid == 101:
        return ScoredOpportunity(
            post=post,
            title="Perception & Simulation Engineering Intern",
            company="Motional",
            domain_name="Robotics & Autonomous Systems",
            relevance_score=95,
            role_type="Internship",
            is_event=False,
            deadline="15 December 2026",
            match_reasons=[
                "Direct semantic alignment with your autonomous systems, ROS 2, and LiDAR perception background.",
                "Involves simulation pipelines and C++ embedded development.",
            ],
            concerns=[],
            action_links=[("Apply on Career Portal", "https://careers.motional.com/jobs/12345")],
        )
    elif mid == 102:
        return ScoredOpportunity(
            post=post,
            title="Applied Computer Vision Intern (PyTorch)",
            company="Institute for Infocomm Research",
            domain_name="Computer Vision & Applied AI",
            relevance_score=85,
            role_type="Internship",
            is_event=False,
            deadline="20 December 2026",
            match_reasons=[
                "Strong match for deep learning modeling, PyTorch CNN/Transformer training, and synthetic datasets.",
            ],
            concerns=[],
            action_links=[("Register via Google Form", "https://forms.gle/cvSampleForm")],
        )
    elif mid == 103:
        return ScoredOpportunity(
            post=post,
            title="Backend Infrastructure Intern (Go / C++)",
            company="ByteDance / TikTok",
            domain_name="Systems & High-Performance Software",
            relevance_score=75,
            role_type="Internship",
            is_event=False,
            deadline="31 December 2026",
            match_reasons=[
                "Matches your systems software engineering interest in Go, concurrency, and high-throughput pipelines.",
            ],
            concerns=[],
            action_links=[("Apply on ByteDance Careers", "https://jobs.bytedance.com/swe-intern")],
        )
    elif mid == 104:
        return ScoredOpportunity(
            post=post,
            title="Autonomous Systems Hackathon 2026",
            company="Hackathon Organizers",
            domain_name="Robotics & Autonomous Systems",
            relevance_score=80,
            role_type="Hackathon",
            is_event=True,
            deadline="05 December 2026",
            match_reasons=[
                "Relevant hands-on autonomous robotics navigation challenge with sponsor interview fast-tracking.",
            ],
            concerns=[],
            action_links=[("Register via Google Form", "https://forms.gle/roboticsHackathon")],
        )
    elif mid == 105:
        return ScoredOpportunity(
            post=post,
            title="Social Media Marketing Representative",
            company="Outreach Brand Agency",
            domain_name="Non-Technical",
            relevance_score=10,
            role_type="Marketing",
            is_event=False,
            deadline=None,
            match_reasons=["Non-technical telemarketing position."],
            concerns=["Violates candidate negative filter for sales/marketing."],
            action_links=[],
        )

    return None
