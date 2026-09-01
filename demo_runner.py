"""
GymOS AI Revenue Recovery Sentinel — CLI Interactive Demo Runner.
Run this script to evaluate single scenarios or the full 100-case benchmark.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from gymos_core.models import MemberProfile, MembershipTier, FailureReasonCode
from gymos_core.mock_gateway import GymOSGateway
from agent.action_orchestrator import RecoveryOrchestrator
from benchmark.evaluation_runner import BenchmarkRunner
from benchmark.results_visualizer import BenchmarkVisualizer


def run_single_demo():
    print("\n" + "=" * 78)
    print(" 🏋️‍♂️ GYMOS AI REVENUE RECOVERY AGENT — SINGLE SCENARIO EXECUTION")
    print("=" * 78)
    
    # 1. Create a sample member with disengagement + payment failure
    member = GymOSGateway.create_sample_member()
    print(f"\n[1] Ingested GymOS Platform Signals for Member: {member.name} ({member.member_id})")
    print(f"    • Plan: {member.membership_tier.value} (₹{member.membership_amount:,.2f})")
    print(f"    • Attendance: {member.actual_visits_last_30_days} visits in 30 days (Inactive for {member.days_since_last_checkin} days)")
    print(f"    • Payment Status: Failed ({member.last_failure_code.value})")

    # 2. Run Orchestrator
    orchestrator = RecoveryOrchestrator()
    intervention = orchestrator.process_recovery(member, trigger_signal="CLI_DEMO_SCAN")

    print("\n[2] AI Root Cause & Bounded Decision:")
    print(f"    • Diagnosed Root Cause: {intervention.root_cause}")
    print(f"    • Action Strategy:      {intervention.strategy_applied}")
    print(f"    • Approved Discount:    {intervention.discount_percentage}% (Max 15% Guardrail Cap)")
    print(f"    • Final Recovery Price: ₹{intervention.discounted_amount:,.2f}")
    print(f"    • Execution Status:     {intervention.status}")

    print("\n[3] Generated Razorpay Dynamic Payment Link:")
    print(f"    • Payment Link URL:     {intervention.razorpay_payment_link}")
    print(f"    • Razorpay Order/ID:    {intervention.razorpay_order_id}")

    print("\n[4] Generated Multi-Channel Copy (Hinglish/WhatsApp):")
    print("    " + "-" * 70)
    for line in intervention.recovery_copy.split("\n"):
        print("    " + line)
    print("    " + "-" * 70)

    print("\n[5] Guardrail Policy Audit:")
    for note in intervention.guardrail_reasons:
        print(f"    • {note}")


from agent.conversational_agent import ConversationalRecoveryAgent
from agent.b2b_dunning import B2BAccountsReceivableEngine


def run_conversational_demo():
    print("\n" + "=" * 78)
    print(" 💬 TWO-WAY CONVERSATIONAL WHATSAPP NEGOTIATION DEMO")
    print("=" * 78)
    chat_agent = ConversationalRecoveryAgent()
    member = GymOSGateway.create_sample_member()

    objections = [
        "I had an injury and broke my leg, need to pause for 30 days.",
        "Annual plan is too expensive for me right now. Can I get a cheaper option?",
        "Salary is delayed this month. I will pay on 5th."
    ]

    for idx, obj in enumerate(objections, 1):
        print(f"\n[Turn {idx}] Customer WhatsApp Message: '{obj}'")
        res = chat_agent.handle_incoming_message(member, obj)
        print(f"    ➔ AI Classified Intent: {res['intent']}")
        print(f"    ➔ Bounded Action Taken: {res['action_executed'].get('action')}")
        if res.get("payment_link"):
            print(f"    ➔ Dynamic Razorpay Link: {res['payment_link']}")
        print("    ➔ AI WhatsApp Reply:")
        for line in res["reply_message"].split("\n"):
            print(f"       {line}")


def run_b2b_demo():
    print("\n" + "=" * 78)
    print(" 🏢 B2B CORPORATE ACCOUNTS RECEIVABLE (AR) DUNNING DEMO")
    print("=" * 78)
    b2b_engine = B2BAccountsReceivableEngine()
    invoices = b2b_engine.get_sample_corporate_invoices()

    for inv in invoices:
        res = b2b_engine.evaluate_corporate_dunning(inv)
        print(f"\n• Corporate Client: {inv.company_name} ({inv.employee_seat_count} seats)")
        print(f"  Invoice: {inv.invoice_id} | Amount: ₹{inv.invoice_amount_inr:,.2f} | Aging: {inv.days_overdue} days overdue")
        print(f"  Dunning Stage: {res['dunning_stage']} ➔ Action: {res['action_taken']}")
        print(f"  B2B Razorpay Portal: {res['payment_link']}")


def run_benchmark_demo():
    print("\n" + "=" * 78)
    print(" 📊 RUNNING 100-RECORD BENCHMARK EVALUATION (TRACK 03 RUBRIC)")
    print("=" * 78)
    runner = BenchmarkRunner()
    summary = runner.run_benchmark(simulation_seed=42)
    report_text = BenchmarkVisualizer.format_terminal_summary(summary)
    print(report_text)


if __name__ == "__main__":
    print("\nStarting GymOS AI Revenue Recovery Sentinel...")
    run_single_demo()
    run_conversational_demo()
    run_b2b_demo()
    run_benchmark_demo()
    print("\n✨ Enterprise Demo completed successfully. Start the Web Console via: uvicorn web.app:app --reload --port 8000\n")

