# Deterministic A/B/C demo

Run `python run.py`, open the local dashboard, and use the **DEMO SCENARIOS** buttons. Each run resets only generated NovaMart in-memory records and company tickets. The scenario launcher intentionally bypasses OTP; it is a local judge-demo harness, not an identity-verified request.

## A — Happy path
1. Click **A · HAPPY PATH**.
2. Click **SIMULATE COMPANY STAFF APPROVAL**.
3. The mock company service removes the synthetic contact records.
4. Independent verification should return `VERIFIED` with zero leftovers.

## B — Replica lag and retry
1. Click **B · REPLICA LAG** and approve the initial company ticket.
2. The mock execution removes the CRM copy but leaves the EmailVendor copy on attempt zero.
3. Verification reports `LEFTOVERS_FOUND`. Submit the bounded retry.
4. Approve the new company ticket. Attempt one clears the lagging copy.
5. Verification should return `VERIFIED`.

## C — Persistent failure and escalation
1. Click **C · FAILURE** and approve the initial company ticket.
2. The simulator preserves the requested records after every company approval.
3. Submit and approve three bounded retries.
4. Submit another retry. It is refused and opens a `RETRY_LIMIT` human-review ticket.
5. Inspect it in the Human Review Queue. Marking it reviewed does not delete data or approve a company ticket.

## Judge talking points
- Six specialist agents coordinate through the orchestrator.
- The Deletion Request Agent submits requests; NovaMart remains responsible for approval and execution.
- Each retry is a new idempotent company ticket for leftover IDs only and needs fresh company approval.
- Verification scans the full approved category scope.
- All data and fault modes are synthetic and in-memory. The scenario launcher bypasses OTP only for these demo scenarios; the normal intake path demonstrates OTP.
- There is no real NovaMart integration, email/SMS delivery, production identity verification, or production deletion.
