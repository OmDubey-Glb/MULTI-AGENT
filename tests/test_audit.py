import sqlite3

from app.agents.audit import AuditAgent


def test_audit_events_form_valid_hash_chain(tmp_path):
    agent = AuditAgent(tmp_path / "audit.db", hmac_key="test-secret")
    agent.record(request_id="ER-123", subject="CUST-1001", agent="Intake",
                 action="REQUEST_ACCEPTED", outcome="RECEIVED",
                 item_count=2, categories=["profile_identity", "contact_details"])
    agent.record(request_id="ER-123", subject="CUST-1001", agent="Discovery",
                 action="SCOPED_DISCOVERY", outcome="COMPLETED", item_count=1)
    assert agent.verify_chain() == {"valid": True, "checked": 2, "total": 2}


def test_audit_does_not_store_raw_subject_identifier(tmp_path):
    path = tmp_path / "audit.db"
    agent = AuditAgent(path, hmac_key="test-secret")
    agent.record(request_id="ER-123", subject="asha@example.com", agent="Intake",
                 action="REQUEST_ACCEPTED", outcome="RECEIVED")
    with sqlite3.connect(path) as db:
        stored = str(db.execute("SELECT * FROM audit_events").fetchone())
    assert "asha@example.com" not in stored


def test_tampering_is_detected(tmp_path):
    path = tmp_path / "audit.db"
    agent = AuditAgent(path, hmac_key="test-secret")
    agent.record(request_id="ER-123", subject="CUST-1001", agent="Intake",
                 action="REQUEST_ACCEPTED", outcome="RECEIVED")
    with sqlite3.connect(path) as db:
        db.execute("UPDATE audit_events SET outcome='ALTERED' WHERE sequence=1")
    assert agent.verify_chain()["valid"] is False
