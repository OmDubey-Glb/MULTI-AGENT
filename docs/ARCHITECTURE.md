# Architecture

## Trust boundary
The orchestrator coordinates work. The Deletion Request Agent prepares and submits requests only through an explicitly authorized company interface. A separate fictional NovaMart service will represent the company's own system and mutate generated demo records only.

## Components
- FastAPI application: dashboard, health, agent status, and SSE endpoints.
- Orchestrator: coordinates six specialist agents and workflow progression.
- Shared Pydantic contracts: typed agent messages and events.
- In-process asynchronous event bus: distributes events to agent/UI subscribers.
- Browser dashboard: visualizes agent state and the event stream.

## Planned workflow
Intake -> Discovery -> Deletion Request -> Verification -> Audit -> Monitoring. Verification failures can route a bounded retry to Deletion Request. After the retry limit, escalate to a human. Legitimate retention and immutable-backup tickets remain visible rather than being silently marked deleted.

## Privacy
Do not place raw identifiers, OTP values, or document contents in audit events. The offline demo OTP inbox is not proof of real-world contact ownership.
