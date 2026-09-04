"""
Two-Way Interactive Conversational Recovery Agent.
Handles multi-turn objection negotiation over WhatsApp / SMS:
Travel/Injury Freeze, Price Downgrading, Salary Deferrals, and Razorpay Link Dispatch.
"""
from typing import Dict, Any, List, Optional
import json
import logging
import requests
from config.settings import settings
from gymos_core.models import MemberProfile
from gymos_core.subscription_lifecycle import SubscriptionLifecycleManager
from razorpay_client.client import RazorpayRecoveryClient

logger = logging.getLogger(__name__)


class UserIntentType:
    TRAVEL_OR_INJURY = "TRAVEL_OR_INJURY"
    PRICE_TOO_HIGH = "PRICE_TOO_HIGH"
    SALARY_DELAY_PROMISE = "SALARY_DELAY_PROMISE"
    REQUEST_DISCOUNT = "REQUEST_DISCOUNT"
    EXPLICIT_CANCELLATION = "EXPLICIT_CANCELLATION"
    ASK_PAYMENT_LINK = "ASK_PAYMENT_LINK"
    GENERAL_QUERY = "GENERAL_QUERY"


class ConversationalRecoveryAgent:
    def __init__(self, razorpay_client: Optional[RazorpayRecoveryClient] = None):
        self.rzp = razorpay_client or RazorpayRecoveryClient()
        self.lifecycle = SubscriptionLifecycleManager()
        self.openai_key = settings.OPENAI_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY

    def handle_incoming_message(
        self,
        member: MemberProfile,
        incoming_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Processes an incoming customer message, detects intent, executes bounded business actions,
        and returns an empathetic conversational reply with action metadata.
        """
        intent, extracted_data = self._classify_intent(incoming_message)
        logger.info("Conversational Agent classified intent=%s for member=%s", intent, member.member_id)

        reply_text = ""
        action_executed = {}
        payment_link = None

        if intent == UserIntentType.TRAVEL_OR_INJURY:
            freeze_days = extracted_data.get("days", 30)
            freeze_res = self.lifecycle.execute_freeze(member.member_id, freeze_days=freeze_days)
            action_executed = freeze_res
            reply_text = (
                f"No worries at all, {member.name.split()[0]}! Health & travel come first. 🧘‍♂️\n\n"
                f"Humne aapka GymOS membership & billing exactly **{freeze_days} dino ke liye freeze (pause)** kar diya hai "
                f"(Resume date: {freeze_res['resume_date']}). Zero cancellation charge!\n\n"
                f"Aapki membership **{freeze_res['resume_date']}** se seamless continue hogi bina kisi extra penalty ke. Get well soon / Safe travels! 🚀"
            )

        elif intent == UserIntentType.PRICE_TOO_HIGH:
            downgrade_res = self.lifecycle.execute_downgrade(
                member_id=member.member_id,
                from_tier=member.membership_tier.value,
                to_tier="MONTHLY_BASIC",
                new_amount=2499.0
            )
            # Generate fresh Razorpay link for the lower amount
            link_res = self.rzp.create_dynamic_payment_link(
                amount_inr=2499.0,
                member_name=member.name,
                member_phone=member.phone,
                member_email=member.email,
                description=f"GymOS Downgrade - Monthly Basic ({member.name})"
            )
            payment_link = link_res.get("short_url")
            display_link = link_res.get("display_url") or (payment_link if payment_link and payment_link.startswith("http") else f"https://rzp.io/i/{link_res.get('id', 'pay_now')}")
            action_executed = {**downgrade_res, "razorpay_link": payment_link, "display_url": display_link}
            reply_text = (
                f"Hum samajh sakte hain {member.name.split()[0]}. Fitness accessible honi chahiye!\n\n"
                f"Aap annual plan ki jagah hamare **Monthly Flexible Plan (₹2,499/mo)** par switch kar sakte hain. "
                f"No long-term lock-in!\n\n"
                f"👉 Instant Activation Link: {display_link}\n"
                f"Bina heavy commitment ke workout continue kijiye! 💪"
            )

        elif intent == UserIntentType.SALARY_DELAY_PROMISE:
            promised_date = extracted_data.get("date", "5th of the month")
            promise_res = self.lifecycle.execute_promise_to_pay(member.member_id, promised_date)
            action_executed = promise_res
            reply_text = (
                f"Bilkul {member.name.split()[0]} bhai! ✅ Humne aapka renewal date **{promised_date}** par defer kar diya hai.\n\n"
                f"Is beech aapka gym check-in access seamlessly active rahega. "
                f"Hum {promised_date} ko reminder bhejenge. Have a great workout today! 🏋️‍♂️"
            )

        elif intent == UserIntentType.REQUEST_DISCOUNT:
            # Maximum 15% discount bounded rule
            discount_pct = 15.0
            discounted_amt = round(member.membership_amount * (1.0 - (discount_pct / 100.0)), 2)
            link_res = self.rzp.create_dynamic_payment_link(
                amount_inr=discounted_amt,
                member_name=member.name,
                member_phone=member.phone,
                member_email=member.email,
                description=f"GymOS Exclusive Retention - {member.membership_tier.value}"
            )
            payment_link = link_res.get("short_url")
            mock_id = link_res.get("id", "plink_pay")
            display_link = link_res.get("display_url") or (payment_link if payment_link and payment_link.startswith("http") else f"https://rzp.io/i/{mock_id}")
            action_executed = {"action": "DISCOUNT_GRANTED", "discount_percent": discount_pct, "razorpay_link": payment_link, "display_url": display_link}
            display_amt_str = f"{discounted_amt:,.0f}" if discounted_amt.is_integer() or discounted_amt == int(discounted_amt) else f"{discounted_amt:,.2f}"
            reply_text = (
                f"Special loyalty member hone ke naate, humne aapke account par **{discount_pct:.0f}% direct discount** apply kiya hai! 🎉\n\n"
                f"Original: ₹{member.membership_amount:,.0f} ➔ **Special Price: ₹{display_amt_str}**\n"
                f"👉 Secure Razorpay Link: {display_link}\n"
                f"(Offer valid for next 24 hours only)"
            )

        elif intent == UserIntentType.EXPLICIT_CANCELLATION:
            action_executed = {"action": "CANCELLATION_RECORDED", "opt_out": True}
            reply_text = (
                f"We are sorry to see you go, {member.name.split()[0]}. 💔\n\n"
                f"Aapki membership cancel request accept ho gayi hai. Future communications stop kar diye gaye hain. "
                f"Whenever you're ready to restart your fitness journey, IronPeak Gym ke darwaaze hamesha khule hain! Wishing you the best!"
            )

        else:
            # General / Payment Link request
            link_res = self.rzp.create_dynamic_payment_link(
                amount_inr=member.membership_amount,
                member_name=member.name,
                member_phone=member.phone,
                member_email=member.email,
                description=f"GymOS Renewal - {member.membership_tier.value}"
            )
            payment_link = link_res.get("short_url")
            mock_id = link_res.get("id", "plink_pay")
            display_link = link_res.get("display_url") or (payment_link if payment_link and payment_link.startswith("http") else f"https://rzp.io/i/{mock_id}")
            action_executed = {"action": "STANDARD_LINK_DISPATCH", "razorpay_link": payment_link, "display_url": display_link}
            reply_text = (
                f"Hi {member.name.split()[0]}! Niche diye link par tap karke aap kisi bhi UPI app (GPay, PhonePe, Paytm) "
                f"ya Card se 1-click mein renew kar sakte hain:\n\n"
                f"👉 {display_link}\n"
                f"Amount: ₹{member.membership_amount:,.0f}"
            )

        return {
            "intent": intent,
            "member_id": member.member_id,
            "reply_message": reply_text,
            "payment_link": payment_link,
            "action_executed": action_executed
        }

    def _extract_freeze_days(self, text: str) -> int:
        import re
        t = text.lower()
        
        # 1. Matches weeks: "3 weeks", "2 week", "3 hafte", "2 hafto"
        week_match = re.search(r'(\d+)\s*(?:weeks?|hafte|hafta|hafto)', t)
        if week_match:
            return int(week_match.group(1)) * 7

        # 2. Matches months: "3 months", "1 month", "2 mahine", "1 mahina"
        month_match = re.search(r'(\d+)\s*(?:months?|mahine|mahina|maheene)', t)
        if month_match:
            return int(month_match.group(1)) * 30

        # 3. Matches days: "15 days", "10 day", "21 din", "45 dino"
        day_match = re.search(r'(\d+)\s*(?:days?|din|dino)', t)
        if day_match:
            return int(day_match.group(1))

        # 4. English / Hindi words
        if "one week" in t or "a week" in t or "1 week" in t or "ek hafta" in t:
            return 7
        if "two weeks" in t or "2 weeks" in t or "do hafte" in t:
            return 14
        if "three weeks" in t or "3 weeks" in t or "teen hafte" in t:
            return 21
        if "four weeks" in t or "4 weeks" in t or "char hafte" in t:
            return 28
        if "one month" in t or "a month" in t or "ek mahina" in t:
            return 30
        if "two months" in t or "2 months" in t or "do mahine" in t:
            return 60
        if "three months" in t or "3 months" in t or "teen mahine" in t:
            return 90

        # 5. Number after pause/freeze/travel (e.g., "pause for 10", "freeze 45")
        num_match = re.search(r'(?:pause|freeze|travel|traveling|holiday|bed rest|rest for|leave for)\s*(?:for\s*)?(\d+)', t)
        if num_match:
            return int(num_match.group(1))

        return 30

    def _extract_promise_date(self, text: str) -> str:
        import re
        t = text.lower()
        
        # Matches e.g. "25th", "10th", "5th", "1st", "15th", "20th"
        day_match = re.search(r'\b(\d{1,2}(?:st|nd|rd|th)?)\b', t)
        if day_match:
            return day_match.group(1)
            
        if "next week" in t or "agle hafte" in t:
            return "Next Monday"
        if "month end" in t or "month-end" in t or "mahine ke end" in t:
            return "End of the month"
            
        return "5th of the month"

    def _classify_intent(self, text: str) -> (str, Dict[str, Any]):
        t = text.lower()
        if any(w in t for w in ["injured", "injury", "fracture", "accident", "travel", "traveling", "trip", "out of station", "village", "pause", "freeze", "hometown"]):
            days = self._extract_freeze_days(text)
            return UserIntentType.TRAVEL_OR_INJURY, {"days": days}
        if any(w in t for w in ["expensive", "costly", "mehnga", "budget", "can't afford", "no money", "cheaper", "downgrade"]):
            return UserIntentType.PRICE_TOO_HIGH, {}
        if any(w in t for w in ["salary", "month end", "5th", "1st", "10th", "20th", "25th", "pay later", "next week", "paise aane do"]):
            date = self._extract_promise_date(text)
            return UserIntentType.SALARY_DELAY_PROMISE, {"date": date}
        if any(w in t for w in ["discount", "offer", "coupon", "kam karo", "best price"]):
            return UserIntentType.REQUEST_DISCOUNT, {}
        if any(w in t for w in ["cancel", "stop", "mat message karo", "band karo", "don't want", "left gym", "shifted"]):
            return UserIntentType.EXPLICIT_CANCELLATION, {}
        if any(w in t for w in ["link", "pay", "payment", "qr", "how to"]):
            return UserIntentType.ASK_PAYMENT_LINK, {}
        return UserIntentType.GENERAL_QUERY, {}
