from abc import ABC, abstractmethod

from app.contracts.messages import AgentName
from app.core.events import event_bus


class BaseAgent(ABC):
    name: AgentName

    async def emit(self, status: str, message: str, request_id: str | None = None, **details) -> None:
        await event_bus.publish({
            "agent": self.name.value,
            "status": status,
            "message": message,
            "request_id": request_id,
            "details": details,
        })

    @abstractmethod
    async def handle(self, message):
        raise NotImplementedError
