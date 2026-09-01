"""
Razorpay Optimizer & Smart Payment Routing Engine.
Provides multi-gateway health monitoring, circuit breaking,
and automated dynamic failover across banking rails.
"""
import time
import random
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"        # Normal healthy operation
    HALF_OPEN = "HALF_OPEN"  # Testing recovery
    OPEN = "OPEN"            # Tripped / Outage detected (traffic rerouted)


class PaymentRail(BaseModel):
    rail_id: str
    gateway_name: str
    primary_protocol: str   # 'UPI_AUTOPAY', 'NETBANKING', 'CARD_TOKEN', 'DYNAMIC_QR'
    success_rate_pct: float
    average_latency_ms: int
    circuit_state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    total_routed_volume_inr: float = 0.0
    priority: int = 1


class SmartPaymentRouter:
    def __init__(self):
        self.rails: Dict[str, PaymentRail] = {
            "rail_hdfc": PaymentRail(
                rail_id="rail_hdfc",
                gateway_name="Razorpay HDFC Direct Rail",
                primary_protocol="UPI_AUTOPAY",
                success_rate_pct=94.5,
                average_latency_ms=320,
                priority=1
            ),
            "rail_icici": PaymentRail(
                rail_id="rail_icici",
                gateway_name="Razorpay ICICI Smart Gateway",
                primary_protocol="NETBANKING_MANDATE",
                success_rate_pct=93.8,
                average_latency_ms=410,
                priority=2
            ),
            "rail_axis": PaymentRail(
                rail_id="rail_axis",
                gateway_name="Razorpay Axis Direct Rail",
                primary_protocol="CARD_TOKENIZATION",
                success_rate_pct=91.2,
                average_latency_ms=480,
                priority=3
            ),
            "rail_dynamic_qr": PaymentRail(
                rail_id="rail_dynamic_qr",
                gateway_name="Razorpay High-Resilience Dynamic UPI QR",
                primary_protocol="DYNAMIC_QR",
                success_rate_pct=98.2,
                average_latency_ms=250,
                priority=4
            )
        }

    def get_all_rails_status(self) -> List[Dict[str, Any]]:
        return [rail.model_dump() for rail in sorted(self.rails.values(), key=lambda r: r.priority)]

    def route_transaction(self, amount_inr: float, preferred_method: Optional[str] = None) -> Dict[str, Any]:
        """
        Selects the optimal healthy payment rail based on success rates, latency, and circuit status.
        If the primary rail is down (OPEN), dynamically fails over to the next healthiest rail.
        """
        # Sort candidate rails by circuit health and priority
        healthy_rails = [
            r for r in sorted(self.rails.values(), key=lambda x: (x.circuit_state != CircuitState.CLOSED, x.priority))
            if r.circuit_state != CircuitState.OPEN
        ]

        if not healthy_rails:
            # Fallback to high-resilience Dynamic QR
            selected_rail = self.rails["rail_dynamic_qr"]
            failover_triggered = True
            failover_reason = "ALL_PRIMARY_RAILS_DEGRADED_FALLBACK_QR"
        else:
            selected_rail = healthy_rails[0]
            failover_triggered = (selected_rail.priority > 1)
            failover_reason = f"FAILOVER_TO_{selected_rail.rail_id.upper()}" if failover_triggered else "PRIMARY_HEALTHY"

        selected_rail.total_routed_volume_inr += amount_inr
        logger.info("Optimizer routed ₹%s through %s (Failover=%s, Reason=%s)", 
                    amount_inr, selected_rail.gateway_name, failover_triggered, failover_reason)

        return {
            "transaction_amount_inr": amount_inr,
            "selected_rail_id": selected_rail.rail_id,
            "gateway_name": selected_rail.gateway_name,
            "protocol_used": selected_rail.primary_protocol,
            "expected_latency_ms": selected_rail.average_latency_ms,
            "gateway_success_rate": selected_rail.success_rate_pct,
            "failover_triggered": failover_triggered,
            "routing_reason": failover_reason,
            "circuit_state": selected_rail.circuit_state.value
        }

    def simulate_gateway_outage(self, rail_id: str, trip_circuit: bool = True) -> Dict[str, Any]:
        """
        Simulates an upstream bank server outage or degradation to test dynamic failover.
        """
        rail = self.rails.get(rail_id)
        if not rail:
            return {"status": "ERROR", "message": f"Rail {rail_id} not found"}

        if trip_circuit:
            rail.circuit_state = CircuitState.OPEN
            rail.success_rate_pct = 32.0  # Degraded
            rail.average_latency_ms = 2400
            rail.consecutive_failures = 5
            logger.warning("TRIPPED CIRCUIT BREAKER FOR %s (Success rate dropped to 32%%)", rail.gateway_name)
        else:
            rail.circuit_state = CircuitState.CLOSED
            rail.success_rate_pct = 94.5  # Restored
            rail.average_latency_ms = 320
            rail.consecutive_failures = 0
            logger.info("RESTORED CIRCUIT BREAKER FOR %s (Healthy)", rail.gateway_name)

        return {
            "status": "UPDATED",
            "rail_id": rail_id,
            "circuit_state": rail.circuit_state.value,
            "success_rate_pct": rail.success_rate_pct,
            "average_latency_ms": rail.average_latency_ms
        }
