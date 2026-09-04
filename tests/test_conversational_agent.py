"""
Unit tests for Two-Way Conversational Recovery Agent & Objection Negotiation.
"""
import pytest
from gymos_core.models import MemberProfile, MembershipTier, FailureReasonCode
from agent.conversational_agent import ConversationalRecoveryAgent, UserIntentType


@pytest.fixture
def chat_agent():
    return ConversationalRecoveryAgent()


@pytest.fixture
def sample_member():
    return MemberProfile(
        member_id="mem_test_chat",
        name="Rahul Sharma",
        phone="+919876543210",
        email="rahul@example.com",
        membership_tier=MembershipTier.ANNUAL_ELITE,
        membership_amount=19999.0,
        plan_start_date="2026-01-01",
        plan_expiry_date="2026-09-01"
    )


def test_chat_injury_freeze_intent(chat_agent, sample_member):
    res = chat_agent.handle_incoming_message(sample_member, "I met with an accident and broke my leg, need to pause for 30 days.")
    assert res["intent"] == UserIntentType.TRAVEL_OR_INJURY
    assert res["action_executed"]["action"] == "FREEZE_MEMBERSHIP"
    assert res["action_executed"]["freeze_duration_days"] == 30
    assert "freeze" in res["reply_message"].lower()


def test_chat_travel_exact_days_freeze(chat_agent, sample_member):
    res = chat_agent.handle_incoming_message(sample_member, "I am traveling to my hometown for 3 weeks and will resume after that.")
    assert res["intent"] == UserIntentType.TRAVEL_OR_INJURY
    assert res["action_executed"]["action"] == "FREEZE_MEMBERSHIP"
    assert res["action_executed"]["freeze_duration_days"] == 21
    assert "21 days" in res["reply_message"]

    res_10 = chat_agent.handle_incoming_message(sample_member, "Going on a family trip for 10 days, please pause.")
    assert res_10["action_executed"]["freeze_duration_days"] == 10
    assert "10 days" in res_10["reply_message"]


def test_chat_price_resistance_downgrade(chat_agent, sample_member):
    res = chat_agent.handle_incoming_message(sample_member, "Annual plan is too expensive for me right now. Can I downgrade to monthly?")
    assert res["intent"] == UserIntentType.PRICE_TOO_HIGH
    assert res["action_executed"]["action"] == "DOWNGRADE_PLAN"
    assert res["payment_link"] is not None
    assert "2,499" in res["reply_message"]


def test_chat_salary_delay_promise_to_pay(chat_agent, sample_member):
    res = chat_agent.handle_incoming_message(sample_member, "Salary delayed this month, please wait until 25th.")
    assert res["intent"] == UserIntentType.SALARY_DELAY_PROMISE
    assert res["action_executed"]["action"] == "PROMISE_TO_PAY"
    assert res["action_executed"]["promised_payment_date"] == "25th"
    assert "25th" in res["reply_message"]


def test_chat_bounded_discount_request(chat_agent, sample_member):
    res = chat_agent.handle_incoming_message(sample_member, "Any renewal discount available? Will pay right now.")
    assert res["intent"] == UserIntentType.REQUEST_DISCOUNT
    assert res["action_executed"]["discount_percent"] <= 15.0
    assert res["payment_link"] is not None


def test_chat_dynamic_guardrail_clamping_to_9_percent():
    from agent.policy_guardrails import PolicyGuardrailEngine
    at_risk_member = MemberProfile(
        member_id="mem_clamped_test",
        name="Sunita Verma",
        phone="+919876543210",
        email="sunita@example.com",
        membership_tier=MembershipTier.ANNUAL_ELITE,
        membership_amount=12000.0,
        plan_start_date="2026-01-01",
        plan_expiry_date="2026-09-01",
        days_since_last_checkin=12,
        actual_visits_last_30_days=3,
        baseline_visits_per_week=2.0
    )
    # Merchant sets max discount ceiling to 9.0%
    custom_guardrail = PolicyGuardrailEngine(max_discount_percentage=9.0)
    agent_with_9pct_cap = ConversationalRecoveryAgent(guardrail_engine=custom_guardrail)
    
    # User asks for 20% discount
    res = agent_with_9pct_cap.handle_incoming_message(at_risk_member, "Can I get 20% discount on renewal?")
    assert res["intent"] == UserIntentType.REQUEST_DISCOUNT
    assert res["action_executed"]["discount_percent"] == 9.0
    assert res["action_executed"]["was_clamped_by_guardrail"] is True
    assert "9%" in res["reply_message"]
    assert "20%" in res["reply_message"]


