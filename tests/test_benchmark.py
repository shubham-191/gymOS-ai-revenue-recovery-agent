"""
Integration test for 100-batch Benchmark Evaluation.
Verifies execution, recovery threshold (>=70%), 0 policy violations, and audit integrity.
"""
import pytest
from benchmark.evaluation_runner import BenchmarkRunner


def test_benchmark_100_scenarios_execution():
    runner = BenchmarkRunner()
    summary = runner.run_benchmark(simulation_seed=42)

    assert summary["total_scenarios_evaluated"] == 100
    assert summary["ai_recovery_rate_percent"] >= 70.0
    assert summary["baseline_recovery_rate_percent"] <= 25.0
    assert summary["policy_violations_count"] == 0
    assert summary["compliance_opt_outs_honored"] >= 5
    assert summary["audit_chain_valid"] is True
    assert summary["ai_gross_recovered_gmv_inr"] > summary["baseline_recovered_gmv_inr"]
