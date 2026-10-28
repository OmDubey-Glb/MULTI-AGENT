from __future__ import annotations

import hashlib
import secrets
import time
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

CONFIG = Path(__file__).resolve().parents[2] / "config" / "legal_rules.yaml"
RULES = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
CATEGORIES = RULES.get("categories", {})
OTP_TTL_SECONDS = 300
MAX_OTP_ATTEMPTS = 3
RESEND_COOLDOWN_SECONDS = 30

# In-memory state is intentional for the offline hackathon prototype.
# Replace with persistent, encrypted storage and a delivery provider in production.
_sessions: dict[str, dict] = {}
_dev_inbox: list[dict] = []
_requests: dict[str, dict] = {}


class OtpStart(BaseModel):
    company_id: Literal["novamart"] = "novamart"
    customer_id: str = Field(min_length=3, max_length=64)
    channel: Literal["email", "mobile"]
    destination: str = Field(min_length=5, max_length=254)

    @field_validator("destination")
    @classmethod
    def no_control_chars(cls, value: str) -> str:
        if any(ord(ch) < 32 for ch in value):
            raise ValueError("Destination contains invalid characters")
        return value.strip()


class OtpVerify(BaseModel):
    session_id: str
    code: str = Field(pattern=r"^\d{6}$")


class RequestSubmit(BaseModel):
    session_id: str
    categories: list[str] = Field(min_length=1, max_length=13)


def catalog() -> dict:
    return {
        "company": {"id": "novamart", "name": "NovaMart"},
        "categories": [
            {"id": key, "label": value.get("label", key), "action": value.get("demo_action", "REVIEW"), "reason": value.get("retention_note", "Available for an erasure request; NovaMart will assess the selected scope.")}
            for key, value in CATEGORIES.items()
        ],
    }


def start_otp(data: OtpStart) -> dict:
    now = time.time()
    recent = [
        session for session in _sessions.values()
        if session["customer_id"] == data.customer_id
        and session["channel"] == data.channel
        and now - session["created_at"] < RESEND_COOLDOWN_SECONDS
    ]
    if recent:
        raise HTTPException(status_code=429, detail="Please wait 30 seconds before requesting another OTP.")

    session_id = str(uuid4())
    code = f"{secrets.randbelow(1_000_000):06d}"
    _sessions[session_id] = {
        "customer_id": data.customer_id,
        "company_id": data.company_id,
        "channel": data.channel,
        "destination": data.destination,
        "code_hash": hashlib.sha256(code.encode()).hexdigest(),
        "created_at": now,
        "expires_at": now + OTP_TTL_SECONDS,
        "attempts": 0,
        "verified": False,
    }
    _dev_inbox.append({
        "session_id": session_id,
        "channel": data.channel,
        "destination": data.destination,
        "code": code,
        "created_at": now,
    })
    return {"session_id": session_id, "expires_in_seconds": OTP_TTL_SECONDS,
            "delivery": "OFFLINE_DEV_INBOX", "message": "Demo OTP generated. Open the Dev Inbox to view it."}


def verify_otp(data: OtpVerify) -> dict:
    session = _sessions.get(data.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="OTP session not found.")
    if time.time() > session["expires_at"]:
        raise HTTPException(status_code=410, detail="OTP expired. Request a new code.")
    if session["attempts"] >= MAX_OTP_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Maximum OTP attempts reached.")
    session["attempts"] += 1
    supplied = hashlib.sha256(data.code.encode()).hexdigest()
    if not secrets.compare_digest(supplied, session["code_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect OTP.")
    session["verified"] = True
    session["code_hash"] = ""
    return {"verified": True, "message": "Identity verification completed for this demo session."}


def submit_request(data: RequestSubmit) -> dict:
    session = _sessions.get(data.session_id)
    if not session or not session.get("verified"):
        raise HTTPException(status_code=403, detail="Verify the OTP before submitting a request.")
    if session.get("consumed"):
        raise HTTPException(status_code=409, detail="This verified session has already submitted a request.")
    if time.time() > session["expires_at"]:
        raise HTTPException(status_code=410, detail="Verification session expired.")
    selected = list(dict.fromkeys(data.categories))
    if not selected or any(category not in CATEGORIES for category in selected):
        raise HTTPException(status_code=422, detail="Choose valid categories from the NovaMart catalog.")

    request_id = "ER-" + uuid4().hex[:10].upper()
    assessment = {
        category: CATEGORIES[category].get("demo_action", "REVIEW")
        for category in selected
    }
    record = {
        "request_id": request_id,
        "company_id": session["company_id"],
        "customer_id": session["customer_id"],
        "verification_method": session["channel"],
        "selected_categories": selected,
        "policy_assessment": assessment,
        "status": "RECEIVED",
        "note": "Demo policy assessment only; company systems must authorize and execute any deletion.",
    }
    _requests[request_id] = record
    session["consumed"] = True
    return record


def inbox() -> list[dict]:
    # Only the local demo UI can inspect this development inbox.
    return list(reversed(_dev_inbox[-20:]))


def list_requests() -> list[dict]:
    return list(_requests.values())


def create_demo_request(customer_id: str, categories: list[str], scenario_label: str) -> dict:
    """Create a clearly synthetic, OTP-bypassing request for the local scenario launcher only."""
    selected = list(dict.fromkeys(categories))
    if not selected or any(category not in CATEGORIES for category in selected):
        raise ValueError("Invalid demo categories.")
    request_id = "ER-DEMO-" + uuid4().hex[:8].upper()
    record = {
        "request_id": request_id,
        "company_id": "novamart",
        "customer_id": customer_id,
        "verification_method": "DEMO_SCENARIO",
        "selected_categories": selected,
        "policy_assessment": {category: CATEGORIES[category].get("demo_action", "REVIEW") for category in selected},
        "status": "RECEIVED",
        "demo_scenario": scenario_label,
        "note": "Synthetic scenario launcher only; not an identity-verified user request.",
    }
    _requests[request_id] = record
    return record
