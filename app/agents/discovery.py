from __future__ import annotations

import httpx
from fastapi import HTTPException

from app.core.events import event_bus

NOVAMART_API = "http://127.0.0.1:9000"


class DiscoveryAgent:
    """Searches only company-authorized mock API and the request's selected scope."""

    async def handle(self, request: dict) -> dict:
        request_id = request["request_id"]
        categories = request["selected_categories"]
        await event_bus.publish({
            "agent": "Discovery", "status": "WORKING", "request_id": request_id,
            "message": f"Searching NovaMart for {len(categories)} selected categories only.",
        })
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{NOVAMART_API}/company/v1/discovery",
                    json={"customer_id": request["customer_id"], "categories": categories},
                )
                response.raise_for_status()
                result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            await event_bus.publish({
                "agent": "Discovery", "status": "ERROR", "request_id": request_id,
                "message": "NovaMart mock API is unavailable. Start the company service on port 9000.",
            })
            raise HTTPException(status_code=503, detail="NovaMart company API unavailable. Ensure port 9000 is running.") from exc

        await event_bus.publish({
            "agent": "Discovery", "status": "SUCCESS", "request_id": request_id,
            "message": f"Discovery complete: {result['count']} matching demo records found.",
            "details": {"count": result["count"], "categories": categories},
        })
        return result
