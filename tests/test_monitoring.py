from datetime import datetime, timedelta, timezone

from app.agents.monitoring import MonitoringAgent


def test_retry_limit_escalates(tmp_path):
    agent = MonitoringAgent(tmp_path / "monitor.db", max_retries=3)
    agent.register("ER-1", "novamart")
    agent.record_retry("ER-1")
    agent.record_retry("ER-1")
    result = agent.record_retry("ER-1")
    assert result["status"] == "RETRY_LIMIT_REACHED"
    assert result["retry_count"] == 3


def test_deadline_breach_and_terminal_state(tmp_path):
    agent = MonitoringAgent(tmp_path / "monitor.db", deadline_days=1)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    agent.register("ER-2", "novamart", now=now)
    agent.register("ER-3", "novamart", now=now)
    agent.update("ER-3", "VERIFIED")
    alerts = agent.check_deadlines(now=now + timedelta(days=2))
    assert [item["request_id"] for item in alerts] == ["ER-2"]
