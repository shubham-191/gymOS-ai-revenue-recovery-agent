"""
Unit tests for Razorpay Smart Optimizer and Failover Routing.
"""
import pytest
from razorpay_client.smart_optimizer import SmartPaymentRouter, CircuitState


@pytest.fixture
def router():
    return SmartPaymentRouter()


def test_smart_router_initial_state(router):
    rails = router.get_all_rails_status()
    assert len(rails) == 4
    assert rails[0]["rail_id"] == "rail_hdfc"
    assert rails[0]["circuit_state"] == "CLOSED"


def test_smart_router_healthy_route(router):
    res = router.route_transaction(6499.0)
    assert res["selected_rail_id"] == "rail_hdfc"
    assert res["failover_triggered"] is False
    assert res["circuit_state"] == "CLOSED"


def test_smart_router_dynamic_failover_on_outage(router):
    # Simulate HDFC UPI Server Outage
    router.simulate_gateway_outage("rail_hdfc", trip_circuit=True)
    
    # Route transaction - should automatically failover to ICICI
    res = router.route_transaction(6499.0)
    assert res["selected_rail_id"] == "rail_icici"
    assert res["failover_triggered"] is True
    assert "FAILOVER" in res["routing_reason"]
