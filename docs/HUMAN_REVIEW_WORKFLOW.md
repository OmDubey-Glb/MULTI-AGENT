# Human-review workflow

The human-review queue is an operational support service, not a seventh specialist agent. It stores review tickets in local SQLite and exposes them in the AgentOps dashboard.

## Automatic ticket reasons
- `POLICY_REVIEW`: selected categories excluded from a company deletion request by the illustrative demo policy.
- `VERIFICATION_LEFTOVERS`: independent verification found requested items still present.
- `RETRY_LIMIT`: monitoring retry budget exhausted.
- `DEADLINE_BREACH`: request passed its configured deadline.

Tickets are idempotent per request and reason.

## API
- `GET /api/human-review`: list all tickets.
- `GET /api/human-review?status=OPEN`: list open tickets.
- `GET /api/human-review?status=RESOLVED`: list resolved tickets.
- `POST /api/human-review/{ticket_id}/resolve`: record human review with a required note.

Resolving a ticket records review only. It does not delete data, approve a NovaMart request, or mark the erasure request complete. Company-side execution remains with authorized company staff.

## Prototype limitations
The queue uses local SQLite and the dashboard resolution action is unauthenticated. This is local-demo-only. Production requires authenticated staff, role-based access, durable storage, assignment/SLA controls, and company ticketing integration.
