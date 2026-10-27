import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.agents.intake import RULES


class MonitoringAgent:
    """Track request deadlines, status and bounded retry counts."""

    def __init__(self, db_path=None, deadline_days=None, max_retries=3):
        self.db_path = Path(db_path or Path(__file__).resolve().parents[2] / "data" / "monitoring.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.deadline_days = int(deadline_days if deadline_days is not None else RULES.get("default_deadline_days", 30))
        self.max_retries = max_retries
        with sqlite3.connect(self.db_path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS monitored_requests (request_id TEXT PRIMARY KEY, company_id TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, deadline_at TEXT NOT NULL, retry_count INTEGER NOT NULL DEFAULT 0, company_ticket TEXT, last_outcome TEXT NOT NULL DEFAULT 'RECEIVED', alert TEXT NOT NULL DEFAULT '')")
