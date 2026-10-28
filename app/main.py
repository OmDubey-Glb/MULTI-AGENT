import asyncio
import json
import httpx
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.agents.audit import AuditAgent
from app.agents.human_review import HumanReviewAgent
from app.agents.monitoring import MonitoringAgent
from app.agents.deletion_request import DeletionRequestAgent
from app.agents.discovery import DiscoveryAgent
from app.agents.verification import VerificationAgent
from app.agents.intake import (
    OtpStart, OtpVerify, RequestSubmit, catalog, inbox, list_requests,
    start_otp, submit_request, verify_otp, create_demo_request,
)
from app.core.events import event_bus
from app.orchestrator import Orchestrator
from app.dpdp_assistant import answer_dpdp

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="DPDP Erasure Orchestrator", version="0.5.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
orchestrator = Orchestrator()
discovery_agent = DiscoveryAgent()
deletion_agent = DeletionRequestAgent()
verification_agent = VerificationAgent()
audit_agent = AuditAgent()
monitoring_agent = MonitoringAgent()
human_review_agent = HumanReviewAgent()
NOVAMART_API = "http://127.0.0.1:9000"


@app.get("/")
async def dashboard():
    return FileResponse(BASE_DIR / "static" / "index.html")




class DpdpAssistantQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=700)
    language: str = Field(default="en", pattern="^(en|hi)$")


@app.post("/api/dpdp-assistant/ask")
async def ask_dpdp_assistant(payload: DpdpAssistantQuestion):
    """Answer only from the curated bilingual DPDP knowledge base; no external model/API."""
    return answer_dpdp(payload.question, payload.language)

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
    monitoring_agent.register(result["request_id"], request["company_id"])
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


@app.post("/api/demo/scenario/{scenario}")
async def launch_demo_scenario(scenario: str):
    """Launch deterministic synthetic demo data; intentionally bypasses OTP only for judge scenarios."""
    modes = {
        "A": ("normal", "Scenario A · Happy path"),
        "B": ("replica_lag", "Scenario B · Replica lag"),
        "C": ("persistent_failure", "Scenario C · Persistent failure"),
    }
    if scenario not in modes:
        raise HTTPException(status_code=404, detail="Choose scenario A, B or C.")
    mode, label = modes[scenario]
    request = create_demo_request("CUST-1001", ["contact_details"], label)
    request["scenario_mode"] = mode
    monitoring_agent.register(request["request_id"], request["company_id"])
    audit_agent.record(request_id=request["request_id"], subject=request["customer_id"],
        agent="Demo Scenario", action="SCENARIO_LAUNCHED", outcome=label,
        item_count=1, categories=request["selected_categories"])
    await event_bus.publish({"agent": "Orchestrator", "status": "INFO",
        "request_id": request["request_id"], "message": label + " started with synthetic records. Demo launcher bypasses OTP."})
    discovery = await discovery_agent.handle(request)
    company_result = await deletion_agent.handle(request, discovery)
    if not company_result.get("company_ticket"):
        raise HTTPException(status_code=409, detail="Scenario data did not produce a company ticket.")
    monitoring_agent.update(request["request_id"], "AWAITING_COMPANY",
        company_ticket=company_result["company_ticket"], outcome="SCENARIO_TICKET_CREATED")
    return {"scenario": scenario, "label": label, "request_id": request["request_id"],
        "company_ticket": company_result["company_ticket"], "status": company_result["status"],
        "message": "Company ticket created. Click the explicit mock company approval control to execute synthetic data."}


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
    monitor_status = "AWAITING_COMPANY" if result.get("company_ticket") else "REVIEW_REQUIRED"
    monitoring_agent.update(request_id, monitor_status, company_ticket=result.get("company_ticket"), outcome=result.get("status", monitor_status))
    audit_agent.record(request_id=request_id, subject=request["customer_id"],
        agent="Deletion Request", action="COMPANY_REQUEST_SUBMITTED",
        outcome=result.get("status", "SUBMITTED"),
        item_count=len(discovery.get("items", [])), categories=request["selected_categories"])
    if not result.get("company_ticket") or result.get("not_submitted_categories"):
        ticket = human_review_agent.open_ticket(
            request_id, "POLICY_REVIEW",
            "Some selected categories require human policy review and were not included in the company deletion request: " + ", ".join(result.get("not_submitted_categories", request["selected_categories"])) + ".",
        )
        await event_bus.publish({"agent": "Monitoring", "status": "WARN", "request_id": request_id,
                                 "message": "Human review ticket " + ticket["ticket_id"] + " opened for policy review."})
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
    monitoring_agent.update(result["request_id"], "AWAITING_VERIFICATION", outcome="EXECUTED")
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
    matching = [item for item in tickets if item["request_id"] == request_id]
    ticket = matching[-1] if matching else None
    if ticket is None:
        raise HTTPException(status_code=404, detail="No company ticket exists.")
    result = await verification_agent.handle(request, ticket)
    monitoring_agent.update(request_id, result.get("status", "VERIFICATION_UNKNOWN"), outcome=result.get("status", "UNKNOWN"))
    audit_agent.record(request_id=request_id, subject=request["customer_id"],
        agent="Verification", action="INDEPENDENT_VERIFICATION",
        outcome=result.get("status", "UNKNOWN"),
        item_count=result.get("leftover_count") or 0, categories=request["selected_categories"])
    if result.get("status") == "LEFTOVERS_FOUND":
        ticket = human_review_agent.open_ticket(
            request_id, "VERIFICATION_LEFTOVERS",
            "Independent verification found remaining item IDs: " + ", ".join(result.get("leftover_item_ids", [])),
        )
        await event_bus.publish({"agent": "Monitoring", "status": "WARN", "request_id": request_id,
                                 "message": "Human review ticket " + ticket["ticket_id"] + " opened for verification leftovers."})
    return result


