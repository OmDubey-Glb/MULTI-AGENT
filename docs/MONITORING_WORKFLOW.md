# Monitoring Agent workflow

The Monitoring Agent keeps a local SQLite register for each accepted erasure request. It stores the company ID, request status, creation time, configured deadline, retry count, optional company ticket, last outcome, and current alert.

## Deadline tracking

The deadline duration comes from `config/legal_rules.yaml` (`default_deadline_days`, currently 30 days for this illustrative demo). `GET /api/monitoring` returns the monitoring snapshot and checks for overdue requests. `POST /api/monitoring/check` explicitly checks deadlines and publishes alerts to the live event stream. A breached request is marked `DEADLINE_BREACHED` with a human-escalation alert. `VERIFIED`, `COMPLETED`, `COMPLETED_WITH_RETENTION`, and `CANCELLED` are treated as terminal.

## Retry budget

`POST /api/monitoring/retry/{request_id}` increments the request's retry counter. The third attempt (configurable in code) marks `RETRY_LIMIT_REACHED` and asks for human review. This endpoint records a retry-budget event; it does not itself re-submit a deletion request. The orchestrator must decide when a real retry is safe and authorized.

## Dashboard

The Monitoring & SLA Control panel displays tracked requests, company tickets, deadlines, pending-company count, deadline breaches, and retry-limit alerts.

## Demo and production boundaries

The monitor uses local SQLite and is intended for the offline hackathon prototype. It does not run a background scheduler; checks occur when monitoring endpoints are called. Production should use a durable shared task store, scheduled workers, authenticated operator actions, configured retention/deadline rules reviewed by counsel, and notification channels. The 30-day value is illustrative, not legal advice.


## Retry-budget safety clarification

The current `POST /api/monitoring/retry/{request_id}` endpoint records an attempt against the monitoring budget only. It does **not** submit another deletion request to NovaMart and does not delete data. The counter is hard-capped at the configured maximum (default 3); repeated calls after the cap leave the count unchanged and mark the request for human review. A future retry executor must create a new company-side request scoped only to verified leftovers and must preserve the company's approval step before execution.
