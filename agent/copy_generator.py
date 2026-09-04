"""
Context-Aware Recovery Copy Generator for Plain English Communications.
"""
from typing import Dict, Any
from gymos_core.models import MemberProfile
from agent.diagnostician import RootCauseCategory


class RecoveryCopyGenerator:
    @staticmethod
    def generate_message(
        member: MemberProfile,
        root_cause: str,
        discount_percent: float,
        final_amount_inr: float,
        payment_url: str
    ) -> str:
        """
        Generates empathetic, context-aware recovery message in simple, polite English.
        """
        first_name = member.name.split()[0] if member.name else "Friend"

        if root_cause == RootCauseCategory.TECHNICAL_BANKING_FAILURE:
            return (
                f"Hi {first_name}! We noticed a temporary bank server timeout during your scheduled renewal. "
                f"Your gym access is safely reserved. You can complete your renewal smoothly via this link:\n"
                f"👉 {payment_url}\n"
                f"Amount: ₹{final_amount_inr:,.0f}"
            )

        elif root_cause == RootCauseCategory.SILENT_CHURN_DISENGAGEMENT:
            discount_text = f" To welcome you back, a {discount_percent:.0f}% special discount has been applied." if discount_percent > 0 else ""
            return (
                f"Hi {first_name}! We miss seeing you at IronPeak Gym. Your fitness journey matters to us!{discount_text} "
                f"You can restart your workouts easily using this link:\n"
                f"👉 {payment_url}\n"
                f"Special Offer: ₹{final_amount_inr:,.0f} (Valid for 48 hrs)"
            )

        elif root_cause == RootCauseCategory.INSUFFICIENT_FUNDS_TIMING:
            return (
                f"Hi {first_name}! A quick friendly reminder regarding your GymOS renewal. "
                f"You can complete your membership payment conveniently via this link:\n"
                f"👉 {payment_url}\n"
                f"Amount: ₹{final_amount_inr:,.0f}"
            )

        elif root_cause == RootCauseCategory.CARD_MANDATE_EXPIRED:
            return (
                f"Hello {first_name}! Your recurring autopay mandate has expired. "
                f"To maintain uninterrupted gym check-in access, please renew your plan here:\n"
                f"👉 {payment_url}\n"
                f"Amount: ₹{final_amount_inr:,.0f}"
            )

        # Default / Affordability
        return (
            f"Hi {first_name}! Here is your exclusive renewal offer for your GymOS membership. "
            f"Continue your workouts with one tap:\n"
            f"👉 {payment_url}\n"
            f"Total: ₹{final_amount_inr:,.0f}"
        )

