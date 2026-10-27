"""Human-review ticket register for the offline prototype."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class HumanReviewAgent:
    def __init__(self, db_path=None):
        self.db_path = Path(db_path or Path(__file__).resolve().parents[2] / "data" / "human_review.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS human_tickets (
                ticket_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                details TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                resolution_note TEXT,
                UNIQUE(request_id, reason)
            )""")

    def open_ticket(self, request_id, reason, details):
        now = datetime.now(timezone.utc).isoformat()
        ticket_id = "HR-" + uuid4().hex[:8].upper()
        with sqlite3.connect(self.db_path, timeout=10) as db:
            db.execute(
                "INSERT OR IGNORE INTO human_tickets "
                "(ticket_id,request_id,reason,details,status,created_at) "
                "VALUES (?,?,?,?,?,?)",
                (ticket_id, request_id, reason, details, "OPEN", now),
            )
            row = db.execute(
                "SELECT * FROM human_tickets WHERE request_id=? AND reason=?",
                (request_id, reason),
            ).fetchone()
        return self._as_dict(row)

    def resolve_ticket(self, ticket_id, note):
        with sqlite3.connect(self.db_path, timeout=10) as db:
            db.execute(
                "UPDATE human_tickets SET status='RESOLVED', resolved_at=?, resolution_note=? "
                "WHERE ticket_id=? AND status='OPEN'",
                (datetime.now(timezone.utc).isoformat(), note, ticket_id),
            )
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM human_tickets WHERE ticket_id=?", (ticket_id,)).fetchone()
        return dict(row) if row else None

    def list_tickets(self, status=None):
        with sqlite3.connect(self.db_path, timeout=10) as db:
            db.row_factory = sqlite3.Row
            if status:
                rows = db.execute("SELECT * FROM human_tickets WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
            else:
                rows = db.execute("SELECT * FROM human_tickets ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _as_dict(row):
        columns = ("ticket_id", "request_id", "reason", "details", "status", "created_at", "resolved_at", "resolution_note")
        return dict(zip(columns, row))
