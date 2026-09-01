"""
Deterministic Policy & Financial Guardrails Engine.
Enforces merchant boundaries, statutory compliance, and hard stopping rules.
"""
from typing import Dict, Any, List, Tuple
import logging
from config.settings import settings
from gymos_core.models import MemberProfile

logger = logging.getLogger(__name__)


class PolicyGuardrailEngine:
    def __init__(
        self,
        max_discount_percentage: float = 15.0,
        max_touches: int = 3,
        strict_opt_out: bool = True,
        vip_threshold_inr: float = 50000.0
    ):
        self.max_discount = max_discount_percentage
        self.max_touches = max_touches
        self.strict_opt_out = strict_opt_out
        self.vip_threshold = vip_threshold_inr

    def evaluate_proposed_action(
        self,
        member: MemberProfile,
        proposed_discount_percentage: float,
        proposed_channel: str
    ) -> Tuple[bool, float, List[str], str]:
        """
        Validates the proposed recovery action against merchant financial rules.
        Returns:
            - is_allowed: bool
            - bounded_discount: float (adjusted if needed)
            - guardrail_notes: List[str]
            - execution_verdict: str ('APPROVED', 'CLAMPED', 'BLOCKED', 'ESCALATED')
        """
        notes = []

        # Rule 1: Compliance / Opt-Out Hard Stop
        if member.opted_out and self.strict_opt_out:
            notes.append("COMPLIANCE_HARD_STOP: Member explicitly opted out of automated communications.")
            logger.warning("Recovery blocked for member %s due to opt-out", member.member_id)
            return False, 0.0, notes, "BLOCKED_OPT_OUT"

        # Rule 2: Touch Frequency Limit
        if member.consecutive_failed_attempts >= self.max_touches:
            notes.append(f"FREQUENCY_LIMIT_EXCEEDED: Member reached max allowed touches ({self.max_touches}).")
            return False, 0.0, notes, "BLOCKED_MAX_TOUCHES"

        # Rule 3: High-Value VIP / Enterprise Escalation
        if member.membership_amount >= self.vip_threshold:
            notes.append(f"VIP_ESCALATION_TRIGGER: Membership amount (₹{member.membership_amount}) exceeds auto-recovery threshold.")
            return True, 0.0, notes, "ESCALATE_TO_MANAGER"

        # Rule 4: Discount Bounding & Margin Protection
        bounded_discount = proposed_discount_percentage
        verdict = "APPROVED"

        if proposed_discount_percentage > self.max_discount:
            bounded_discount = self.max_discount
            notes.append(f"DISCOUNT_CLAMPED: Proposed {proposed_discount_percentage}% clamped to max policy ceiling of {self.max_discount}%.")
            verdict = "CLAMPED"
        elif proposed_discount_percentage < 0.0:
            bounded_discount = 0.0

        if bounded_discount > 0.0:
            notes.append(f"DISCOUNT_AUTHORIZED: {bounded_discount}% retention discount approved under policy budget.")
        else:
            notes.append("ZERO_DISCOUNT_POLICY: Full price preservation maintained.")

        return True, bounded_discount, notes, verdict
