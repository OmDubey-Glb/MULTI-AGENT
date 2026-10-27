from app.agents.human_review import HumanReviewAgent


def test_ticket_is_idempotent_and_resolvable(tmp_path):
    agent = HumanReviewAgent(tmp_path / "human.db")
    first = agent.open_ticket("ER-100", "POLICY_REVIEW", "Needs manual review")
    second = agent.open_ticket("ER-100", "POLICY_REVIEW", "Needs manual review")
    assert first["ticket_id"] == second["ticket_id"]
    assert first["status"] == "OPEN"
    resolved = agent.resolve_ticket(first["ticket_id"], "Reviewed by operator")
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolution_note"] == "Reviewed by operator"


def test_distinct_reasons_create_distinct_tickets(tmp_path):
    agent = HumanReviewAgent(tmp_path / "human.db")
    policy = agent.open_ticket("ER-101", "POLICY_REVIEW", "Policy")
    backup = agent.open_ticket("ER-101", "BACKUP_REVIEW", "Backup")
    assert policy["ticket_id"] != backup["ticket_id"]
    assert len(agent.list_tickets("OPEN")) == 2
