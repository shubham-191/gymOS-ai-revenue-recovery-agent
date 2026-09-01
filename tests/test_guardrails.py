"""
Unit tests for Policy Guardrails Engine.
"""
import pytest
from gymos_core.models import MemberProfile, MembershipTier, FailureReasonCode
from agent.policy_guardrails import PolicyGuardrailEngine


@pytest.fixture
def guardrails():
    return PolicyGuardrailEngine(
        max_discount_percentage=15.0,
        max_touches=3,
        strict_opt_out=True,
        vip_threshold_inr=50000.0
    )


def test_guardrail_clamp_excessive_discount(guardrails):
    member = MemberProfile(
        member_id="mem_01",
        name="Test User",
        phone="+919876543210",
        email="test@example.com",
        membership_tier=MembershipTier.QUARTERLY_PRO,
        membership_amount=6499.0,
        plan_start_date="2026-06-01",
        plan_expiry_date="2026-09-01"
    )
    # Propose 25% discount (exceeds 15% limit)
    allowed, bounded_discount, notes, verdict = guardrails.evaluate_proposed_action(
        member=member,
        proposed_discount_percentage=25.0,
        proposed_channel="whatsapp"
    )
    assert allowed is True
    assert bounded_discount == 15.0  # Clamped
    assert verdict == "CLAMPED"


def test_guardrail_strict_opt_out_stop(guardrails):
    member = MemberProfile(
        member_id="mem_opted_out",
        name="Opted Out User",
        phone="+919876543210",
        email="optout@example.com",
        membership_tier=MembershipTier.MONTHLY_BASIC,
        membership_amount=2499.0,
        plan_start_date="2026-06-01",
        plan_expiry_date="2026-09-01",
        opted_out=True
    )
    allowed, bounded_discount, notes, verdict = guardrails.evaluate_proposed_action(
        member=member,
        proposed_discount_percentage=10.0,
        proposed_channel="whatsapp"
    )
    assert allowed is False
    assert verdict == "BLOCKED_OPT_OUT"


def test_guardrail_max_touch_frequency(guardrails):
    member = MemberProfile(
        member_id="mem_max_touch",
        name="Spammed User",
        phone="+919876543210",
        email="spammed@example.com",
        membership_tier=MembershipTier.MONTHLY_BASIC,
        membership_amount=2499.0,
        plan_start_date="2026-06-01",
        plan_expiry_date="2026-09-01",
        consecutive_failed_attempts=3
    )
    allowed, bounded_discount, notes, verdict = guardrails.evaluate_proposed_action(
        member=member,
        proposed_discount_percentage=10.0,
        proposed_channel="whatsapp"
    )
    assert allowed is False
    assert verdict == "BLOCKED_MAX_TOUCHES"