@app.post("/api/retry/{request_id}")
async def submit_bounded_retry(request_id: str):
    """Create a new company ticket for verified leftovers; never execute deletion."""
    request = get_request(request_id)
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{NOVAMART_API}/company/v1/erasure-requests")
        response.raise_for_status()
        all_tickets = response.json()["requests"]
        previous = [item for item in all_tickets if item["request_id"] == request_id]
        if not previous:
            raise HTTPException(status_code=404, detail="No company ticket exists for this request.")
        latest = previous[-1]
        if latest["execution"] != "EXECUTED":
            raise HTTPException(status_code=409, detail="The company must execute the latest ticket before a retry can be assessed.")
        scan_response = await client.post(
            f"{NOVAMART_API}/company/v1/discovery",
            json={"customer_id": request["customer_id"], "categories": latest["categories"]},
        )
        scan_response.raise_for_status()
        scan = scan_response.json()
        leftover_ids = sorted({item["item_id"] for item in scan.get("items", [])})
        if not leftover_ids:
            raise HTTPException(status_code=409, detail="No leftovers found; a retry is not needed.")
        budget = monitoring_agent.record_retry(request_id)
        if budget is None:
            raise HTTPException(status_code=404, detail="Monitoring record not found.")
        if budget["status"] == "RETRY_LIMIT_REACHED":
            ticket = human_review_agent.open_ticket(
                request_id, "RETRY_LIMIT",
                "Three company-approved retry submissions have been used and leftovers remain: " + ", ".join(leftover_ids),
            )
            monitoring_agent.update(request_id, "AWAITING_HUMAN", outcome="RETRY_LIMIT_REACHED")
            raise HTTPException(status_code=409, detail="Retry limit reached. Human-review ticket " + ticket["ticket_id"] + " opened.")
        attempt = budget["retry_count"]
        payload = {
            "request_id": request_id,
            "submission_id": f"{request_id}:retry:{attempt}",
            "attempt": attempt,
            "customer_id": request["customer_id"],
            "categories": latest["categories"],
            "discovered_item_ids": leftover_ids,
        }
        retry_response = await client.post(f"{NOVAMART_API}/company/v1/erasure-requests", json=payload)
        retry_response.raise_for_status()
        retry_ticket = retry_response.json()
    monitoring_agent.update(request_id, "AWAITING_COMPANY", company_ticket=retry_ticket["company_ticket"], outcome="RETRY_SUBMITTED")
    audit_agent.record(
        request_id=request_id, subject=request["customer_id"],
        agent="Deletion Request", action="BOUNDED_RETRY_SUBMITTED",
        outcome="PENDING_COMPANY_APPROVAL", item_count=len(leftover_ids),
        categories=latest["categories"],
    )
    await event_bus.publish({
        "agent": "Deletion Request", "status": "SUCCESS", "request_id": request_id,
        "message": f"Retry {attempt}/3 submitted to NovaMart as {retry_ticket['company_ticket']}; explicit company approval is still required.",
        "details": {"leftover_count": len(leftover_ids), "company_ticket": retry_ticket["company_ticket"]},
    })
    return {"retry_count": attempt, "max_retries": monitoring_agent.max_retries,
            "leftover_item_ids": leftover_ids, "company_ticket": retry_ticket["company_ticket"],
            "status": retry_ticket["status"],
            "message": "A new company request was submitted for leftovers only. No data was deleted."}



@app.get("/api/monitoring")
async def monitoring_snapshot():
    monitoring_agent.check_deadlines()
    return monitoring_agent.snapshot()

@app.post("/api/monitoring/check")
async def monitoring_check():
    alerts = monitoring_agent.check_deadlines()
    for alert in alerts:
        ticket = human_review_agent.open_ticket(alert["request_id"], "DEADLINE_BREACH", alert["alert"])
        await event_bus.publish({"agent": "Monitoring", "status": "WARN", "request_id": alert["request_id"], "message": alert["alert"] + " Ticket " + ticket["ticket_id"] + " opened."})
    return {"alerts": alerts, "snapshot": monitoring_agent.snapshot()}

@app.post("/api/monitoring/retry/{request_id}")
async def monitoring_retry(request_id: str):
    """Backward-compatible alias for the real bounded company retry workflow."""
    return await submit_bounded_retry(request_id)

class HumanTicketResolution(BaseModel):
    note: str = Field(min_length=3, max_length=500)


@app.get("/api/human-review")
async def human_review_tickets(status: str | None = None):
    if status and status not in {"OPEN", "RESOLVED"}:
        raise HTTPException(status_code=422, detail="Status must be OPEN or RESOLVED.")
    return {"tickets": human_review_agent.list_tickets(status)}


@app.post("/api/human-review/{ticket_id}/resolve")
async def resolve_human_review(ticket_id: str, payload: HumanTicketResolution):
    ticket = human_review_agent.resolve_ticket(ticket_id, payload.note.strip())
    if ticket is None:
        raise HTTPException(status_code=404, detail="Human-review ticket not found.")
    if ticket["status"] != "RESOLVED":
        raise HTTPException(status_code=409, detail="Ticket could not be resolved.")
    await event_bus.publish({"agent": "Monitoring", "status": "SUCCESS", "request_id": ticket["request_id"],
                             "message": "Human-review ticket " + ticket_id + " resolved: " + payload.note.strip()})
    return ticket


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


@app.post('/api/demo/reset')
async def reset_synthetic_demo():
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(NOVAMART_API + '/company/v1/demo/reset')
        response.raise_for_status()
    return {'status': 'reset', 'note': 'Synthetic demo records and company tickets reset.'}
