"""Company-side intake for deletion requests; no data is deleted here."""
from __future__ import annotations

from threading import Lock
from uuid import uuid4

_lock = Lock()
_requests: dict[str, dict] = {}


def create_erasure_request(payload: dict) -> dict:
    # submission_id makes each bounded retry a distinct, idempotent company ticket.
    submission_id = payload.get("submission_id") or payload["request_id"]
    with _lock:
        existing = _requests.get(submission_id)
        if existing:
            return dict(existing)
        company_ticket = "NM-" + uuid4().hex[:8].upper()
        record = {
            "company_ticket": company_ticket,
            "submission_id": submission_id,
            "request_id": payload["request_id"],
            "attempt": payload.get("attempt", 0),
            "scenario_mode": payload.get("scenario_mode", "normal"),
            "customer_id": payload["customer_id"],
            "categories": list(payload["categories"]),
            "discovered_item_ids": list(payload["discovered_item_ids"]),
            "status": "PENDING_COMPANY_APPROVAL",
            "execution": "NOT_EXECUTED",
            "message": "Request received by NovaMart. Authorized company staff must review and execute any approved deletion.",
        }
        _requests[submission_id] = record
        return dict(record)


def list_erasure_requests() -> list[dict]:
    with _lock:
        return [dict(item) for item in _requests.values()]


def get_erasure_request(company_ticket: str) -> dict | None:
    with _lock:
        item = next((r for r in _requests.values() if r["company_ticket"] == company_ticket), None)
        return dict(item) if item else None


def mark_executed(company_ticket: str, execution_result: dict) -> dict | None:
    with _lock:
        for item in _requests.values():
            if item["company_ticket"] == company_ticket:
                item["status"] = "COMPANY_EXECUTED"
                item["execution"] = "EXECUTED"
                item["execution_result"] = dict(execution_result)
                item["message"] = "NovaMart demo staff approved and executed this request against synthetic records."
                return dict(item)
    return None
