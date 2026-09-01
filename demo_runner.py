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
    run_benchmark_demo()
    print("\n✨ Demo completed successfully. Start the Web Console via: uvicorn web.app:app --reload --port 8000\n")
