"""
Unit tests for Razorpay Client and Webhook Handler.
"""
import pytest
from razorpay_client.client import RazorpayRecoveryClient
from razorpay_client.webhook_handler import WebhookProcessor


@pytest.fixture
def rzp_client():
    return RazorpayRecoveryClient(key_id="mock", key_secret="mock")


def test_create_dynamic_payment_link(rzp_client):
    res = rzp_client.create_dynamic_payment_link(
        amount_inr=5849.10,
        member_name="Rahul Sharma",
        member_phone="+919876543210",
        member_email="rahul@example.com",
        description="GymOS Renewal - Quarterly Pro"
    )
    assert res is not None
    assert res["id"].startswith("plink_")
    assert "rzp.io" in res["short_url"]
    assert res["amount"] == 5849.10


def test_webhook_payment_link_paid(rzp_client):
    processor = WebhookProcessor(rzp_client)
    sample_payload = {
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_test123",
                    "amount_paid": 584910,
                    "customer": {
                        "contact": "+919876543210"
                    }
                }
            }
        }
    }
    result = processor.process_incoming_webhook(
        payload=sample_payload,
        signature="mock_sig",
        raw_body='{"event": "payment_link.paid"}'
    )
    assert result["status"] == "PROCESSED"
    assert result["recovery_state"] == "SUCCESS"
    assert result["amount_paid_inr"] == 5849.10
