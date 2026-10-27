from fastapi import FastAPI
from pydantic import BaseModel, Field

from novamart_service.erasure import create_erasure_request, list_erasure_requests
from novamart_service.store import discover, seed_demo_records

app = FastAPI(title="NovaMart Mock Company API", version="0.2.0")


class DiscoveryQuery(BaseModel):
    customer_id: str = Field(min_length=3, max_length=64)
    categories: list[str] = Field(min_length=1, max_length=10)


class CompanyErasureRequest(BaseModel):
    request_id: str = Field(min_length=5, max_length=64)
    customer_id: str = Field(min_length=3, max_length=64)
    categories: list[str] = Field(min_length=1, max_length=10)
    discovered_item_ids: list[str] = Field(default_factory=list, max_length=100)


@app.on_event("startup")
def startup() -> None:
    seed_demo_records()


@app.get("/health")
def health():
    return {"status": "online", "service": "novamart-mock", "data": "synthetic-only"}


@app.post("/company/v1/discovery")
def discovery(payload: DiscoveryQuery):
    allowed = {"profile_identity", "contact_details", "order_history", "invoices"}
    if any(category not in allowed for category in payload.categories):
        return {"status": "rejected", "reason": "Unknown category", "items": []}
    items = discover(payload.customer_id, payload.categories)
    return {
        "status": "completed",
        "company": "NovaMart",
        "customer_id": payload.customer_id,
        "searched_categories": payload.categories,
        "items": items,
        "count": len(items),
        "note": "Synthetic demo records only. This endpoint does not delete or modify data.",
    }


@app.post("/company/v1/erasure-requests")
def receive_erasure_request(payload: CompanyErasureRequest):
    allowed = {"profile_identity", "contact_details", "order_history", "invoices"}
    if any(category not in allowed for category in payload.categories):
        return {"status": "rejected", "reason": "Unknown category"}
    return create_erasure_request(payload.model_dump())


@app.get("/company/v1/erasure-requests")
def company_erasure_requests():
    return {"requests": list_erasure_requests()}
