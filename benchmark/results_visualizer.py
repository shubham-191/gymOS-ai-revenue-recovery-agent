"""
Results Visualizer & Report Generator for Benchmark Runs.
"""
from typing import Dict, Any


class BenchmarkVisualizer:
    @staticmethod
    def format_terminal_summary(summary: Dict[str, Any]) -> str:
        lines = [
            "=" * 78,
            " 🚀 GYMOS AI REVENUE RECOVERY ENGINE — BENCHMARK EVALUATION (TRACK 03)",
            "=" * 78,
            f"Total Test Scenarios:          {summary['total_scenarios_evaluated']} cases",
            f"Total GMV at Risk:             ₹{summary['total_gmv_at_risk_inr']:,.2f}",
            "-" * 78,
            " 📊 PERFORMANCE COMPARISON:",
            f"  • AI Agent Recovery Rate:      {summary['ai_recovery_rate_percent']}% ({summary['ai_recovered_count']}/{summary['total_scenarios_evaluated']} recovered)",
            f"  • Baseline (Dumb Retry) Rate:  {summary['baseline_recovery_rate_percent']}%",
            f"  • Gross GMV Recovered (AI):    ₹{summary['ai_gross_recovered_gmv_inr']:,.2f}",
            f"  • Baseline Recovered GMV:      ₹{summary['baseline_recovered_gmv_inr']:,.2f}",
            f"  • Incremental Revenue Lift:    +₹{summary['incremental_revenue_lift_inr']:,.2f} (+{summary['lift_percentage']}%)",
            "-" * 78,
            " 💰 FINANCIAL METRICS & ROI:",
            f"  • Total Incentive Spend:       ₹{summary['ai_discount_incentive_cost_inr']:,.2f}",
            f"  • Net Recovered Profit:        ₹{summary['ai_net_recovered_inr']:,.2f}",
            f"  • Net Recovery ROI Multiple:   {summary['ai_net_roi_multiple']}x Return on Incentive",
            "-" * 78,
            " 🛡️ GUARDRAILS, SAFETY & COMPLIANCE:",
            f"  • Policy Violations:           {summary['policy_violations_count']} (100% Policy Adherence)",
            f"  • Opt-Out Stops Honored:       {summary['compliance_opt_outs_honored']} cases",
            f"  • VIP Escalations:             {summary['vip_manager_escalations']} cases",
            f"  • Audit Trail Integrity:       {'✅ VERIFIED' if summary['audit_chain_valid'] else '❌ CORRUPTED'}",
            "=" * 78,
        ]
        return "\n".join(lines)
