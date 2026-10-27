import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.agents.discovery import DiscoveryAgent
from app.agents.intake import (
    OtpStart, OtpVerify, RequestSubmit, catalog, inbox, list_requests,
    start_otp, submit_request, verify_otp,
)
from app.core.events import event_bus
from app.orchestrator import Orchestrator

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="DPDP Erasure Orchestrator", version="0.3.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
orchestrator = Orchestrator()
discovery_agent = DiscoveryAgent()


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
    await event_bus.publish({"agent": "Intake", "status": "SUCCESS",
                             "request_id": result["request_id"],
                             "message": f"Intake accepted {len(result['selected_categories'])} selected data categories."})
    await event_bus.publish({"agent": "Orchestrator", "status": "INFO",
                             "request_id": result["request_id"],
                             "message": "Request registered. Starting scoped discovery against NovaMart's authorized demo API."})
    return result


@app.post("/api/discovery/{request_id}")
async def run_discovery(request_id: str):
    request = next((item for item in list_requests() if item["request_id"] == request_id), None)
    if request is None:
        raise HTTPException(status_code=404, detail="Erasure request not found.")
    return await discovery_agent.handle(request)


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
