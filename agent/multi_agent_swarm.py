"""
Multi-Agent Swarm & War Room Coordinator.
Executes an event-driven collaborative agent loop with 5 specialized sub-agents:
1. Telemetry Sentinel Agent
2. Forensic Diagnostic Agent
3. Risk & Compliance Auditor Agent (with Veto power)
4. Omnichannel Negotiator Agent
5. Settlement & Ledger Agent (Razorpay & SHA-256 Chaining)
"""
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from gymos_core.models import MemberProfile, RecoveryIntervention
from agent.diagnostician import RecoveryDiagnostician, RootCauseCategory
from agent.policy_guardrails import PolicyGuardrailEngine
from agent.copy_generator import RecoveryCopyGenerator
from agent.audit_logger import AuditLogger
from razorpay_client.client import RazorpayRecoveryClient
from razorpay_client.smart_optimizer import SmartPaymentRouter

logger = logging.getLogger(__name__)


class AgentRole(str):
    SENTINEL = "TELEMETRY_SENTINEL_AGENT"
    FORENSIC = "FORENSIC_DIAGNOSTIC_AGENT"
    AUDITOR = "RISK_AUDITOR_AGENT"
    NEGOTIATOR = "OMNICHANNEL_NEGOTIATOR_AGENT"
    SETTLEMENT = "SETTLEMENT_LEDGER_AGENT"


class SwarmAgentMessage(BaseModel):
    step_number: int
    agent_name: str
    agent_role: str
    status: str
    timestamp: str
    input_received: Dict[str, Any]
    output_produced: Dict[str, Any]
    reasoning_trace: str


