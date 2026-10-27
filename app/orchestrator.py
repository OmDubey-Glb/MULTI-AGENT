from app.contracts.messages import AgentName
from app.core.events import event_bus

SPECIALISTS = [
    AgentName.INTAKE,
    AgentName.DISCOVERY,
    AgentName.DELETION,
    AgentName.VERIFICATION,
    AgentName.AUDIT,
    AgentName.MONITORING,
]


class Orchestrator:
    """Coordinates six specialists; it is not a seventh specialist agent."""

    def __init__(self) -> None:
        self.status = {agent.value: "IDLE" for agent in SPECIALISTS}

    def agent_status(self) -> list[dict[str, str]]:
        return [{"name": name, "status": status} for name, status in self.status.items()]

    async def publish_demo_event(self, agent: AgentName, status: str, message: str, request_id: str) -> None:
        self.status[agent.value] = status
        await event_bus.publish({
            "agent": agent.value,
            "status": status,
            "message": message,
            "request_id": request_id,
        })
