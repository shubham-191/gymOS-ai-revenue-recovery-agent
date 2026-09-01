# Razorpay AI Buildathon 2026 — Submission Card

## 📌 Project Overview
* **Project Name**: GymOS AI Revenue Recovery Sentinel
* **Track**: **Track 03 — AI Revenue Recovery**
* **Repository**: Public GitHub Repository
* **Target Audience**: Gym & Fitness SaaS Operators, Subscription Merchants on Razorpay

---

## 🎯 Track 03 Rubric & "The Bar" Checklist

| Requirement | How We Solved It | Verification File |
| :--- | :--- | :--- |
| **End-to-End Execution** | Diagnoses root cause, verifies guardrails, dispatches dynamic Razorpay Payment Links, and schedules UPI Autopay smart retries. | [`agent/action_orchestrator.py`](file:///Users/shubhamkumarrai/Desktop/Razorpay_Buildathon/agent/action_orchestrator.py) |
| **100-Record Benchmark** | Evaluates a 100-case synthetic dataset spanning 6 real loss modes, measuring recovery rate (78.0%), GMV lift (+₹2.91L), and net ROI (17.8x). | [`benchmark/evaluation_runner.py`](file:///Users/shubhamkumarrai/Desktop/Razorpay_Buildathon/benchmark/evaluation_runner.py) |
| **Deterministic Guardrails** | Enforces maximum 15% discount caps, max 3 touches per cycle, mandatory cooling-off, and strict opt-out stops. | [`agent/policy_guardrails.py`](file:///Users/shubhamkumarrai/Desktop/Razorpay_Buildathon/agent/policy_guardrails.py) |
| **Immutable Audit Trail** | SHA-256 cryptographically chained audit logging verifying every decision, tool payload, and signature check. | [`agent/audit_logger.py`](file:///Users/shubhamkumarrai/Desktop/Razorpay_Buildathon/agent/audit_logger.py) |
| **Failure Handling** | Demonstrates resilience to bank timeouts, expired mandates, invalid customer inputs, and API errors. | [`tests/`](file:///Users/shubhamkumarrai/Desktop/Razorpay_Buildathon/tests/) |

---

## 📊 Benchmark Summary Card (100 Scenarios)

* **Total GMV at Risk**: ₹4,82,000
* **AI Agent Recovery Rate**: **78.0%** (vs **18.0%** dumb retry baseline)
* **Gross GMV Recovered**: **₹3,78,500**
* **Incentive Discount Spend**: ₹21,200
* **Net Recovered Profit**: **₹3,57,300**
* **Net ROI Multiple**: **17.8x Return on Incentive**
* **Policy Adherence**: **100% (0 violations)**
* **Audit Chain Verification**: **Passed (Cryptographically Intact)**

---

## 🚀 5-Minute Video Pitch Outline

1. **[0:00 - 0:45] The Problem**: Why gyms and subscription businesses lose 20–30% of revenue to silent churn, mandate expiration, and naive retry dunning.
2. **[0:45 - 1:45] The GymOS Architecture**: Integrating GymOS physical attendance telemetry with Razorpay payment signals into a multi-signal root-cause diagnostician.
3. **[1:45 - 3:00] Live Demonstration**:
   - Case 1: Member with silent churn (attendance drop > 70%) $\rightarrow$ Bounded 10% discount + Hinglish WhatsApp message + Dynamic Razorpay Link.
   - Case 2: Bank gateway downtime $\rightarrow$ Silent Smart Retry with zero merchant discount.
   - Case 3: Compliance Opt-Out $\rightarrow$ Hard stop enforced by guardrails.
4. **[3:00 - 4:15] 100-Case Benchmark Evaluation**: Running the batch simulation live, showcasing the 78% recovery rate, +₹2.91L incremental lift, and 17.8x ROI.
5. **[4:15 - 5:00] The Bar & Security**: Demonstrating the SHA-256 chained audit trail and policy adherence guarantees.

---

## 💻 Quick Start & Evaluation
```bash
# 1. Run CLI Benchmark & Single Demo
python3 demo_runner.py

# 2. Launch Interactive Web Console
uvicorn web.app:app --port 8000

# 3. Run Automated Pytest Suite
pytest -v
```
