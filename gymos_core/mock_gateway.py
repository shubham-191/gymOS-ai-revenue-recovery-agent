"""
Mock GymOS Integration Gateway & Event Generator.
Simulates incoming events from gym-backend-spring microservices.
"""
from typing import List
from gymos_core.models import MemberProfile, MembershipTier, FailureReasonCode
from gymos_core.event_bus import GymOSEventEnvelope, GymOSEventType


class GymOSGateway:
    """Provides bridge to fetch member profiles and simulate incoming platform signals."""

    @staticmethod
    def create_sample_member() -> MemberProfile:
        return MemberProfile(
            member_id="mem_blr_4091",
            name="Rahul Sharma",
            phone="+919876543210",
            email="rahul.sharma@example.com",
            language_preference="hinglish",
            membership_tier=MembershipTier.QUARTERLY_PRO,
            membership_amount=6499.0,
            plan_start_date="2026-06-01",
            plan_expiry_date="2026-09-01",
            baseline_visits_per_week=4.0,
            actual_visits_last_30_days=3,
            days_since_last_checkin=14,
            lifetime_paid_inr=19497.0,
            previous_payment_method="UPI_AUTOPAY",
            consecutive_failed_attempts=1,
            opted_out=False,
            last_failure_code=FailureReasonCode.INSUFFICIENT_FUNDS,
            last_failure_timestamp="2026-09-01T10:15:00Z"
        )
