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
    assert "21 dino ke liye freeze" in res["reply_message"]

    res_10 = chat_agent.handle_incoming_message(sample_member, "Going on a family trip for 10 days, please pause.")
    assert res_10["action_executed"]["freeze_duration_days"] == 10
    assert "10 dino ke liye freeze" in res_10["reply_message"]


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
