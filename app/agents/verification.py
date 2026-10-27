from __future__ import annotations

import httpx
from app.core.events import event_bus

NOVAMART_API = "http://127.0.0.1:9000"


class VerificationAgent:
    """Independently checks the company-reported result."""

    async def handle(self, request: dict, ticket: dict) -> dict:
        request_id = request["request_id"]
        if ticket["execution"] != "EXECUTED":
            result = {"status": "WAITING_FOR_COMPANY", "leftover_count": None, "leftover_item_ids": [], "message": "Company has not confirmed execution; verification cannot claim success."}
            await event_bus.publish({"agent": "Verification", "status": "WARN", "request_id": request_id, "message": result["message"]})
            return result
        await event_bus.publish({"agent": "Verification", "status": "WORKING", "request_id": request_id, "message": "Independently re-scanning the exact company ticket scope."})
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{NOVAMART_API}/company/v1/discovery", json={"customer_id": ticket["customer_id"], "categories": ticket["categories"]})
            response.raise_for_status()
            scan = response.json()
        expected = set(ticket["discovered_item_ids"])
        leftovers = sorted(item["item_id"] for item in scan.get("items", []) if item["item_id"] in expected)
        verified = not leftovers
        result = {"status": "VERIFIED" if verified else "LEFTOVERS_FOUND", "leftover_count": len(leftovers), "leftover_item_ids": leftovers, "checked_categories": ticket["categories"], "message": "Independent scan found none of the requested items remaining." if verified else "Independent scan found requested items still present; escalation or a bounded retry is required."}
        await event_bus.publish({"agent": "Verification", "status": "SUCCESS" if verified else "WARN", "request_id": request_id, "message": result["message"], "details": {"leftover_count": len(leftovers)}})
        return result
