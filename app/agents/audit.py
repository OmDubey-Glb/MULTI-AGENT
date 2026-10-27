import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class AuditAgent:
    """Privacy-minimized append-only hash-chain audit log."""

    def __init__(self, db_path=None, hmac_key=None):
        self.db_path = Path(db_path or Path(__file__).resolve().parents[2] / "data" / "audit.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        key = hmac_key or os.getenv("AUDIT_HMAC_KEY", "local-demo-only-change-before-deployment")
        self.key = key.encode("utf-8")
        with sqlite3.connect(self.db_path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS audit_events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, request_id TEXT NOT NULL, subject_hash TEXT NOT NULL, agent TEXT NOT NULL, action TEXT NOT NULL, outcome TEXT NOT NULL, item_count INTEGER NOT NULL, categories_json TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL)")

    def _subject_hash(self, subject):
        return hmac.new(self.key, subject.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def _hash(record):
        raw = json.dumps(record, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def record(self, *, request_id, subject, agent, action, outcome, item_count=0, categories=None):
        if item_count < 0:
            raise ValueError("item_count cannot be negative")
        timestamp = datetime.now(timezone.utc).isoformat()
        safe_categories = sorted(set(categories or []))
        with sqlite3.connect(self.db_path, timeout=10) as db:
            previous = db.execute("SELECT event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1").fetchone()
            previous_hash = previous[0] if previous else "GENESIS"
            record = {"timestamp": timestamp, "request_id": request_id,
                "subject_hash": self._subject_hash(subject), "agent": agent,
                "action": action, "outcome": outcome, "item_count": item_count,
                "categories": safe_categories, "previous_hash": previous_hash}
            event_hash = self._hash(record)
            cursor = db.execute("INSERT INTO audit_events (timestamp,request_id,subject_hash,agent,action,outcome,item_count,categories_json,previous_hash,event_hash) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (timestamp, request_id, record["subject_hash"], agent, action, outcome,
                 item_count, json.dumps(safe_categories), previous_hash, event_hash))
            record.update({"sequence": cursor.lastrowid, "event_hash": event_hash})
            return record

    def list_events(self, limit=100):
        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM audit_events ORDER BY sequence DESC LIMIT ?",
                              (max(1, min(limit, 500)),)).fetchall()
        events = []
        for row in rows:
            event = dict(row)
            event["categories"] = json.loads(event.pop("categories_json"))
            events.append(event)
        return events

    def verify_chain(self):
        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM audit_events ORDER BY sequence").fetchall()
        previous = "GENESIS"
        for row in rows:
            record = {"timestamp": row["timestamp"], "request_id": row["request_id"],
                "subject_hash": row["subject_hash"], "agent": row["agent"],
                "action": row["action"], "outcome": row["outcome"],
                "item_count": row["item_count"],
                "categories": json.loads(row["categories_json"]),
                "previous_hash": row["previous_hash"]}
            if row["previous_hash"] != previous or row["event_hash"] != self._hash(record):
                return {"valid": False, "checked": row["sequence"], "total": len(rows)}
            previous = row["event_hash"]
        return {"valid": True, "checked": len(rows), "total": len(rows)}
