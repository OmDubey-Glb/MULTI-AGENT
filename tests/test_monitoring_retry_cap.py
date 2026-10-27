from app.agents.monitoring import MonitoringAgent


def test_retry_budget_is_hard_capped(tmp_path):
    agent = MonitoringAgent(tmp_path / "bounded.db", max_retries=2)
    agent.register("ER-BOUND", "novamart")
    agent.record_retry("ER-BOUND")
    capped = agent.record_retry("ER-BOUND")
    repeated = agent.record_retry("ER-BOUND")
    assert capped["retry_count"] == 2
    assert repeated["retry_count"] == 2
    assert repeated["status"] == "RETRY_LIMIT_REACHED"
