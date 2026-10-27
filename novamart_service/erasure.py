"""Company-side intake for deletion requests; no data is deleted here."""
from __future__ import annotations

from threading import Lock
from uuid import uuid4

_lock = Lock()
_requests: dict[str, dict] = {}


def create_erasure_request(payload: dict) -> dict:
    with _lock:
        existing = _requests.get(payload["request_id"])
        if existing:
            return dict(existing)
        company_ticket = "NM-" + uuid4().hex[:8].upper()
        record = {
            "company_ticket": company_ticket,
            "request_id": payload["request_id"],
            "customer_id": payload["customer_id"],
            "categories": list(payload["categories"]),
            "discovered_item_ids": list(payload["discovered_item_ids"]),
            "status": "PENDING_COMPANY_APPROVAL",
            "execution": "NOT_EXECUTED",
            "message": "Request received by NovaMart. Authorized company staff must review and execute any approved deletion.",
        }
        _requests[payload["request_id"]] = record
        return dict(record)


def list_erasure_requests() -> list[dict]:
    with _lock:
        return [dict(item) for item in _requests.values()]
