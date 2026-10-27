from fastapi.testclient import TestClient

from novamart_service.main import app
from novamart_service.erasure import list_erasure_requests


client = TestClient(app)


def test_company_receives_request_without_executing_deletion():
    response = client.post("/company/v1/erasure-requests", json={
        "request_id": "ER-TEST000001",
        "customer_id": "CUST-1001",
        "categories": ["profile_identity"],
        "discovered_item_ids": ["profile:1001"],
    })
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PENDING_COMPANY_APPROVAL"
    assert body["execution"] == "NOT_EXECUTED"
    assert body["company_ticket"].startswith("NM-")


def test_company_request_is_idempotent():
    payload = {
        "request_id": "ER-TEST000002",
        "customer_id": "CUST-1001",
        "categories": ["contact_details"],
        "discovered_item_ids": ["contact:1001"],
    }
    first = client.post("/company/v1/erasure-requests", json=payload).json()
    second = client.post("/company/v1/erasure-requests", json=payload).json()
    assert first["company_ticket"] == second["company_ticket"]
    assert len([r for r in list_erasure_requests() if r["request_id"] == payload["request_id"]]) == 1


def test_retry_submission_gets_distinct_idempotent_company_ticket():
    payload = {
        "request_id": "ER-TEST000003",
        "submission_id": "ER-TEST000003:retry:1",
        "attempt": 1,
        "customer_id": "CUST-1001",
        "categories": ["contact_details"],
        "discovered_item_ids": ["contact:1001"],
    }
    first = client.post("/company/v1/erasure-requests", json=payload).json()
    second = client.post("/company/v1/erasure-requests", json=payload).json()
    assert first["company_ticket"] == second["company_ticket"]
    assert first["request_id"] == payload["request_id"]
    assert first["attempt"] == 1
    assert len([r for r in list_erasure_requests() if r["submission_id"] == payload["submission_id"]]) == 1


def test_retry_ticket_inherits_scenario_mode():
    initial = {
        "request_id": "ER-SCENARIO-0001",
        "customer_id": "CUST-1001",
        "categories": ["contact_details"],
        "discovered_item_ids": ["contact:1001"],
        "scenario_mode": "replica_lag",
    }
    first = client.post("/company/v1/erasure-requests", json=initial).json()
    retry = client.post("/company/v1/erasure-requests", json={
        **initial,
        "submission_id": "ER-SCENARIO-0001:retry:1",
        "attempt": 1,
        "discovered_item_ids": ["subscriber:1001"],
    }).json()
    assert first["scenario_mode"] == "replica_lag"
    assert retry["scenario_mode"] == "replica_lag"