def test_chat_super_regular_discount_denied_with_value_add():
    from agent.policy_guardrails import PolicyGuardrailEngine
    super_regular_member = MemberProfile(
        member_id="mem_super_regular",
        name="Aman Gupta",
        phone="+919876543210",
        email="aman@example.com",
        membership_tier=MembershipTier.ANNUAL_ELITE,
        membership_amount=10000.0,
        plan_start_date="2026-01-01",
        plan_expiry_date="2026-09-01",
        days_since_last_checkin=2,
        actual_visits_last_30_days=16  # Super dedicated regular attendee (16 workouts)
    )
    guardrail_15 = PolicyGuardrailEngine(max_discount_percentage=15.0)
    agent = ConversationalRecoveryAgent(guardrail_engine=guardrail_15)

    # Super regular member asks: "any discount available?"
    res = agent.handle_incoming_message(super_regular_member, "Is there any discount available?")
    assert res["intent"] == UserIntentType.REQUEST_DISCOUNT
    # Zero cash discount granted! Zero margin leakage for power users
    assert res["action_executed"]["discount_percent"] == 0.0
    assert res["action_executed"]["is_super_regular"] is True
    assert res["action_executed"]["action"] == "DISCOUNT_DENIED_SUPER_REGULAR"
    assert "dedicated" in res["reply_message"].lower()
    assert "InBody" in res["reply_message"]


def test_chat_graduated_discount_not_surrendering_max_on_first_ask():
    from agent.policy_guardrails import PolicyGuardrailEngine
    moderate_member = MemberProfile(
        member_id="mem_moderate_regular",
        name="Rohan Mehra",
        phone="+919876543210",
        email="rohan@example.com",
        membership_tier=MembershipTier.ANNUAL_ELITE,
        membership_amount=10000.0,
        plan_start_date="2026-01-01",
        plan_expiry_date="2026-09-01",
        days_since_last_checkin=7,
        actual_visits_last_30_days=5  # Moderate attendee
    )
    guardrail_15 = PolicyGuardrailEngine(max_discount_percentage=15.0)
    agent = ConversationalRecoveryAgent(guardrail_engine=guardrail_15)

    # Moderate member casually asks: "any discount available?"
    res = agent.handle_incoming_message(moderate_member, "Is there any discount available?")
    assert res["intent"] == UserIntentType.REQUEST_DISCOUNT
    # Should NOT give 15% immediately! Gives starter 5% token
    assert res["action_executed"]["discount_percent"] == 5.0
    assert "5%" in res["reply_message"]


def test_chat_zero_discount_policy_rejection(sample_member):
    from agent.policy_guardrails import PolicyGuardrailEngine
    zero_guardrail = PolicyGuardrailEngine(max_discount_percentage=0.0)
    agent = ConversationalRecoveryAgent(guardrail_engine=zero_guardrail)

    res = agent.handle_incoming_message(sample_member, "Can you give me discount?")
    assert res["intent"] == UserIntentType.REQUEST_DISCOUNT
    assert res["action_executed"]["action"] == "DISCOUNT_REJECTED_POLICY"
    assert res["action_executed"]["discount_percent"] == 0.0
    assert "Personal Trainer" in res["reply_message"]



def test_continuous_subscription_cycle_accounting():
    from gymos_core.subscription_lifecycle import SubscriptionLifecycleManager
    
    # Member plan expired on 2026-09-01
    # Member pays on 2026-09-06 (5 days delay after using 5 days of grace workouts)
    renewal_res = SubscriptionLifecycleManager.execute_settled_renewal(
        member_id="mem_test_accounting",
        plan_expiry_date="2026-09-01",
        plan_duration_days=30,
        payment_date="2026-09-06"
    )
    
    # Total plan is 30 days
    # 5 days grace consumed
    # New expiry date = 2026-09-01 + 30 days = 2026-10-01
    # Effective remaining days from Sep 6 = 25 days!
    assert renewal_res["days_grace_consumed"] == 5
    assert renewal_res["effective_days_remaining_from_today"] == 25
    assert renewal_res["new_membership_expiry_date"] == "2026-10-01"
    assert renewal_res["accounting_rule"] == "CONTINUOUS_CYCLE_ANCHORING"


def test_chat_at_risk_disengaged_capped_at_custom_policy_5_percent():
    from agent.policy_guardrails import PolicyGuardrailEngine
    at_risk_member = MemberProfile(
        member_id="mem_at_risk_5pct",
        name="Vikram Rao",
        phone="+919876543210",
        email="vikram@example.com",
        membership_tier=MembershipTier.QUARTERLY_PRO,
        membership_amount=6000.0,
        plan_start_date="2026-01-01",
        plan_expiry_date="2026-09-01",
        days_since_last_checkin=25,
        actual_visits_last_30_days=1  # Disengaged at risk
    )
    # Merchant sets max discount cap to 5.0%
    guardrail_5 = PolicyGuardrailEngine(max_discount_percentage=5.0)
    agent = ConversationalRecoveryAgent(guardrail_engine=guardrail_5)

    # General request: should NOT exceed 5%
    res = agent.handle_incoming_message(at_risk_member, "Any discount if I renew today?")
    assert res["intent"] == UserIntentType.REQUEST_DISCOUNT
    assert res["action_executed"]["discount_percent"] == 5.0
    assert "5%" in res["reply_message"]

    # Explicit 15% request: should clamp strictly to 5%
    res_clamped = agent.handle_incoming_message(at_risk_member, "Can I get 15% discount?")
    assert res_clamped["action_executed"]["discount_percent"] == 5.0
    assert res_clamped["action_executed"]["was_clamped_by_guardrail"] is True
    assert "5%" in res_clamped["reply_message"]

