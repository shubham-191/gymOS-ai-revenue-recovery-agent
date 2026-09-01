"""
Synthetic Dataset Generator for Track 03 Benchmark.
Generates 100 realistic, diverse member churn and payment loss scenarios.
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from gymos_core.models import MemberProfile, MembershipTier, FailureReasonCode

FIRST_NAMES = ["Aarav", "Aditi", "Ananya", "Dev", "Ishaan", "Kavya", "Manish", "Neha", "Pooja", "Rahul", "Rohan", "Sanjay", "Tanvi", "Varun", "Vikram", "Zoya", "Karan", "Priya", "Amit", "Sneha"]
LAST_NAMES = ["Sharma", "Verma", "Rao", "Patel", "Gupta", "Mehta", "Iyer", "Nair", "Reddy", "Singh", "Das", "Joshi", "Kulkarni", "Bose", "Choudhury"]

TIER_CONFIGS = [
    (MembershipTier.MONTHLY_BASIC, 2499.0, 0.40),
    (MembershipTier.QUARTERLY_PRO, 6499.0, 0.35),
    (MembershipTier.ANNUAL_ELITE, 19999.0, 0.20),
    (MembershipTier.CORPORATE_VIP, 60000.0, 0.05),
]


def generate_benchmark_dataset(count: int = 100, seed: int = 42) -> List[Dict[str, Any]]:
    random.seed(seed)
    scenarios = []

    # Distribution buckets:
    # 1. Technical bank failure (20%)
    # 2. Insufficient balance / salary cycle (25%)
    # 3. Silent Churn / disengagement (30%)
    # 4. Expired mandate (15%)
    # 5. High value VIP escalation (5%)
    # 6. Opt-out compliance edge case (5%)

    for i in range(1, count + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        full_name = f"{first} {last}"
        phone = f"+9198{random.randint(10000000, 99999999)}"
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        lang = "hinglish" if random.random() < 0.70 else "english"

        # Pick tier
        r_tier = random.random()
        if i % 20 == 0:  # 5% VIP
            tier, amount = MembershipTier.CORPORATE_VIP, 60000.0
        elif r_tier < 0.45:
            tier, amount = MembershipTier.MONTHLY_BASIC, 2499.0
        elif r_tier < 0.80:
            tier, amount = MembershipTier.QUARTERLY_PRO, 6499.0
        else:
            tier, amount = MembershipTier.ANNUAL_ELITE, 19999.0

        # Behavioral & Failure scenario assignment
        scenario_type = i % 6
        opted_out = False
        consecutive_fails = random.randint(0, 2)
        history_discount = 0.0

        if scenario_type == 0:
            # Opt-out compliance test case
            opted_out = True
            failure_code = FailureReasonCode.USER_CANCELLED
            days_inactive = 20
            visits_30 = 2
            base_visits = 4.0
        elif scenario_type == 1:
            # Technical bank gateway failure
            failure_code = FailureReasonCode.BANK_SERVER_UNAVAILABLE
            days_inactive = 1
            visits_30 = 14
            base_visits = 4.0
        elif scenario_type == 2:
            # Insufficient funds
            failure_code = FailureReasonCode.INSUFFICIENT_FUNDS
            days_inactive = 3
            visits_30 = 12
            base_visits = 3.5
        elif scenario_type == 3:
            # Silent churn
            failure_code = FailureReasonCode.NONE
            days_inactive = random.randint(14, 28)
            visits_30 = random.randint(0, 3)
            base_visits = 4.0
        elif scenario_type == 4:
            # Expired mandate
            failure_code = FailureReasonCode.MANDATE_EXPIRED
            days_inactive = 4
            visits_30 = 11
            base_visits = 3.0
        else:
            # Price sensitive / general
            failure_code = FailureReasonCode.CARD_DECLINED
            days_inactive = random.randint(8, 16)
            visits_30 = random.randint(4, 8)
            base_visits = 3.5

        member_dict = {
            "scenario_id": f"SCN-{i:03d}",
            "member_id": f"mem_gym_{i:04d}",
            "tenant_id": "gym_ironpeak_001",
            "name": full_name,
            "phone": phone,
            "email": email,
            "language_preference": lang,
            "membership_tier": tier.value,
            "membership_amount": amount,
            "plan_start_date": "2026-06-01",
            "plan_expiry_date": "2026-09-01",
            "baseline_visits_per_week": base_visits,
            "actual_visits_last_30_days": visits_30,
            "days_since_last_checkin": days_inactive,
            "lifetime_paid_inr": amount * random.randint(2, 6),
            "previous_payment_method": "UPI_AUTOPAY" if i % 2 == 0 else "CARD",
            "consecutive_failed_attempts": consecutive_fails,
            "opted_out": opted_out,
            "last_failure_code": failure_code.value,
            "last_failure_timestamp": "2026-09-01T08:30:00Z",
            "historical_discount_given": history_discount
        }
        scenarios.append(member_dict)

    return scenarios


def save_dataset_to_file(filepath: Optional[str] = None) -> str:
    path = Path(filepath) if filepath else Path(__file__).resolve().parent / "test_dataset.json"
    dataset = generate_benchmark_dataset(100)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
    return str(path)


if __name__ == "__main__":
    saved_path = save_dataset_to_file()
    print(f"Successfully generated 100 benchmark scenarios at: {saved_path}")
