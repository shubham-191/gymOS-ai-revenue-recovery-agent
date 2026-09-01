"""
Context-Aware Recovery Copy Generator for English & Hinglish Communications.
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
        Generates empathetic, context-aware recovery message.
        """
        first_name = member.name.split()[0] if member.name else "Friend"
        is_hinglish = member.language_preference.lower() == "hinglish"

        if root_cause == RootCauseCategory.TECHNICAL_BANKING_FAILURE:
            if is_hinglish:
                return (
                    f"Hi {first_name}! 👋 GymOS se quick update. Lagta hai aapka auto-payment bank gateway "
                    f"timeout ki wajah se complete nahi ho paya. Humne aapka slot hold pe rakha hai. "
                    f"Aap directly is secure Razorpay link se bina kisi issue ke complete kar sakte hain:\n"
                    f"👉 {payment_url}\n"
                    f"Amount: ₹{final_amount_inr:.0f}"
                )
            else:
                return (
                    f"Hi {first_name}! We noticed a temporary bank gateway timeout during your scheduled renewal. "
                    f"Your GymOS workout access is safe. You can complete your renewal securely via this link:\n"
                    f"👉 {payment_url}\n"
                    f"Amount: ₹{final_amount_inr:.0f}"
                )

        elif root_cause == RootCauseCategory.SILENT_CHURN_DISENGAGEMENT:
            if is_hinglish:
                discount_text = f" Aur aapke dedicated return ke liye humne {discount_percent:.0f}% loyalty discount add kiya hai!" if discount_percent > 0 else ""
                return (
                    f"Arre {first_name} bhai! 💪 IronPeak Gym mein aapko miss kar rahe hain. "
                    f"Goals break nahi hone chahiye!{discount_text} "
                    f"Apna workout streak wapas start kijiye. Renewal link below:\n"
                    f"👉 {payment_url}\n"
                    f"Special Offer: ₹{final_amount_inr:.0f} (Valid for 48 hrs)"
                )
            else:
                discount_text = f" As a welcome-back incentive, a {discount_percent:.0f}% loyalty credit has been applied." if discount_percent > 0 else ""
                return (
                    f"Hi {first_name}! We miss seeing you at IronPeak Gym. Your fitness journey matters to us!{discount_text} "
                    f"Restart your workout access with a single tap:\n"
                    f"👉 {payment_url}\n"
                    f"Renew for: ₹{final_amount_inr:.0f}"
                )

        elif root_cause == RootCauseCategory.INSUFFICIENT_FUNDS_TIMING:
            if is_hinglish:
                return (
                    f"Hi {first_name}! 👋 GymOS reminder: Aapka gym renewal schedule pending hai. "
                    f"Agar salary credit window ke hisaab se pay karna chahein, toh aap is 1-click Razorpay link se "
                    f"apni convenience par pay kar sakte hain:\n"
                    f"👉 {payment_url}\n"
                    f"Amount: ₹{final_amount_inr:.0f}"
                )
            else:
                return (
                    f"Hi {first_name}! A quick reminder regarding your GymOS renewal. You can complete your membership "
                    f"conveniently via this direct Razorpay link:\n"
                    f"👉 {payment_url}\n"
                    f"Amount: ₹{final_amount_inr:.0f}"
                )

        elif root_cause == RootCauseCategory.CARD_MANDATE_EXPIRED:
            if is_hinglish:
                return (
                    f"Hello {first_name}! Aapka recurring autopay mandate expire ho chuka hai. "
                    f"Bina kisi workout interruption ke apna plan renew karne ke liye niche diye link par tap karein:\n"
                    f"👉 {payment_url}\n"
                    f"Amount: ₹{final_amount_inr:.0f}"
                )
            else:
                return (
                    f"Hello {first_name}! Your recurring autopay mandate requires re-authorization. "
                    f"Maintain uninterrupted gym access by renewing in 30 seconds:\n"
                    f"👉 {payment_url}\n"
                    f"Amount: ₹{final_amount_inr:.0f}"
                )

        # Default / Affordability
        if is_hinglish:
            return (
                f"Hi {first_name}! IronPeak Gym par aapka exclusive renewal offer active hai. "
                f"Special discounted price par access continue karein:\n"
                f"👉 {payment_url}\n"
                f"Special Price: ₹{final_amount_inr:.0f}"
            )
        return (
            f"Hi {first_name}! Exclusive renewal offer for your GymOS membership. "
            f"Continue your fitness journey with one click:\n"
            f"👉 {payment_url}\n"
            f"Total: ₹{final_amount_inr:.0f}"
        )
