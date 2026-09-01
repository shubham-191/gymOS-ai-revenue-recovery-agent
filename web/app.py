"""
FastAPI Server for GymOS AI Revenue Recovery Engine & Interactive Console.
"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from gymos_core.models import MemberProfile, RecoveryIntervention
from agent.action_orchestrator import RecoveryOrchestrator
from agent.audit_logger import AuditLogger
from agent.policy_guardrails import PolicyGuardrailEngine
from agent.conversational_agent import ConversationalRecoveryAgent
from agent.b2b_dunning import B2BAccountsReceivableEngine, CorporateInvoice
from benchmark.evaluation_runner import BenchmarkRunner
from benchmark.dataset_generator import generate_benchmark_dataset
from razorpay_client.client import RazorpayRecoveryClient
from razorpay_client.webhook_handler import WebhookProcessor

app = FastAPI(
    title="GymOS AI Revenue Recovery Engine",
    description="Autonomous, bounded revenue recovery engine for GymOS & Razorpay Buildathon (Track 03)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "web" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Shared instances
audit_logger = AuditLogger()
guardrail_engine = PolicyGuardrailEngine(
    max_discount_percentage=settings.MAX_DISCOUNT_PERCENT,
    max_touches=settings.MAX_RECOVERY_ATTEMPTS,
    strict_opt_out=True,
    vip_threshold_inr=settings.VIP_ESCALATION_THRESHOLD_INR
)
rzp_client = RazorpayRecoveryClient()
orchestrator = RecoveryOrchestrator(
    razorpay_client=rzp_client,
    audit_logger=audit_logger,
    guardrail_engine=guardrail_engine
)
webhook_processor = WebhookProcessor(rzp_client)
benchmark_runner = BenchmarkRunner()
conversational_agent = ConversationalRecoveryAgent(razorpay_client=rzp_client)
b2b_engine = B2BAccountsReceivableEngine(razorpay_client=rzp_client)


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>GymOS AI Revenue Recovery Engine</h1><p>Static UI not yet built.</p>")


@app.get("/api/health")
async def health():
    return {
        "status": "HEALTHY",
        "service": "GymOS-RecoverySentinel",
        "razorpay_mode": "MOCK_EMULATOR" if rzp_client.is_mock else "LIVE_TEST_MODE",
        "audit_integrity": audit_logger.verify_integrity()
    }


@app.get("/api/scenarios")
async def get_scenarios():
    dataset = generate_benchmark_dataset(20)  # Return sample 20 for instant UI selection
    return {"count": len(dataset), "scenarios": dataset}


@app.post("/api/recover/single")
async def recover_single(member: MemberProfile):
    try:
        intervention = orchestrator.process_recovery(member, trigger_signal="MANUAL_UI_TRIGGER")
        return intervention.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recover/batch")
async def run_batch_simulation(payload: Optional[Dict[str, Any]] = None):
    try:
        seed = payload.get("seed", 42) if payload else 42
        summary = benchmark_runner.run_benchmark(simulation_seed=seed)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit-trail")
async def get_audit_trail(limit: int = 30):
    entries = audit_logger.get_recent_entries(limit=limit)
    is_valid = audit_logger.verify_integrity()
    return {
        "total_entries": len(entries),
        "chain_integrity_verified": is_valid,
        "entries": list(reversed(entries))
    }


@app.get("/api/policies")
async def get_policies():
    return {
        "max_discount_percentage": guardrail_engine.max_discount,
        "max_touches": guardrail_engine.max_touches,
        "strict_opt_out": guardrail_engine.strict_opt_out,
        "vip_threshold_inr": guardrail_engine.vip_threshold
    }


class PolicyUpdateRequest(BaseModel):
    max_discount_percentage: float
    max_touches: int
    strict_opt_out: bool
    vip_threshold_inr: float


@app.post("/api/policies")
async def update_policies(req: PolicyUpdateRequest):
    guardrail_engine.max_discount = req.max_discount_percentage
    guardrail_engine.max_touches = req.max_touches
    guardrail_engine.strict_opt_out = req.strict_opt_out
    guardrail_engine.vip_threshold = req.vip_threshold_inr
    return {"status": "UPDATED", "policies": req.model_dump()}


class ChatMessageRequest(BaseModel):
    member: MemberProfile
    message: str
    history: Optional[List[Dict[str, str]]] = None


@app.post("/api/chat/respond")
async def chat_respond(req: ChatMessageRequest):
    try:
        res = conversational_agent.handle_incoming_message(
            member=req.member,
            incoming_message=req.message,
            conversation_history=req.history
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/b2b/invoices")
async def get_b2b_invoices():
    invoices = b2b_engine.get_sample_corporate_invoices()
    return {"count": len(invoices), "invoices": [inv.model_dump() for inv in invoices]}


class B2BDunningRequest(BaseModel):
    invoice: CorporateInvoice


@app.post("/api/b2b/dunning")
async def trigger_b2b_dunning(req: B2BDunningRequest):
    try:
        res = b2b_engine.evaluate_corporate_dunning(req.invoice)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None)
):
    raw_body = await request.body()
    body_str = raw_body.decode("utf-8")
    import json
    try:
        payload = json.loads(body_str)
    except Exception:
        payload = {}
    
    result = webhook_processor.process_incoming_webhook(
        payload=payload,
        signature=x_razorpay_signature or "mock_sig",
        raw_body=body_str
    )
    return result
