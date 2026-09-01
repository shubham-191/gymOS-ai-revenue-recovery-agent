"""
Event definitions matching GymOS Kafka event streams.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid


class GymOSEventType:
    PAYMENT_FAILED = "payment.payment.failed.v1"
    PAYMENT_COMPLETED = "payment.payment.completed.v1"
    ATTENDANCE_ANOMALY = "attendance.member.disengaged.v1"
    RENEWAL_UPCOMING = "membership.subscription.renewal_due.v1"
    MANDATE_EXPIRED = "payment.mandate.expired.v1"
    MEMBER_OPT_OUT = "notification.member.opt_out.v1"


class GymOSEventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    occurred_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    producer: str = "gymos-platform"
    tenant_id: str = "gym_ironpeak_001"
    payload: Dict[str, Any]
