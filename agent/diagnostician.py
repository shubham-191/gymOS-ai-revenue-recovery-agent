"""
Multi-Signal Root-Cause Diagnostician.
Categorizes revenue risks by fusing behavioral telemetry (attendance)
and payment failure signals.
"""
from typing import Dict, Any, Tuple
import logging
from gymos_core.models import MemberProfile, FailureReasonCode

logger = logging.getLogger(__name__)


class RootCauseCategory:
    TECHNICAL_BANKING_FAILURE = "TECHNICAL_BANKING_FAILURE"
    INSUFFICIENT_FUNDS_TIMING = "INSUFFICIENT_FUNDS_TIMING"
    SILENT_CHURN_DISENGAGEMENT = "SILENT_CHURN_DISENGAGEMENT"
    CARD_MANDATE_EXPIRED = "CARD_MANDATE_EXPIRED"
    AFFORDABILITY_PRICE_SENSITIVE = "AFFORDABILITY_PRICE_SENSITIVE"
    HIGH_VALUE_VIP_RISK = "HIGH_VALUE_VIP_RISK"
    UNKNOWN = "UNKNOWN"


class RecoveryDiagnostician:
    def __init__(self, provider: str = "mock_heuristic"):
        self.provider = provider

    def diagnose(self, member: MemberProfile) -> Dict[str, Any]:
        """
        Analyzes member telemetry to determine root-cause and confidence score.
        """
        # VIP / Corporate High-Value Check
        if member.membership_amount >= 50000.0:
            return {
                "root_cause": RootCauseCategory.HIGH_VALUE_VIP_RISK,
                "confidence": 0.98,
                "reasoning": f"High value enterprise/annual membership (₹{member.membership_amount}). Requires high-touch manager escalation to prevent high GMV loss.",
                "signals_matched": ["high_gmv_threshold", "tier_" + member.membership_tier.value]
            }

        # Check for technical bank rail errors
        if member.last_failure_code in [FailureReasonCode.BANK_SERVER_UNAVAILABLE, FailureReasonCode.PAYMENT_TIMED_OUT]:
            return {
                "root_cause": RootCauseCategory.TECHNICAL_BANKING_FAILURE,
                "confidence": 0.94,
                "reasoning": "Payment failed due to upstream bank gateway timeout or NPCI/UPI server downtime. User has good attendance and active intent.",
                "signals_matched": ["failure_code_" + member.last_failure_code.value, "recent_active_attendance"]
            }

        # Check for expired mandate / card decline
        if member.last_failure_code in [FailureReasonCode.MANDATE_EXPIRED, FailureReasonCode.CARD_DECLINED]:
            return {
                "root_cause": RootCauseCategory.CARD_MANDATE_EXPIRED,
                "confidence": 0.92,
                "reasoning": "Recurring mandate token expired or card was replaced. Member needs an instant one-click Razorpay payment link to renew mandate.",
                "signals_matched": ["mandate_invalidation", "recurring_autopay_method"]
            }

        # Check for disengagement & silent churn (Attendance dropped significantly)
        attendance_drop_ratio = 0.0
        if member.baseline_visits_per_week > 0:
            expected_monthly = member.baseline_visits_per_week * 4
            attendance_drop_ratio = max(0.0, 1.0 - (member.actual_visits_last_30_days / expected_monthly))

        if member.days_since_last_checkin >= 12 or attendance_drop_ratio >= 0.65:
            return {
                "root_cause": RootCauseCategory.SILENT_CHURN_DISENGAGEMENT,
                "confidence": 0.89,
                "reasoning": f"Member attendance dropped by {attendance_drop_ratio*100:.1f}% (last visit was {member.days_since_last_checkin} days ago). Disengagement is the primary churn driver.",
                "signals_matched": [f"days_inactive_{member.days_since_last_checkin}", f"attendance_drop_{attendance_drop_ratio:.2f}"]
            }

        # Check for insufficient balance / salary timing
        if member.last_failure_code == FailureReasonCode.INSUFFICIENT_FUNDS:
            return {
                "root_cause": RootCauseCategory.INSUFFICIENT_FUNDS_TIMING,
                "confidence": 0.91,
                "reasoning": "Failure due to temporary balance insufficiency. Recommend alignment with upcoming salary window without eroding price with discounts.",
                "signals_matched": ["insufficient_funds_code", "active_attendance_history"]
            }

        # Default / Affordability sensitivity
        return {
            "root_cause": RootCauseCategory.AFFORDABILITY_PRICE_SENSITIVE,
            "confidence": 0.75,
            "reasoning": "General payment abandonment or renewal hesitation. Member is price-sensitive; targeted bounded incentive recommended.",
            "signals_matched": ["unspecified_failure_pattern"]
        }
