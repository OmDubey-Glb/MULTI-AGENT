from novamart_service import store


def seed_two_contact_copies(monkeypatch):
    monkeypatch.setattr(store, "_records", [
        {"customer_id": "CUST-X", "category": "contact_details", "system": "CRM", "item_id": "contact:x", "summary": "fake"},
        {"customer_id": "CUST-X", "category": "contact_details", "system": "EmailVendor", "item_id": "subscriber:x", "summary": "fake"},
    ])


def test_replica_lag_leaves_vendor_copy_then_retry_clears_it(monkeypatch):
    seed_two_contact_copies(monkeypatch)
    first = store.execute_approved_erasure(
        "CUST-X", ["contact_details"], ["contact:x", "subscriber:x"], "replica_lag", 0
    )
    assert first["removed_count"] == 1
    assert [row["item_id"] for row in store.discover("CUST-X", ["contact_details"])] == ["subscriber:x"]

    retry = store.execute_approved_erasure(
        "CUST-X", ["contact_details"], ["subscriber:x"], "replica_lag", 1
    )
    assert retry["removed_count"] == 1
    assert store.discover("CUST-X", ["contact_details"]) == []


def test_persistent_failure_preserves_requested_records(monkeypatch):
    seed_two_contact_copies(monkeypatch)
    result = store.execute_approved_erasure(
        "CUST-X", ["contact_details"], ["contact:x", "subscriber:x"], "persistent_failure", 2
    )
    assert result["removed_count"] == 0
    assert len(store.discover("CUST-X", ["contact_details"])) == 2
