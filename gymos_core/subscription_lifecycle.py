"""
GymOS Subscription Lifecycle & Plan Elasticity Engine.
Manages flexible alternatives to churn: Pause/Freeze, Plan Downgrades,
and Promise-to-Pay deferrals.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


class LifecycleActionType(str, Enum):
    FREEZE_MEMBERSHIP = "FREEZE_MEMBERSHIP"
    DOWNGRADE_PLAN = "DOWNGRADE_PLAN"
    PROMISE_TO_PAY = "PROMISE_TO_PAY"
    CONVERT_TO_CREDIT_WALLET = "CONVERT_TO_CREDIT_WALLET"
    CANCEL_GRACEFUL = "CANCEL_GRACEFUL"


class SubscriptionLifecycleManager:
    @staticmethod
    def execute_freeze(member_id: str, freeze_days: int = 30) -> Dict[str, Any]:
        resume_date = (datetime.now(IST) + timedelta(days=freeze_days)).strftime("%Y-%m-%d")
        logger.info("Executed subscription freeze for %s until %s", member_id, resume_date)
        return {
            "action": LifecycleActionType.FREEZE_MEMBERSHIP,
            "member_id": member_id,
            "freeze_duration_days": freeze_days,
            "resume_date": resume_date,
            "billing_status": "PAUSED_NO_FEE",
            "message": f"Your gym access and billing are frozen for {freeze_days} days until {resume_date}. Zero cancellation fee applied."
        }

    @staticmethod
    def execute_downgrade(member_id: str, from_tier: str, to_tier: str = "MONTHLY_BASIC", new_amount: float = 2499.0) -> Dict[str, Any]:
        logger.info("Executed plan downgrade for %s from %s to %s (₹%s)", member_id, from_tier, to_tier, new_amount)
        return {
            "action": LifecycleActionType.DOWNGRADE_PLAN,
            "member_id": member_id,
            "previous_tier": from_tier,
            "new_tier": to_tier,
            "new_amount_inr": new_amount,
            "savings_for_user": "Lower monthly commitment",
            "message": f"Successfully switched your plan to {to_tier} at ₹{new_amount:,.0f}/month."
        }

    @staticmethod
    def execute_promise_to_pay(member_id: str, promised_date: str) -> Dict[str, Any]:
        logger.info("Recorded promise-to-pay for %s on %s", member_id, promised_date)
        return {
            "action": LifecycleActionType.PROMISE_TO_PAY,
            "member_id": member_id,
            "promised_payment_date": promised_date,
            "grace_period_active": True,
            "message": f"Payment deferred to {promised_date}. Workout access remains active in grace period."
        }

    @staticmethod
    def execute_settled_renewal(
        member_id: str,
        plan_expiry_date: str,
        plan_duration_days: int = 30,
        payment_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Continuous Subscription Cycle Accounting:
        If a payment is delayed by X days (e.g. 5 days grace period used by the member),
        the new plan expiry date anchors to the previous expiry date:
        New Expiry Date = Previous Expiry Date + Plan Duration Days.
        
        This ensures that:
        - 5 days consumed during grace period are accounted for.
        - Effective days remaining from the payment date = Plan Duration - Days Delayed = 30 - 5 = 25 days.
        - The gym gets paid for all 30 days without giving 5 days of free workouts!
        """
        now_ist = datetime.now(IST)
        pay_dt = datetime.strptime(payment_date, "%Y-%m-%d").replace(tzinfo=IST) if payment_date else now_ist
        
        try:
            prev_expiry_dt = datetime.strptime(plan_expiry_date, "%Y-%m-%d").replace(tzinfo=IST)
        except Exception:
            prev_expiry_dt = now_ist

        # Calculate days delayed
        days_delayed = max(0, (pay_dt.date() - prev_expiry_dt.date()).days)
        
        # Anchor to previous expiry date
        new_expiry_dt = prev_expiry_dt + timedelta(days=plan_duration_days)
        
        # If payment was delayed longer than the entire plan duration (e.g. 40 days overdue), reset from payment date
        if new_expiry_dt.date() <= pay_dt.date():
            new_expiry_dt = pay_dt + timedelta(days=plan_duration_days)
            effective_days_remaining = plan_duration_days
        else:
            effective_days_remaining = (new_expiry_dt.date() - pay_dt.date()).days

        new_expiry_str = new_expiry_dt.strftime("%Y-%m-%d")
        
        logger.info(
            "Settled renewal for %s: PrevExpiry=%s, PayDate=%s, DaysGraceUsed=%d, RemainingDays=%d, NewExpiry=%s",
            member_id, plan_expiry_date, pay_dt.strftime("%Y-%m-%d"), days_delayed, effective_days_remaining, new_expiry_str
        )
        
        return {
            "action": "SETTLED_RENEWAL_CYCLE",
            "member_id": member_id,
            "previous_expiry_date": plan_expiry_date,
            "payment_settled_date": pay_dt.strftime("%Y-%m-%d"),
            "days_grace_consumed": days_delayed,
            "total_plan_duration_days": plan_duration_days,
            "effective_days_remaining_from_today": effective_days_remaining,
            "new_membership_expiry_date": new_expiry_str,
            "accounting_rule": "CONTINUOUS_CYCLE_ANCHORING",
            "message": f"Membership renewed until {new_expiry_str}. ({days_delayed} days grace period consumed, {effective_days_remaining} days remaining in this billing cycle)."
        }
