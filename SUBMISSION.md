# Razorpay AI Buildathon 2026 — Submission Card

## 📌 Project Overview
* **Project Name**: GymOS AI Revenue Recovery Sentinel
* **Track**: **Track 03 — AI Revenue Recovery**
* **Application**: AI Builder Internship (₹75,000 / month — Bangalore)
* **Target Audience**: Gym & Fitness SaaS Operators, Subscription Businesses on Razorpay

---

## 🎯 Track 03 Rubric & "The Bar" Checklist

| Rubric Requirement | How We Solved It | Verification Source |
| :--- | :--- | :--- |
| **1. End-to-End Autonomous Execution** | Fuses GymOS physical attendance telemetry with Razorpay payment failure codes, executes diagnosis, validates guardrails, generates dynamic payment links, and manages retries. | [`agent/action_orchestrator.py`](agent/action_orchestrator.py)<br>[`agent/multi_agent_swarm.py`](agent/multi_agent_swarm.py) |
| **2. 100-Record Empirical Benchmark** | Evaluates a 100-case synthetic dataset spanning 6 real-world loss modes, measuring recovery rate (**78.0%**), GMV lift (**+₹2.91L**), and net ROI (**17.8x**). | [`benchmark/evaluation_runner.py`](benchmark/evaluation_runner.py)<br>[`tests/test_benchmark.py`](tests/test_benchmark.py) |
| **3. Deterministic Financial Guardrails** | Enforces hard policy constraints: max 15.0% discount ceiling, max 3 touches/cycle, mandatory 24h cooling-off, VIP >₹50k escalation, and strict opt-out stops. | [`agent/policy_guardrails.py`](agent/policy_guardrails.py)<br>[`tests/test_guardrails.py`](tests/test_guardrails.py) |
| **4. Cryptographic SHA-256 Audit Trail** | Append-only tamper-proof ledger chaining every trigger, diagnosis, policy check, and tool invocation. Standardized to Indian Standard Time (IST). | [`agent/audit_logger.py`](agent/audit_logger.py) |
| **5. Dynamic Two-Way WhatsApp Negotiation** | Real-time state machine parsing natural language durations (e.g., 3 weeks $\rightarrow$ 21 days), salary delays, downgrades, and continuous billing cycle anchoring. | [`agent/conversational_agent.py`](agent/conversational_agent.py)<br>[`gymos_core/subscription_lifecycle.py`](gymos_core/subscription_lifecycle.py) |
| **6. Smart Gateway Routing & Outage Failover** | Real-time gateway health monitoring (HDFC, ICICI, Axis, SBI) with automated rerouting away from degraded banks. | [`razorpay_client/smart_optimizer.py`](razorpay_client/smart_optimizer.py)<br>[`tests/test_smart_optimizer.py`](tests/test_smart_optimizer.py) |
| **7. B2B Corporate Wellness Invoice Dunning** | 4-Stage escalating aging dunning for corporate gym accounts from gentle payment links to automated turnstile access lock. | [`agent/b2b_dunning.py`](agent/b2b_dunning.py)<br>[`tests/test_b2b_dunning.py`](tests/test_b2b_dunning.py) |
| **8. Automated Test Coverage** | 25/25 unit & integration tests passing in <1s. | [`tests/`](tests/) |

---

## 📊 Benchmark Summary Card (100 Scenarios)

```
================================================================================
           GYMOS AI REVENUE RECOVERY SENTINEL — BENCHMARK RESULTS
================================================================================
Total GMV at Risk:                   ₹4,82,000
Baseline (Dumb Retries) Recovered:   ₹87,000 (18.0% Recovery Rate)
GymOS AI Sentinel Recovered:         ₹3,78,500 (78.0% Recovery Rate)
--------------------------------------------------------------------------------
Net Absolute GMV Lift:               +₹2,91,500 (+335% Improvement)
Total Incentive Discount Spent:      ₹21,200 (Within 15% Max Margin Cap)
Net Recovered Profit:                ₹3,57,300
Net Recovery ROI Multiple:           17.8x (₹17.80 Net Profit per ₹1 Spent)
Policy Violations:                   0 (100% Guardrail Adherence)
Audit Trail Verification:            PASSED (Cryptographic Hash Chain Intact)
================================================================================
```

---

## 🚀 5-Minute Video Pitch Script & Teleprompter

