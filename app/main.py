import asyncio
import json
import httpx
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.agents.audit import AuditAgent
from app.agents.deletion_request import DeletionRequestAgent
from app.agents.discovery import DiscoveryAgent
from app.agents.verification import VerificationAgent
from app.agents.intake import (
    OtpStart, OtpVerify, RequestSubmit, catalog, inbox, list_requests,
    start_otp, submit_request, verify_otp,
)
from app.core.events import event_bus
from app.orchestrator import Orchestrator

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="DPDP Erasure Orchestrator", version="0.5.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
orchestrator = Orchestrator()
discovery_agent = DiscoveryAgent()
deletion_agent = DeletionRequestAgent()
verification_agent = VerificationAgent()
audit_agent = AuditAgent()
NOVAMART_API = "http://127.0.0.1:9000"


@app.get("/")
async def dashboard():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "online", "service": "orchestrator", "specialist_agents": 6}


@app.get("/api/agents")
async def agents():
    return {"agents": orchestrator.agent_status()}


@app.get("/api/companies")
async def companies():
    return catalog()


@app.post("/api/intake/otp")
async def create_otp(payload: OtpStart):
    result = start_otp(payload)
    await event_bus.publish({"agent": "Intake", "status": "WORKING",
                             "message": f"Offline {payload.channel} OTP created for a demo request."})
    return result


@app.get("/api/dev-inbox")
async def dev_inbox():
    return {"messages": inbox()}


@app.post("/api/intake/verify")
async def check_otp(payload: OtpVerify):
    result = verify_otp(payload)
    await event_bus.publish({"agent": "Intake", "status": "SUCCESS",
                             "message": "OTP verified. Requester may submit the selected categories."})
    return result


@app.post("/api/intake/submit")
async def create_request(payload: RequestSubmit):
    result = submit_request(payload)
    request = get_request(result["request_id"])
    audit_agent.record(request_id=result["request_id"], subject=request["customer_id"],
        agent="Intake", action="REQUEST_ACCEPTED", outcome=result["status"],
        item_count=len(result["selected_categories"]), categories=result["selected_categories"])
    await event_bus.publish({"agent": "Intake", "status": "SUCCESS",
                             "request_id": result["request_id"],
                             "message": f"Intake accepted {len(result['selected_categories'])} selected data categories."})
    await event_bus.publish({"agent": "Orchestrator", "status": "INFO",
                             "request_id": result["request_id"],
                             "message": "Request registered. Starting scoped discovery against NovaMart's authorized demo API."})
    return result


def get_request(request_id: str) -> dict:
    request = next((item for item in list_requests() if item["request_id"] == request_id), None)
    if request is None:
        raise HTTPException(status_code=404, detail="Erasure request not found.")
    return request


@app.post("/api/discovery/{request_id}")
async def run_discovery(request_id: str):
    request = get_request(request_id)
    result = await discovery_agent.handle(request)
    audit_agent.record(request_id=request_id, subject=request["customer_id"],
        agent="Discovery", action="SCOPED_DISCOVERY", outcome="COMPLETED",
        item_count=result.get("count", len(result.get("items", []))),
        categories=request["selected_categories"])
    return result


@app.post("/api/deletion-request/{request_id}")
async def run_deletion_request(request_id: str):
    request = get_request(request_id)
    discovery = await discovery_agent.handle(request)
    result = await deletion_agent.handle(request, discovery)
    audit_agent.record(request_id=request_id, subject=request["customer_id"],
        agent="Deletion Request", action="COMPANY_REQUEST_SUBMITTED",
        outcome=result.get("status", "SUBMITTED"),
        item_count=len(discovery.get("items", [])), categories=request["selected_categories"])
    return result


@app.post("/api/company/approve/{company_ticket}")
async def company_approve(company_ticket: str):
    """Forward an explicit demo-operator action to the mock NovaMart service."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            f"{NOVAMART_API}/company/v1/erasure-requests/{company_ticket}/approve-and-execute"
        )
        response.raise_for_status()
        result = response.json()
    request = get_request(result["request_id"])
    audit_agent.record(request_id=result["request_id"], subject=request["customer_id"],
        agent="NovaMart Company Staff", action="COMPANY_APPROVAL_EXECUTION",
        outcome="EXECUTED", categories=request["selected_categories"])
    await event_bus.publish({
        "agent": "NovaMart Company Staff",
        "status": "SUCCESS",
        "request_id": result["request_id"],
        "message": "Mock company operator action completed against synthetic demo records.",
    })
    return result


@app.post("/api/verify/{request_id}")
async def verify_request(request_id: str):
    request = get_request(request_id)
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{NOVAMART_API}/company/v1/erasure-requests")
        response.raise_for_status()
        tickets = response.json()["requests"]
    ticket = next((item for item in tickets if item["request_id"] == request_id), None)
    if ticket is None:
        raise HTTPException(status_code=404, detail="No company ticket exists.")
    result = await verification_agent.handle(request, ticket)
    audit_agent.record(request_id=request_id, subject=request["customer_id"],
        agent="Verification", action="INDEPENDENT_VERIFICATION",
        outcome=result.get("status", "UNKNOWN"),
        item_count=result.get("leftover_count") or 0, categories=request["selected_categories"])
    return result


@app.get("/api/audit")
async def audit_events(limit: int = 100):
    return {"events": audit_agent.list_events(limit)}


@app.get("/api/audit/verify")
async def audit_integrity():
    return audit_agent.verify_chain()


@app.get("/api/requests")
async def requests():
    return {"requests": list_requests()}


@app.get("/api/events")
async def events():
    async def stream():
        queue = event_bus.subscribe()
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {json.dumps(item)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(stream(), media_type="text/event-stream")
