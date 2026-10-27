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
