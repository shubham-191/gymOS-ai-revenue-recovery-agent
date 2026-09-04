"""
Unit tests for Root-Cause Diagnostician.
"""
import pytest
from gymos_core.models import MemberProfile, MembershipTier, FailureReasonCode
from agent.diagnostician import RecoveryDiagnostician, RootCauseCategory


@pytest.fixture
def diagnostician():
    return RecoveryDiagnostician()


def test_diagnose_technical_bank_failure(diagnostician):
    member = MemberProfile(
        member_id="mem_01",
        name="Amit Kumar",
        phone="+919876543210",
        email="amit@example.com",
        membership_tier=MembershipTier.MONTHLY_BASIC,
        membership_amount=2499.0,
        plan_start_date="2026-06-01",
        plan_expiry_date="2026-09-01",
        baseline_visits_per_week=4.0,
        actual_visits_last_30_days=15,
        days_since_last_checkin=1,
        last_failure_code=FailureReasonCode.BANK_SERVER_UNAVAILABLE
    )
    res = diagnostician.diagnose(member)
    assert res["root_cause"] == RootCauseCategory.TECHNICAL_BANKING_FAILURE
    assert res["confidence"] >= 0.90


def test_diagnose_silent_churn(diagnostician):
    member = MemberProfile(
        member_id="mem_02",
        name="Pooja Sharma",
        phone="+919876543211",
        email="pooja@example.com",
        membership_tier=MembershipTier.QUARTERLY_PRO,
        membership_amount=6499.0,
        plan_start_date="2026-06-01",
        plan_expiry_date="2026-09-01",
        baseline_visits_per_week=4.0,
        actual_visits_last_30_days=1,
        days_since_last_checkin=22,
        last_failure_code=FailureReasonCode.NONE
    )
    res = diagnostician.diagnose(member)
    assert res["root_cause"] == RootCauseCategory.SILENT_CHURN_DISENGAGEMENT
    assert res["confidence"] >= 0.85


def test_diagnose_vip_escalation(diagnostician):
    member = MemberProfile(
        member_id="mem_vip",
        name="Enterprise Corp",
        phone="+919876543299",
        email="admin@corp.com",
        membership_tier=MembershipTier.CORPORATE_VIP,
        membership_amount=75000.0,
        plan_start_date="2026-01-01",
        plan_expiry_date="2026-12-31",
        baseline_visits_per_week=5.0,
        actual_visits_last_30_days=20,
        days_since_last_checkin=2
    )
    res = diagnostician.diagnose(member)
    assert res["root_cause"] == RootCauseCategory.HIGH_VALUE_VIP_RISK
    assert res["confidence"] >= 0.95


def test_diagnose_disengaged_member_with_expired_mandate_classified_as_silent_churn(diagnostician):
    # Member mandate expired, but member hasn't visited in 20 days and had only 1 workout (planning to quit!)
    member = MemberProfile(
        member_id="mem_disengaged_mandate",
        name="Rajesh Khanna",
        phone="+919876543212",
        email="rajesh@example.com",
        membership_tier=MembershipTier.QUARTERLY_PRO,
        membership_amount=5849.0,
        plan_start_date="2026-06-01",
        plan_expiry_date="2026-09-01",
        baseline_visits_per_week=4.0,
        actual_visits_last_30_days=1,
        days_since_last_checkin=20,
        last_failure_code=FailureReasonCode.MANDATE_EXPIRED
    )
    res = diagnostician.diagnose(member)
    # Should diagnose as SILENT_CHURN_DISENGAGEMENT to trigger retention incentive!
    assert res["root_cause"] == RootCauseCategory.SILENT_CHURN_DISENGAGEMENT
    assert res["confidence"] >= 0.90
    assert "Disengagement is the primary churn driver" in res["reasoning"]


def test_diagnose_active_member_with_expired_mandate_classified_as_card_mandate_expired(diagnostician):
    # Member mandate expired, but member is active athlete (14 workouts in 30d, visited 2 days ago)
    member = MemberProfile(
        member_id="mem_active_mandate",
        name="Karan Malhotra",
        phone="+919876543213",
        email="karan@example.com",
        membership_tier=MembershipTier.QUARTERLY_PRO,
        membership_amount=5849.0,
        plan_start_date="2026-06-01",
        plan_expiry_date="2026-09-01",
        baseline_visits_per_week=4.0,
        actual_visits_last_30_days=14,
        days_since_last_checkin=2,
        last_failure_code=FailureReasonCode.MANDATE_EXPIRED
    )
    res = diagnostician.diagnose(member)
    # Active members get seamless link without unneeded margin discount
    assert res["root_cause"] == RootCauseCategory.CARD_MANDATE_EXPIRED
    assert res["confidence"] >= 0.90
    assert "actively attending" in res["reasoning"]

