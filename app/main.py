import asyncio
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.core.events import event_bus
from app.orchestrator import Orchestrator

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="DPDP Erasure Orchestrator", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
orchestrator = Orchestrator()


@app.get("/")
async def dashboard():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "online", "service": "orchestrator", "specialist_agents": 6}


@app.get("/api/agents")
async def agents():
    return {"agents": orchestrator.agent_status()}


@app.get("/api/events")
async def events():
    async def stream():
        queue = event_bus.subscribe()
        try:
            yield "event: connected\\ndata: {}\\n\\n"
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {json.dumps(item)}\\n\\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\\n\\n"
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(stream(), media_type="text/event-stream")
