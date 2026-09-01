"""
Razorpay Webhook Event Processor for Recovery Lifecycle Tracking.
"""
from typing import Dict, Any
import logging
from razorpay_client.client import RazorpayRecoveryClient

logger = logging.getLogger(__name__)


class WebhookProcessor:
    def __init__(self, razorpay_client: RazorpayRecoveryClient):
        self.client = razorpay_client

    def process_incoming_webhook(self, payload: Dict[str, Any], signature: str, raw_body: str) -> Dict[str, Any]:
        """
        Parses webhook events like `payment_link.paid`, `payment.failed`, `subscription.halted`.
        """
        if not self.client.verify_webhook_signature(raw_body, signature):
            logger.warning("Invalid webhook signature received.")
            return {"status": "REJECTED", "reason": "INVALID_SIGNATURE"}

        event = payload.get("event", "unknown")
        logger.info("Processing verified Razorpay Webhook event: %s", event)

        if event == "payment_link.paid":
            entity = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
            return {
                "status": "PROCESSED",
                "event": event,
                "link_id": entity.get("id"),
                "amount_paid_inr": (entity.get("amount_paid", 0) / 100.0),
                "customer_phone": entity.get("customer", {}).get("contact"),
                "recovery_state": "SUCCESS"
            }
        elif event == "payment.failed":
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            return {
                "status": "PROCESSED",
                "event": event,
                "payment_id": payment_entity.get("id"),
                "error_code": payment_entity.get("error_code"),
                "error_description": payment_entity.get("error_description"),
                "recovery_state": "TRIGGER_RECOVERY_PIPELINE"
            }

        return {"status": "IGNORED", "event": event}
