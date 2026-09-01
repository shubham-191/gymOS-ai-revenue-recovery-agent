"""
GymOS Subscription Lifecycle & Plan Elasticity Engine.
Manages flexible alternatives to churn: Pause/Freeze, Plan Downgrades,
and Promise-to-Pay deferrals.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class LifecycleActionType(str, Enum):
    FREEZE_MEMBERSHIP = "FREEZE_MEMBERSHIP"
    DOWNGRADE_PLAN = "DOWNGRADE_PLAN"
    PROMISE_TO_PAY = "PROMISE_TO_PAY"
    CONVERT_TO_CREDIT_WALLET = "CONVERT_TO_CREDIT_WALLET"
    CANCEL_GRACEFUL = "CANCEL_GRACEFUL"


class SubscriptionLifecycleManager:
    @staticmethod
    def execute_freeze(member_id: str, freeze_days: int = 30) -> Dict[str, Any]:
        resume_date = (datetime.utcnow() + timedelta(days=freeze_days)).strftime("%Y-%m-%d")
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