class MultiAgentWarRoomCoordinator:
    def __init__(
        self,
        razorpay_client: Optional[RazorpayRecoveryClient] = None,
        audit_logger: Optional[AuditLogger] = None,
        guardrail_engine: Optional[PolicyGuardrailEngine] = None,
        smart_router: Optional[SmartPaymentRouter] = None
    ):
        self.rzp = razorpay_client or RazorpayRecoveryClient()
        self.audit = audit_logger or AuditLogger()
        self.guardrails = guardrail_engine or PolicyGuardrailEngine()
        self.diagnostician = RecoveryDiagnostician()
        self.router = smart_router or SmartPaymentRouter()

    def run_war_room_pipeline(self, member: MemberProfile, trigger_event: str = "SCHEDULED_TELEMETRY_SCAN") -> Dict[str, Any]:
        """
        Runs the 5-Agent Collaborative Pipeline and returns the execution trace for visualization.
        """
        war_room_id = f"swarm_{uuid.uuid4().hex[:10]}"
        steps: List[SwarmAgentMessage] = []

        # =========================================================================
        # AGENT 1: Telemetry Sentinel Agent
        # Ingests physical check-in velocity and payment failure status
        # =========================================================================
        expected_monthly = member.baseline_visits_per_week * 4
        attendance_drop_pct = round(max(0.0, 1.0 - (member.actual_visits_last_30_days / (expected_monthly or 1.0))) * 100.0, 1)
        
        sentinel_output = {
            "member_id": member.member_id,
            "plan_tier": member.membership_tier.value,
            "amount_inr": member.membership_amount,
            "days_inactive": member.days_since_last_checkin,
            "attendance_drop_percentage": attendance_drop_pct,
            "failure_code": member.last_failure_code.value,
            "consecutive_failures": member.consecutive_failed_attempts,
            "opted_out": member.opted_out
        }
        sentinel_msg = SwarmAgentMessage(
            step_number=1,
            agent_name="Agent Sentinel-01",
            agent_role=AgentRole.SENTINEL,
            status="COMPLETED",
            timestamp=datetime.utcnow().isoformat() + "Z",
            input_received={"trigger_event": trigger_event, "member_id": member.member_id},
            output_produced=sentinel_output,
            reasoning_trace=f"Ingested physical check-in telemetry: Member attended {member.actual_visits_last_30_days} sessions in 30 days ({attendance_drop_pct}% drop velocity). Payment status: {member.last_failure_code.value}."
        )
        steps.append(sentinel_msg)

        # =========================================================================
        # AGENT 2: Forensic Diagnostic Agent
        # Performs root-cause analysis with LLM reasoning & confidence scoring
        # =========================================================================
        diag_res = self.diagnostician.diagnose(member)
        forensic_msg = SwarmAgentMessage(
            step_number=2,
            agent_name="Agent Forensic-02",
            agent_role=AgentRole.FORENSIC,
            status="COMPLETED",
            timestamp=datetime.utcnow().isoformat() + "Z",
            input_received=sentinel_output,
            output_produced=diag_res,
            reasoning_trace=diag_res["reasoning"]
        )
        steps.append(forensic_msg)

        root_cause = diag_res["root_cause"]
        proposed_discount = 10.0 if root_cause == RootCauseCategory.SILENT_CHURN_DISENGAGEMENT else (15.0 if root_cause == RootCauseCategory.AFFORDABILITY_PRICE_SENSITIVE else 0.0)

        # =========================================================================
        # AGENT 3: Risk & Compliance Auditor Agent (Veto Authority)
        # Formally verifies regulatory compliance, cooldowns, and margin limits
        # =========================================================================
        is_allowed, authorized_discount, guardrail_notes, verdict = self.guardrails.evaluate_proposed_action(
            member=member,
            proposed_discount_percentage=proposed_discount,
            proposed_channel="whatsapp"
        )
        auditor_output = {
            "is_authorized": is_allowed,
            "verdict": verdict,
            "authorized_discount_pct": authorized_discount,
            "compliance_notes": guardrail_notes,
            "veto_triggered": not is_allowed
        }
        auditor_msg = SwarmAgentMessage(
            step_number=3,
            agent_name="Agent Auditor-03",
            agent_role=AgentRole.AUDITOR,
            status="VETOED" if not is_allowed else "AUTHORIZED",
            timestamp=datetime.utcnow().isoformat() + "Z",
            input_received={"proposed_discount": proposed_discount, "opted_out": member.opted_out},
            output_produced=auditor_output,
            reasoning_trace=f"Auditor evaluated policy rules. Verdict: {verdict}. Authorized discount: {authorized_discount}%. Violations: {0 if is_allowed else 1}."
        )
        steps.append(auditor_msg)

        # If Vetoed by Auditor, stop swarm here
        if not is_allowed:
            return {
                "war_room_id": war_room_id,
                "status": "STOPPED_BY_AUDITOR",
                "final_verdict": verdict,
                "steps": [s.model_dump() for s in steps]
            }

        # =========================================================================
        # AGENT 4: Omnichannel Negotiator Agent
        # Formulates contextual communication in English/Hinglish
        # =========================================================================
        discounted_amount = member.membership_amount * (1.0 - (authorized_discount / 100.0))
        negotiator_copy = RecoveryCopyGenerator.generate_message(
            member=member,
            root_cause=root_cause,
            discount_percent=authorized_discount,
            final_amount_inr=discounted_amount,
            payment_url="https://rzp.io/l/pending-dispatch"
        )
        negotiator_msg = SwarmAgentMessage(
            step_number=4,
            agent_name="Agent Negotiator-04",
            agent_role=AgentRole.NEGOTIATOR,
            status="COMPLETED",
            timestamp=datetime.utcnow().isoformat() + "Z",
            input_received={"authorized_discount": authorized_discount, "language": member.language_preference},
            output_produced={"final_amount_inr": discounted_amount, "copy_preview": negotiator_copy[:120] + "..."},
            reasoning_trace=f"Synthesized empathetic {member.language_preference} copy tailored to {root_cause} with authorized {authorized_discount}% discount."
        )
        steps.append(negotiator_msg)

        # =========================================================================
        # AGENT 5: Settlement & Ledger Agent
        # Routes through Smart Optimizer, calls Razorpay APIs, & signs SHA-256 block
        # =========================================================================
        routing_decision = self.router.route_transaction(discounted_amount)
        
        link_res = self.rzp.create_dynamic_payment_link(
            amount_inr=discounted_amount,
            member_name=member.name,
            member_phone=member.phone,
            member_email=member.email,
            description=f"GymOS Swarm Renewal - {member.membership_tier.value} ({member.name})"
        )
        final_link = link_res.get("short_url")

        # Record Audit entry
        audit_entry = self.audit.record_decision(
            member_id=member.member_id,
            trigger_signal=f"SWARM_WAR_ROOM_{war_room_id}",
            diagnostics=diag_res,
            guardrail_verdict=verdict,
            guardrail_notes=guardrail_notes,
            action_executed={
                "routing": routing_decision,
                "razorpay_link": final_link,
                "discount_applied": authorized_discount
            },
            outcome_status="DISPATCHED"
        )

        settlement_msg = SwarmAgentMessage(
            step_number=5,
            agent_name="Agent Settlement-05",
            agent_role=AgentRole.SETTLEMENT,
            status="DISPATCHED_AND_LOGGED",
            timestamp=datetime.utcnow().isoformat() + "Z",
            input_received={"amount": discounted_amount, "routing": routing_decision},
            output_produced={
                "razorpay_payment_link": final_link,
                "gateway_used": routing_decision["gateway_name"],
                "failover_active": routing_decision["failover_triggered"],
                "sha256_audit_hash": audit_entry["entry_hash"]
            },
            reasoning_trace=f"Routed ₹{discounted_amount:,.2f} via {routing_decision['gateway_name']}. Generated Razorpay Link {final_link}. Cryptographic block signed: {audit_entry['entry_hash'][:16]}..."
        )
        steps.append(settlement_msg)

        return {
            "war_room_id": war_room_id,
            "status": "SUCCESSFULLY_ORCHESTRATED",
            "final_verdict": verdict,
            "payment_link": final_link,
            "discount_applied_pct": authorized_discount,
            "final_amount_inr": discounted_amount,
            "gateway_rail": routing_decision["gateway_name"],
            "sha256_audit_hash": audit_entry["entry_hash"],
            "steps": [s.model_dump() for s in steps]
        }
