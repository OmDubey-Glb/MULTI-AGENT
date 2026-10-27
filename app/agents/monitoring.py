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

    def register(self, request_id, company_id, now=None):
        current = now or datetime.now(timezone.utc)
        deadline = current + timedelta(days=self.deadline_days)
        with sqlite3.connect(self.db_path, timeout=10) as db:
            db.execute("INSERT OR IGNORE INTO monitored_requests (request_id,company_id,status,created_at,deadline_at) VALUES (?,?,'RECEIVED',?,?)",
                       (request_id, company_id, current.isoformat(), deadline.isoformat()))
        return self.get(request_id)

    def update(self, request_id, status, company_ticket=None, outcome=None):
        with sqlite3.connect(self.db_path, timeout=10) as db:
            db.execute("UPDATE monitored_requests SET status=?, company_ticket=COALESCE(?,company_ticket), last_outcome=COALESCE(?,last_outcome), alert='' WHERE request_id=?",
                       (status, company_ticket, outcome, request_id))
        return self.get(request_id)

    def record_retry(self, request_id):
        with sqlite3.connect(self.db_path, timeout=10) as db:
            row = db.execute("SELECT retry_count FROM monitored_requests WHERE request_id=?", (request_id,)).fetchone()
            if not row:
                return None
            # Never let repeated UI/API calls exceed the configured retry budget.
            if row[0] >= self.max_retries:
                return self.get(request_id)
            count = row[0] + 1
            status = "RETRY_LIMIT_REACHED" if count >= self.max_retries else "RETRY_BUDGET_RECORDED"
            alert = "Maximum retry budget reached; human review required." if count >= self.max_retries else "Retry budget recorded only; no company request was resubmitted."
            db.execute("UPDATE monitored_requests SET retry_count=?,status=?,alert=? WHERE request_id=?",
                       (count, status, alert, request_id))
        return self.get(request_id)

    def check_deadlines(self, now=None):
        current = now or datetime.now(timezone.utc)
        alerts = []
        with sqlite3.connect(self.db_path, timeout=10) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM monitored_requests").fetchall()
            for row in rows:
                terminal = row["status"] in {"COMPLETED", "COMPLETED_WITH_RETENTION", "VERIFIED", "CANCELLED"}
                if not terminal and datetime.fromisoformat(row["deadline_at"]) <= current:
                    alert = "Deadline breached; prepare human escalation."
                    db.execute("UPDATE monitored_requests SET status='DEADLINE_BREACHED',alert=? WHERE request_id=?",
                               (alert, row["request_id"]))
                    alerts.append({"request_id": row["request_id"], "status": "DEADLINE_BREACHED", "alert": alert})
        return alerts

    def get(self, request_id):
        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM monitored_requests WHERE request_id=?", (request_id,)).fetchone()
        return dict(row) if row else None

    def list_requests(self):
        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM monitored_requests ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

    def snapshot(self):
        items = self.list_requests()
        return {"requests": items, "total": len(items),
                "overdue": sum(x["status"] == "DEADLINE_BREACHED" for x in items),
                "retry_limit_reached": sum(x["status"] == "RETRY_LIMIT_REACHED" for x in items),
                "pending_company": sum(x["status"] in {"RECEIVED", "COMPANY_REQUEST_PENDING", "AWAITING_COMPANY"} for x in items),
                "max_retries": self.max_retries, "deadline_days": self.deadline_days}
