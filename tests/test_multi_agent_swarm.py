"""
Unit tests for Multi-Agent Swarm War Room.
"""
import pytest
from gymos_core.models import MemberProfile, MembershipTier, FailureReasonCode
from agent.multi_agent_swarm import MultiAgentWarRoomCoordinator


@pytest.fixture
def coordinator():
    return MultiAgentWarRoomCoordinator()


@pytest.fixture
def active_member():
    return MemberProfile(
        member_id="mem_swarm_01",
        name="Ananya Rao",
        phone="+919876543210",
        email="ananya@example.com",
        membership_tier=MembershipTier.QUARTERLY_PRO,
        membership_amount=6499.0,
        plan_start_date="2026-06-01",
        plan_expiry_date="2026-09-01",
        baseline_visits_per_week=4.0,
        actual_visits_last_30_days=1,
        days_since_last_checkin=19
    )


def test_swarm_full_pipeline_success(coordinator, active_member):
    res = coordinator.run_war_room_pipeline(active_member)
    assert res["status"] == "SUCCESSFULLY_ORCHESTRATED"
    assert len(res["steps"]) == 5
    assert res["payment_link"] is not None
    assert "sha256_audit_hash" in res


def test_swarm_auditor_veto_on_opt_out(coordinator):
    opted_out_member = MemberProfile(
        member_id="mem_swarm_opt",
        name="Veto User",
        phone="+919876543299",
        email="veto@example.com",
        membership_tier=MembershipTier.MONTHLY_BASIC,
        membership_amount=2499.0,
        plan_start_date="2026-06-01",
        plan_expiry_date="2026-09-01",
        opted_out=True
    )
    res = coordinator.run_war_room_pipeline(opted_out_member)
    assert res["status"] == "STOPPED_BY_AUDITOR"
    assert len(res["steps"]) == 3  # Stops after Auditor Agent Veto
    assert res["steps"][2]["status"] == "VETOED"
