"""
Central Action Orchestration Engine for AI Revenue Recovery.
Executes the closed loop: Ingest -> Diagnose -> Guardrail Verification -> Razorpay Action -> Audit.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from gymos_core.models import MemberProfile, RecoveryIntervention
from agent.diagnostician import RecoveryDiagnostician, RootCauseCategory
from agent.policy_guardrails import PolicyGuardrailEngine
from agent.copy_generator import RecoveryCopyGenerator
from agent.audit_logger import AuditLogger
from razorpay_client.client import RazorpayRecoveryClient

logger = logging.getLogger(__name__)


class RecoveryOrchestrator:
    def __init__(
        self,
        razorpay_client: Optional[RazorpayRecoveryClient] = None,
        audit_logger: Optional[AuditLogger] = None,
        guardrail_engine: Optional[PolicyGuardrailEngine] = None
    ):
        self.rzp = razorpay_client or RazorpayRecoveryClient()
        self.audit = audit_logger or AuditLogger()
        self.guardrails = guardrail_engine or PolicyGuardrailEngine()
        self.diagnostician = RecoveryDiagnostician()

    def process_recovery(
        self,
        member: MemberProfile,
        trigger_signal: str = "SCHEDULED_DUNNING_SCAN"
    ) -> RecoveryIntervention:
        """
        Executes end-to-end bounded revenue recovery workflow for a member.
        """
        intervention_id = f"intv_{uuid.uuid4().hex[:10]}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Step 1: Diagnose Root Cause
        diag = self.diagnostician.diagnose(member)
        root_cause = diag["root_cause"]

        # Step 2: Determine Candidate Strategy & Proposed Discount
        proposed_discount = 0.0
        preferred_channel = "whatsapp"
        strategy_name = "STANDARD_RETRY"

        if root_cause == RootCauseCategory.SILENT_CHURN_DISENGAGEMENT:
            proposed_discount = 10.0
            strategy_name = "REACTIVATION_CONCIERGE"
        elif root_cause == RootCauseCategory.AFFORDABILITY_PRICE_SENSITIVE:
            proposed_discount = 15.0
            strategy_name = "DOWNGRADE_OR_DISCOUNT"
        elif root_cause == RootCauseCategory.TECHNICAL_BANKING_FAILURE:
            proposed_discount = 0.0
            strategy_name = "SILENT_SMART_RETRY"
            preferred_channel = "silent_gateway_retry"
        elif root_cause == RootCauseCategory.INSUFFICIENT_FUNDS_TIMING:
            proposed_discount = 0.0
            strategy_name = "SALARY_WINDOW_RETRY"
        elif root_cause == RootCauseCategory.CARD_MANDATE_EXPIRED:
            proposed_discount = 0.0
            strategy_name = "PAYMENT_LINK_UPDATE"
        elif root_cause == RootCauseCategory.HIGH_VALUE_VIP_RISK:
            proposed_discount = 0.0
            strategy_name = "HUMAN_ESCALATION"
            preferred_channel = "manager_call_ticket"

        # Step 3: Run Deterministic Policy Guardrails
        is_allowed, authorized_discount, guardrail_notes, verdict = self.guardrails.evaluate_proposed_action(
            member=member,
            proposed_discount_percentage=proposed_discount,
            proposed_channel=preferred_channel
        )

        original_amount = member.membership_amount
        discounted_amount = original_amount * (1.0 - (authorized_discount / 100.0))

        # Step 4: Execute Bounded Actions
        razorpay_link = None
        razorpay_order_id = None
        recovery_copy = ""
        action_payload = {}
        status = "DISPATCHED"

        if not is_allowed:
            # Blocked by safety guardrails (e.g. opt-out or frequency cap)
            status = "BLOCKED_BY_GUARDRAIL"
            recovery_copy = "[WORKFLOW STOPPED] Automated communications suspended per policy."
            action_payload = {"action": "NONE", "verdict": verdict}
        elif verdict == "ESCALATE_TO_MANAGER":
            status = "ESCALATED"
            recovery_copy = f"[HIGH VALUE ALERT] Escalate VIP account ₹{original_amount:,.0f} for member {member.name} directly to General Manager."
            action_payload = {
                "action": "CREATE_CRM_TICKET",
                "assignee": "gym_general_manager",
                "priority": "P0_CRITICAL",
                "member_phone": member.phone
            }
        elif strategy_name == "SILENT_SMART_RETRY":
            # Gateway retry scheduling
            status = "SCHEDULED_RETRY"
            import time
            scheduled_epoch = int(time.time() + 14400)  # +4 hours
            retry_res = self.rzp.schedule_smart_retry(
                mandate_id=f"mandate_{member.member_id}",
                scheduled_epoch=scheduled_epoch,
                amount_inr=discounted_amount
            )
            action_payload = {"action": "RAZORPAY_SMART_RETRY", "result": retry_res}
            recovery_copy = f"[BACKEND ACTION] Silent gateway retry scheduled for {scheduled_epoch} without disturbing member."
        else:
            # Generate Razorpay Dynamic Payment Link
            link_res = self.rzp.create_dynamic_payment_link(
                amount_inr=discounted_amount,
                member_name=member.name,
                member_phone=member.phone,
                member_email=member.email,
                description=f"GymOS Renewal - {member.membership_tier.value} ({member.name})",
                notes={
                    "member_id": member.member_id,
                    "root_cause": root_cause,
                    "strategy": strategy_name,
                    "discount_applied": str(authorized_discount)
                }
            )
            razorpay_link = link_res.get("short_url")
            razorpay_order_id = link_res.get("id")

            # Generate Context-Aware Copy
            recovery_copy = RecoveryCopyGenerator.generate_message(
                member=member,
                root_cause=root_cause,
                discount_percent=authorized_discount,
                final_amount_inr=discounted_amount,
                payment_url=razorpay_link or "https://rzp.io/l/demo"
            )

            action_payload = {
                "action": "PAYMENT_LINK_DISPATCH",
                "razorpay_link_id": razorpay_order_id,
                "payment_url": razorpay_link,
                "channel": preferred_channel,
                "discount_percentage": authorized_discount
            }

        # Step 5: Record Immutable Audit Trail
        self.audit.record_decision(
            member_id=member.member_id,
            trigger_signal=trigger_signal,
            diagnostics=diag,
            guardrail_verdict=verdict,
            guardrail_notes=guardrail_notes,
            action_executed=action_payload,
            outcome_status=status
        )

        return RecoveryIntervention(
            intervention_id=intervention_id,
            member_id=member.member_id,
            timestamp=timestamp,
            root_cause=root_cause,
            strategy_applied=strategy_name,
            discount_percentage=authorized_discount,
            original_amount=original_amount,
            discounted_amount=discounted_amount,
            channel_used=preferred_channel,
            razorpay_payment_link=razorpay_link,
            razorpay_order_id=razorpay_order_id,
            recovery_copy=recovery_copy,
            status=status,
            guardrail_passed=is_allowed,
            guardrail_reasons=guardrail_notes
        )
