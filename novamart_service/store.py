"""Generated fictional NovaMart records for the local demo only."""
from __future__ import annotations

from copy import deepcopy
from threading import Lock

_lock = Lock()
_records: list[dict] = []
_scenario_modes: dict[str, str] = {}


def seed_demo_records() -> None:
    """Create a small synthetic data set; never reads real company systems."""
    with _lock:
        if _records:
            return
        examples = [
            ("CUST-1001", "profile_identity", "CRM", "profile:1001", "Asha Demo"),
            ("CUST-1001", "contact_details", "CRM", "contact:1001", "asha@example.com"),
            ("CUST-1001", "contact_details", "EmailVendor", "subscriber:1001", "asha@example.com"),
            ("CUST-1001", "order_history", "OrdersDB", "orders:1001", "3 fictional orders"),
            ("CUST-1001", "invoices", "BillingDB", "invoice:1001", "2 fictional invoices"),
            ("CUST-1002", "profile_identity", "CRM", "profile:1002", "Rohan Demo"),
            ("CUST-1002", "contact_details", "CRM", "contact:1002", "rohan@example.com"),
        ]
        for customer_id, category, system, item_id, summary in examples:
            _records.append({
                "customer_id": customer_id,
                "category": category,
                "system": system,
                "item_id": item_id,
                "summary": summary,
            })


def discover(customer_id: str, categories: list[str]) -> list[dict]:
    seed_demo_records()
    with _lock:
        return deepcopy([
            row for row in _records
            if row["customer_id"].casefold() == customer_id.casefold()
            and row["category"] in categories
        ])


def execute_approved_erasure(customer_id: str, categories: list[str], item_ids: list[str], scenario_mode: str = "normal", attempt: int = 0) -> dict:
    """Company-side execution against synthetic in-memory records only, with deterministic demo fault injection."""
    seed_demo_records()
    allowed_ids = set(item_ids)
    allowed_categories = set(categories)
    # Replica lag: first execution leaves the EmailVendor copy behind; retry clears it.
    # Persistent failure: every approved attempt leaves the requested records in place.
    preserve_ids = set()
    if scenario_mode == "persistent_failure":
        preserve_ids = allowed_ids
    elif scenario_mode == "replica_lag" and attempt == 0:
        with _lock:
            preserve_ids = {row["item_id"] for row in _records
                            if row["customer_id"].casefold() == customer_id.casefold()
                            and row["category"] in allowed_categories
                            and row["item_id"] in allowed_ids
                and row["item_id"] not in preserve_ids
                            and row["system"] == "EmailVendor"}
    with _lock:
        before = len(_records)
        _records[:] = [
            row for row in _records
            if not (
                row["customer_id"].casefold() == customer_id.casefold()
                and row["category"] in allowed_categories
                and row["item_id"] in allowed_ids
                and row["item_id"] not in preserve_ids
            )
        ]
        removed = before - len(_records)
    return {"removed_count": removed, "executed_item_ids": sorted(allowed_ids), "preserved_item_ids": sorted(preserve_ids), "scenario_mode": scenario_mode, "attempt": attempt}


def reset_demo_records():
    with _lock:
        _records.clear()
    seed_demo_records()
