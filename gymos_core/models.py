"""
GymOS Domain Data Models.
Reflects GymOS microservices (membership-service, attendance-service, payment-service).
"""
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MembershipTier(str, Enum):
    MONTHLY_BASIC = "MONTHLY_BASIC"
    QUARTERLY_PRO = "QUARTERLY_PRO"
    ANNUAL_ELITE = "ANNUAL_ELITE"
    CORPORATE_VIP = "CORPORATE_VIP"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class FailureReasonCode(str, Enum):
    BANK_SERVER_UNAVAILABLE = "BANK_SERVER_UNAVAILABLE"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    MANDATE_EXPIRED = "MANDATE_EXPIRED"
    CARD_DECLINED = "CARD_DECLINED"
    PAYMENT_TIMED_OUT = "PAYMENT_TIMED_OUT"
    USER_CANCELLED = "USER_CANCELLED"
    NONE = "NONE"


class MemberProfile(BaseModel):
    member_id: str
    tenant_id: str = "gym_ironpeak_001"
    name: str
    phone: str
    email: str
    language_preference: str = "hinglish"  # 'english' or 'hinglish'
    membership_tier: MembershipTier
    membership_amount: float
    plan_start_date: str
    plan_expiry_date: str
    
    # Behavioral Telemetry from GymOS attendance-service
    baseline_visits_per_week: float = 4.0
    actual_visits_last_30_days: int = 16
    days_since_last_checkin: int = 2
    
    # Financial Telemetry from GymOS payment-service
    lifetime_paid_inr: float = 18000.0
    previous_payment_method: str = "UPI_AUTOPAY"  # UPI_AUTOPAY, CARD, NACH, NETBANKING
    consecutive_failed_attempts: int = 0
    opted_out: bool = False
    
    # Churn / Risk Signals
    last_failure_code: FailureReasonCode = FailureReasonCode.NONE
    last_failure_timestamp: Optional[str] = None
    historical_discount_given: float = 0.0


class RecoveryIntervention(BaseModel):
    intervention_id: str
    member_id: str
    timestamp: str
    root_cause: str
    strategy_applied: str
    discount_percentage: float
    original_amount: float
    discounted_amount: float
    channel_used: str
    razorpay_payment_link: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    recovery_copy: str
    scheduled_retry_time: Optional[str] = None
    status: str = "DISPATCHED"  # DISPATCHED, RECOVERED, FAILED, ESCALATED, BLOCKED_BY_GUARDRAIL
    guardrail_passed: bool = True
    guardrail_reasons: List[str] = []
