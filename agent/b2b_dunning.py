"""
B2B Corporate Accounts Receivable (AR) & Invoice Dunning Engine.
Manages multi-stage corporate invoice dunning, aging analysis,
and automated access suspension workflows.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from razorpay_client.client import RazorpayRecoveryClient

logger = logging.getLogger(__name__)


class CorporateInvoice(BaseModel):
    invoice_id: str
    company_name: str
    contact_person: str
    contact_email: str
    contact_phone: str
    employee_seat_count: int
    invoice_amount_inr: float
    invoice_date: str
    due_date: str
    days_overdue: int
    status: str = "OVERDUE"  # PAID, OVERDUE, CRITICAL, SUSPENDED


class B2BAccountsReceivableEngine:
    def __init__(self, razorpay_client: Optional[RazorpayRecoveryClient] = None):
        self.rzp = razorpay_client or RazorpayRecoveryClient()

    @staticmethod
    def get_sample_corporate_invoices() -> List[CorporateInvoice]:
        return [
            CorporateInvoice(
                invoice_id="INV-CORP-901",
                company_name="Zepto Tech Hub",
                contact_person="Kavita Reddy (HR Ops)",
                contact_email="kavita@zepto.example.com",
                contact_phone="+919876541100",
                employee_seat_count=45,
                invoice_amount_inr=112500.0,
                invoice_date="2026-07-15",
                due_date="2026-08-15",
                days_overdue=18,
                status="OVERDUE"
            ),
            CorporateInvoice(
                invoice_id="INV-CORP-902",
                company_name="Groww Financial Corp",
                contact_person="Rohan Mehta (Finance AP)",
                contact_email="ap@groww.example.com",
                contact_phone="+919876541101",
                employee_seat_count=120,
                invoice_amount_inr=360000.0,
                invoice_date="2026-06-30",
                due_date="2026-07-30",
                days_overdue=34,
                status="CRITICAL"
            ),
            CorporateInvoice(
                invoice_id="INV-CORP-903",
                company_name="Swiggy Delivery HQ",
                contact_person="Ankit Sharma (Admin)",
                contact_email="admin@swiggy.example.com",
                contact_phone="+919876541102",
                employee_seat_count=200,
                invoice_amount_inr=500000.0,
                invoice_date="2026-05-30",
                due_date="2026-06-30",
                days_overdue=64,
                status="SUSPENDED"
            ),
        ]

    def evaluate_corporate_dunning(self, invoice: CorporateInvoice) -> Dict[str, Any]:
        """
        Determines appropriate B2B dunning escalation stage based on aging days.
        """
        # Create or fetch dynamic Razorpay payment link
        link_res = self.rzp.create_dynamic_payment_link(
            amount_inr=invoice.invoice_amount_inr,
            member_name=f"{invoice.company_name} ({invoice.contact_person})",
            member_phone=invoice.contact_phone,
            member_email=invoice.contact_email,
            description=f"Corporate Gym Plan - {invoice.invoice_id} ({invoice.employee_seat_count} seats)"
        )
        payment_url = link_res.get("short_url")

        if invoice.days_overdue >= 60:
            stage = "STAGE_4_ACCESS_LOCK"
            action = "LOCK_CORPORATE_BIOMETRICS"
            dunning_copy = (
                f"🚨 **CRITICAL: CORPORATE ACCESS SUSPENSION NOTICE**\n\n"
                f"Dear {invoice.contact_person} ({invoice.company_name}),\n"
                f"Invoice #{invoice.invoice_id} for ₹{invoice.invoice_amount_inr:,.2f} is now **{invoice.days_overdue} days overdue**.\n\n"
                f"Per company policy, gym biometric access for your **{invoice.employee_seat_count} employees** has been temporarily frozen. "
                f"Instant restoration is enabled upon payment completion below:\n"
                f"👉 Instant Settlement Portal: {payment_url}\n"
                f"Escalated to: Accounts Receivable Legal & CFO"
            )
        elif invoice.days_overdue >= 30:
            stage = "STAGE_3_PRE_SUSPENSION"
            action = "NOTIFY_FINANCE_DIRECTOR"
            dunning_copy = (
                f"⚠️ **URGENT: PRE-SUSPENSION WARNING - INVOICE #{invoice.invoice_id}**\n\n"
                f"Dear {invoice.contact_person} ({invoice.company_name}),\n"
                f"Your corporate wellness invoice of ₹{invoice.invoice_amount_inr:,.2f} is **{invoice.days_overdue} days overdue**.\n\n"
                f"Please process the payment within 48 hours to prevent interruption to your {invoice.employee_seat_count} employees' gym memberships.\n"
                f"👉 Direct Razorpay B2B Portal: {payment_url}"
            )
        else:
            stage = "STAGE_1_FRIENDLY_REMINDER"
            action = "SEND_STATEMENT_OF_ACCOUNT"
            dunning_copy = (
                f"Hi {invoice.contact_person}! Quick courtesy follow-up from IronPeak GymOS regarding Invoice #{invoice.invoice_id} (₹{invoice.invoice_amount_inr:,.2f}).\n\n"
                f"You can settle online via corporate card / NEFT on our Razorpay portal:\n"
                f"👉 {payment_url}\n"
                f"Thank you for your ongoing partnership!"
            )

        return {
            "invoice_id": invoice.invoice_id,
            "company_name": invoice.company_name,
            "amount_inr": invoice.invoice_amount_inr,
            "days_overdue": invoice.days_overdue,
            "dunning_stage": stage,
            "action_taken": action,
            "payment_link": payment_url,
            "dunning_notice_copy": dunning_copy
        }
