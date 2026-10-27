from __future__ import annotations

import httpx
from fastapi import HTTPException

from app.core.events import event_bus

NOVAMART_API = "http://127.0.0.1:9000"


class DeletionRequestAgent:
    """Submits an authorized request to the company; never deletes company data."""

    async def handle(self, request: dict, discovery: dict) -> dict:
        request_id = request["request_id"]
        policy = request["policy_assessment"]
        eligible = [category for category in request["selected_categories"]
                    if policy.get(category) == "DELETE"]
        if not eligible:
            await event_bus.publish({
                "agent": "Deletion Request", "status": "WARN", "request_id": request_id,
                "message": "No selected category has a DELETE demo assessment. No company deletion request was submitted.",
            })
            return {
                "status": "NO_DELETION_REQUEST",
                "company_ticket": None,
                "requested_categories": [],
                "not_submitted_categories": request["selected_categories"],
                "execution": "NOT_EXECUTED",
            }

        allowed_items = [
            item["item_id"] for item in discovery.get("items", [])
            if item.get("category") in eligible
        ]
        await event_bus.publish({
            "agent": "Deletion Request", "status": "WORKING", "request_id": request_id,
            "message": f"Preparing a NovaMart company request for {len(eligible)} eligible selected categories.",
        })
        payload = {
            "request_id": request_id,
            "customer_id": request["customer_id"],
            "categories": eligible,
            "discovered_item_ids": allowed_items,
            "scenario_mode": request.get("scenario_mode", "normal"),
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(f"{NOVAMART_API}/company/v1/erasure-requests", json=payload)
                response.raise_for_status()
                result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            await event_bus.publish({
                "agent": "Deletion Request", "status": "ERROR", "request_id": request_id,
                "message": "Could not submit the request to NovaMart. No data was deleted.",
            })
            raise HTTPException(status_code=503, detail="NovaMart company API unavailable for deletion-request submission.") from exc

        await event_bus.publish({
            "agent": "Deletion Request", "status": "SUCCESS", "request_id": request_id,
            "message": f"NovaMart received company ticket {result['company_ticket']}. Awaiting company approval; no deletion executed.",
            "details": {"company_ticket": result["company_ticket"], "status": result["status"]},
        })
        return {
            **result,
            "requested_categories": eligible,
            "not_submitted_categories": [
                category for category in request["selected_categories"] if category not in eligible
            ],
        }
