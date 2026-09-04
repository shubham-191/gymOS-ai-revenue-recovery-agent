import json
import logging
from typing import Dict, Any, Tuple, Optional
import requests
from config.settings import settings
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
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.LLM_PROVIDER
        self.openai_key = settings.OPENAI_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY

    def diagnose(self, member: MemberProfile) -> Dict[str, Any]:
        """
        Analyzes member telemetry to determine root-cause and confidence score.
        Uses OpenAI / Gemini if configured, otherwise calibrated heuristic engine.
        """
        # Try Live LLM if API Key is configured
        if self.openai_key and len(self.openai_key) > 10:
            llm_res = self._call_openai_diagnostics(member)
            if llm_res:
                return llm_res
        elif self.gemini_key and len(self.gemini_key) > 10:
            llm_res = self._call_gemini_diagnostics(member)
            if llm_res:
                return llm_res

        return self._heuristic_diagnose(member)

    def _call_openai_diagnostics(self, member: MemberProfile) -> Optional[Dict[str, Any]]:
        try:
            prompt = f"""You are an AI Revenue Recovery Diagnostician for GymOS.
Analyze this gym member's telemetry and diagnose the root cause of revenue risk:
Member: {member.name}
Plan: {member.membership_tier.value} (₹{member.membership_amount})
Attendance: {member.actual_visits_last_30_days} visits in last 30 days (Days since last checkin: {member.days_since_last_checkin})
Failure Code: {member.last_failure_code.value}
Consecutive Fails: {member.consecutive_failed_attempts}
Opted Out: {member.opted_out}

Categorize into exactly one of: [TECHNICAL_BANKING_FAILURE, INSUFFICIENT_FUNDS_TIMING, SILENT_CHURN_DISENGAGEMENT, CARD_MANDATE_EXPIRED, AFFORDABILITY_PRICE_SENSITIVE, HIGH_VALUE_VIP_RISK].
Domain Rule: If member's mandate expired or card declined, but they haven't visited in >10 days or have very low 30-day visits (<4), classify as SILENT_CHURN_DISENGAGEMENT because they are likely letting autopay lapse to quit/churn.
Respond in JSON format with keys: "root_cause", "confidence" (0.0 to 1.0), "reasoning", "signals_matched" (list of strings)."""

            res = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                },
                timeout=5
            )
            if res.status_code == 200:
                data = res.json()["choices"][0]["message"]["content"]
                return json.loads(data)
        except Exception as e:
            logger.warning("OpenAI diagnostic call failed (%s). Falling back to heuristic.", e)
        return None

    def _call_gemini_diagnostics(self, member: MemberProfile) -> Optional[Dict[str, Any]]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
            prompt = f"""You are an AI Revenue Recovery Diagnostician for GymOS.
Analyze member telemetry and output JSON:
Member: {member.name}, Tier: {member.membership_tier.value} (₹{member.membership_amount}), Visits: {member.actual_visits_last_30_days}/30d, Days Inactive: {member.days_since_last_checkin}, Failure: {member.last_failure_code.value}.
Output JSON format: {{"root_cause": "...", "confidence": 0.9, "reasoning": "...", "signals_matched": []}}"""
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=5)
            if res.status_code == 200:
                text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                # Clean potential markdown backticks
                cleaned = text.replace("```json", "").replace("```", "").strip()
                return json.loads(cleaned)
        except Exception as e:
            logger.warning("Gemini diagnostic call failed (%s). Falling back to heuristic.", e)
        return None

    def _heuristic_diagnose(self, member: MemberProfile) -> Dict[str, Any]:
        # Step 1: VIP / Corporate High-Value Check
        if member.membership_amount >= 50000.0:
            return {
                "root_cause": RootCauseCategory.HIGH_VALUE_VIP_RISK,
                "confidence": 0.98,
                "reasoning": f"High value enterprise/annual membership (₹{member.membership_amount}). Requires high-touch manager escalation to prevent high GMV loss.",
                "signals_matched": ["high_gmv_threshold", "tier_" + member.membership_tier.value]
            }

        # Step 2: Physical Disengagement & Silent Churn Velocity Analysis
        # If member has been inactive for many days or has very low recent attendance,
        # they are at critical risk of silent churn/quitting (even if the technical signal was mandate expiry/card decline).
        attendance_drop_ratio = 0.0
        if member.baseline_visits_per_week > 0:
            expected_monthly = member.baseline_visits_per_week * 4
            attendance_drop_ratio = max(0.0, 1.0 - (member.actual_visits_last_30_days / expected_monthly))

        is_disengaged = (
            member.days_since_last_checkin >= 12
            or attendance_drop_ratio >= 0.65
            or (member.actual_visits_last_30_days <= 3 and member.days_since_last_checkin >= 7)
        )

        if is_disengaged:
            mandate_context = ""
            if member.last_failure_code in [FailureReasonCode.MANDATE_EXPIRED, FailureReasonCode.CARD_DECLINED]:
                mandate_context = f" Mandate expired/card declined ({member.last_failure_code.value}), suggesting member may be passively letting autopay lapse to quit."

            return {
                "root_cause": RootCauseCategory.SILENT_CHURN_DISENGAGEMENT,
                "confidence": 0.93 if mandate_context else 0.89,
                "reasoning": (
                    f"Member attendance dropped by {attendance_drop_ratio*100:.1f}% "
                    f"(last visit was {member.days_since_last_checkin} days ago, only {member.actual_visits_last_30_days} visits in 30d)."
                    f"{mandate_context} Disengagement is the primary churn driver; winback reactivation discount and link recommended."
                ),
                "signals_matched": [
                    f"days_inactive_{member.days_since_last_checkin}",
                    f"actual_visits_{member.actual_visits_last_30_days}",
                    f"attendance_drop_{attendance_drop_ratio:.2f}"
                ] + ([f"lapsed_mandate_{member.last_failure_code.value}"] if mandate_context else [])
            }

        # Step 3: Technical Bank Rail Outages (for active members)
        if member.last_failure_code in [FailureReasonCode.BANK_SERVER_UNAVAILABLE, FailureReasonCode.PAYMENT_TIMED_OUT]:
            return {
                "root_cause": RootCauseCategory.TECHNICAL_BANKING_FAILURE,
                "confidence": 0.94,
                "reasoning": "Payment failed due to upstream bank gateway timeout or NPCI/UPI server downtime. User has good attendance and active intent.",
                "signals_matched": ["failure_code_" + member.last_failure_code.value, "recent_active_attendance"]
            }

        # Step 4: Active Member Expired Mandate / Card Replaced
        if member.last_failure_code in [FailureReasonCode.MANDATE_EXPIRED, FailureReasonCode.CARD_DECLINED]:
            return {
                "root_cause": RootCauseCategory.CARD_MANDATE_EXPIRED,
                "confidence": 0.92,
                "reasoning": f"Recurring mandate token expired or card was replaced. Member is actively attending ({member.actual_visits_last_30_days} visits in 30d, last check-in {member.days_since_last_checkin}d ago); seamless 1-click Razorpay payment link dispatched without unneeded discounts.",
                "signals_matched": ["mandate_invalidation", "active_attendance", "recurring_autopay_method"]
            }

        # Step 5: Insufficient Funds / Salary Timing
        if member.last_failure_code == FailureReasonCode.INSUFFICIENT_FUNDS:
            return {
                "root_cause": RootCauseCategory.INSUFFICIENT_FUNDS_TIMING,
                "confidence": 0.91,
                "reasoning": "Failure due to temporary balance insufficiency. Recommend alignment with upcoming salary window without eroding price with discounts.",
                "signals_matched": ["insufficient_funds_code", "active_attendance_history"]
            }

        # Step 6: Default / Price Sensitivity
        return {
            "root_cause": RootCauseCategory.AFFORDABILITY_PRICE_SENSITIVE,
            "confidence": 0.75,
            "reasoning": "General payment abandonment or renewal hesitation. Member is price-sensitive; targeted bounded incentive recommended.",
            "signals_matched": ["unspecified_failure_pattern"]
        }
