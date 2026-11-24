"""Test fixtures: sample technical opportunity posts."""

from datetime import datetime, timedelta
from typing import List

from src.models import OpportunityPost


def get_sample_posts() -> List[OpportunityPost]:
    """Generates realistic sample posts representative of technical career channels."""
    now = datetime.now()

    return [
        OpportunityPost(
            message_id=101,
            date=now - timedelta(hours=2),
            text=(
                "🚀 [Internship] Autonomous Vehicles & Robotics Perception Intern\n"
                "Company: Motional\n"
                "Role: Perception & Simulation Engineering Intern\n\n"
                "We are looking for students passionate about:\n"
                "- ROS 2 / ROS middleware, embedded Linux, and modern C++\n"
                "- Sensor calibration, LiDAR point clouds, and computer vision\n"
                "- Physics-based simulation and synthetic data pipelines\n\n"
                "Apply by: 15 December 2026\n"
                "Portal: https://careers.motional.com/jobs/12345\n"
                "Contact: university-recruiting@motional.com"
            ),
            channel_title="Tech Career & Opportunity Hub",
        ),
        OpportunityPost(
            message_id=102,
            date=now - timedelta(hours=5),
            text=(
                "🧠 [Research Fellowship] Computer Vision & Deep Learning Intern\n"
                "Company: Institute for Infocomm Research\n"
                "Role: Applied Computer Vision Intern (PyTorch)\n\n"
                "Join our research group developing real-time edge vision architectures:\n"
                "• Training CNN and Transformer models using PyTorch\n"
                "• Multi-camera spatial tracking and synthetic dataset generation\n"
                "• Edge AI deployment on embedded hardware\n\n"
                "Deadline: 20 December 2026\n"
                "Registration Form: https://forms.gle/cvSampleForm"
            ),
            channel_title="Tech Career & Opportunity Hub",
        ),
        OpportunityPost(
            message_id=103,
            date=now - timedelta(hours=8),
            text=(
                "⚡ [Backend & Infrastructure] High-Performance Distributed Systems Intern\n"
                "Company: ByteDance / TikTok\n"
                "Role: Backend Infrastructure Intern (Go / C++)\n\n"
                "Key Responsibilities:\n"
                "- Build high-throughput distributed telemetry and data streaming services\n"
                "- Low-latency storage engines, concurrency optimization, and gRPC\n\n"
                "Apply before: 31 December 2026\n"
                "Link: https://jobs.bytedance.com/swe-intern"
            ),
            channel_title="Tech Career & Opportunity Hub",
        ),
        OpportunityPost(
            message_id=104,
            date=now - timedelta(hours=12),
            text=(
                "🏆 [Competition] Autonomous Systems Hackathon 2026\n"
                "Category: Hackathon & Competitive Challenge\n\n"
                "Compete to program autonomous navigation and obstacle avoidance for robotic rovers.\n"
                "Over $15,000 in prizes and fast-track interview tracks for top performers!\n\n"
                "Event Date: 12 December 2026\n"
                "Register by: 05 December 2026\n"
                "RSVP Link: https://forms.gle/roboticsHackathon"
            ),
            channel_title="Tech Career & Opportunity Hub",
        ),
        OpportunityPost(
            message_id=105,
            date=now - timedelta(hours=16),
            text=(
                "📢 [Unrelated / Spam] Social Media Marketing Representative\n"
                "Company: Outreach Brand Agency\n"
                "Role: Telemarketing & Influencer Outreach\n\n"
                "Looking for energetic individuals to manage promotional calls and TikTok campaigns.\n"
                "No technical skills or programming required.\n"
                "Apply: https://marketingjobs.example.com"
            ),
            channel_title="Tech Career & Opportunity Hub",
        ),
    ]
