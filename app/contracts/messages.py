from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentName(StrEnum):
    INTAKE = "Intake"
    DISCOVERY = "Discovery"
    DELETION = "Deletion Request"
    VERIFICATION = "Verification"
    AUDIT = "Audit"
    MONITORING = "Monitoring"
    ORCHESTRATOR = "Orchestrator"


class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    sender: AgentName
    recipient: AgentName
    message_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None


class AgentEvent(BaseModel):
    agent: AgentName
    status: str
    message: str
    request_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
