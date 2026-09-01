"""
Unit tests for B2B Corporate Accounts Receivable & Dunning.
"""
import pytest
from agent.b2b_dunning import B2BAccountsReceivableEngine, CorporateInvoice


@pytest.fixture
def b2b_engine():
    return B2BAccountsReceivableEngine()


def test_b2b_current_friendly_reminder(b2b_engine):
    inv = CorporateInvoice(
        invoice_id="INV-001",
        company_name="Acme Corp",
        contact_person="John Doe",
        contact_email="john@acme.com",
        contact_phone="+919876543210",
        employee_seat_count=50,
        invoice_amount_inr=150000.0,
        invoice_date="2026-08-01",
        due_date="2026-08-15",
        days_overdue=10,
        status="OVERDUE"
    )
    res = b2b_engine.evaluate_corporate_dunning(inv)
    assert res["dunning_stage"] == "STAGE_1_FRIENDLY_REMINDER"
    assert res["payment_link"] is not None


def test_b2b_critical_access_lock_60_days(b2b_engine):
    inv = CorporateInvoice(
        invoice_id="INV-002",
        company_name="Beta Corp",
        contact_person="Jane Doe",
        contact_email="jane@beta.com",
        contact_phone="+919876543211",
        employee_seat_count=150,
        invoice_amount_inr=450000.0,
        invoice_date="2026-06-01",
        due_date="2026-07-01",
        days_overdue=62,
        status="SUSPENDED"
    )
    res = b2b_engine.evaluate_corporate_dunning(inv)
    assert res["dunning_stage"] == "STAGE_4_ACCESS_LOCK"
    assert res["action_taken"] == "LOCK_CORPORATE_BIOMETRICS"
    assert "SUSPENSION" in res["dunning_notice_copy"]