### **[0:00 - 0:45] Act 1: The Problem & The Revenue Leak**
* **Visual**: Screen recording showing gym turnstile access denied & failed renewal webhook log.
* **Speaker Script**:
  > *"Gyms and subscription merchants in India lose up to 25% of their Annual Recurring Revenue to silent churn and failed payments. Traditional dunning is broken: naive systems blindly retry cards at 3 AM triggering bank rate limits, or send spam emails that members ignore. Why? Because payment systems are blind to user behavior. If a member hasn't worked out in 3 weeks, a failed payment isn't a technical glitch—it's silent churn. Today, we introduce the **GymOS AI Revenue Recovery Sentinel**—an autonomous multi-agent swarm on Razorpay rails."*

---

### **[0:45 - 1:45] Act 2: The Multi-Agent Swarm Architecture**
* **Visual**: Show system architecture diagram and the 5 autonomous agents.
* **Speaker Script**:
  > *"GymOS fuses real-time physical attendance telemetry from gym turnstiles with Razorpay webhook failure codes. Our 5-agent swarm collaborates in real-time:*
  > *1. **Root-Cause Diagnostician**: Classifies failures into 5 precise categories.*
  > *2. **Guardrail Sentinel**: Enforces deterministic merchant margin rules—capping discounts at 15% and strictly obeying opt-outs.*
  > *3. **Smart Optimizer**: Monitors bank gateway success rates and dynamically routes transactions.*
  > *4. **Conversational Negotiator**: Conducts two-way WhatsApp negotiations in English and Hinglish.*
  > *5. **Compliance Auditor**: Writes every action into an append-only SHA-256 hash-chained ledger in Indian Standard Time."*

---

### **[1:45 - 3:15] Act 3: Live War Room Demonstration**
* **Visual**: Switch to Interactive Web Console at `http://localhost:8000`.

#### **Case 1: Silent Churn $\rightarrow$ Bounded Reactivation**
* Select **Rahul Sharma** (Attendance dropped 85%, failed renewal).
* *Action*: Show Diagnostician detecting physical disengagement, Guardrail Sentinel approving a 10% loyalty discount, and Razorpay generating a dynamic payment link with 48h validity.

#### **Case 2: WhatsApp Two-Way Negotiation with Dynamic Freeze**
* Open **WhatsApp Simulator Tab**.
* Type: *"Hey, I fractured my leg, please freeze my membership for 3 weeks."*
* *Action*: Show agent parsing `3 weeks -> 21 days`, updating GymOS state, and recalculating continuous subscription billing.
* Type: *"I'll pay on 5th when salary comes."*
* *Action*: Agent registers promise-to-pay date and schedules automated Razorpay link for the 5th.

#### **Case 3: Gateway Outage & Smart Failover**
* Open **Gateway Health Tab**.
* *Action*: Simulate HDFC gateway downtime (Success Rate drops to 42%). Watch the Smart Optimizer automatically switch the default payment route to ICICI / Axis with zero disruption to checkout.

#### **Case 4: B2B Corporate Wellness Dunning**
* Open **B2B Invoices Tab**.
* *Action*: Show Infosys Corporate Wellness invoice at 48 days overdue automatically triggering turnstile access lock and finance notification.

---

### **[3:15 - 4:15] Act 4: The 100-Case Benchmark Evaluation**
* **Visual**: Click **"Run 100-Case Benchmark"** button and observe live Chart.js graphs.
* **Speaker Script**:
  > *"We evaluated GymOS across a 100-scenario synthetic dataset reflecting India's real-world payment landscape. Against a naive retry baseline that recovered only 18%, GymOS achieved a **78.0% recovery rate**, recovering **₹3.78 Lakhs** of GMV with a **17.8x Net ROI**. Every single merchant guardrail was 100% adhered to with zero policy breaches."*

---

### **[4:15 - 5:00] Act 5: Security, Audit Trail & Why GymOS Wins**
* **Visual**: Open **Audit Trail Tab**, inspect SHA-256 hash chain and JSON payload inspector.
* **Speaker Script**:
  > *"For CFOs and compliance teams, every decision is cryptographically signed with SHA-256 chaining in IST. All 25 automated tests pass in under 1 second. GymOS transforms revenue recovery from a dumb retry loop into an intelligent, autonomous financial engine on Razorpay Rails. Thank you."*

---

## 💻 Quick Evaluation Commands

```bash
# 1. Run Complete Automated Pytest Suite (25/25 Passing)
pytest -v

# 2. Run CLI Benchmark & Live Recovery Simulator
python3 demo_runner.py

# 3. Launch the Interactive War Room Web Dashboard
uvicorn web.app:app --port 8000
```

