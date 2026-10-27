from fastapi.testclient import TestClient

from novamart_service.main import app


client = TestClient(app)


def test_discovery_returns_only_selected_categories():
    response = client.post("/company/v1/discovery", json={
        "customer_id": "CUST-1001",
        "categories": ["profile_identity"],
    })
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert {item["category"] for item in body["items"]} == {"profile_identity"}


def test_discovery_does_not_return_other_customers():
    response = client.post("/company/v1/discovery", json={
        "customer_id": "CUST-1002",
        "categories": ["contact_details"],
    })
    assert response.status_code == 200
    assert all(item["customer_id"] == "CUST-1002" for item in response.json()["items"])
