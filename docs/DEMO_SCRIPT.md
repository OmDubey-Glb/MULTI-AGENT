# Demo script

All people and records are synthetic. Start with `python run.py` and open the local dashboard.

## Scenario A — Company-approved request
1. Use CUST-1001 (Asha Demo), select Personal profile and Email address.
2. Generate the offline OTP, read it in Dev Inbox, verify it, and submit.
3. Show Intake, Discovery and Deletion Request events.
4. Explain that NovaMart has a pending ticket; our agents have not deleted anything.
5. Click SIMULATE NOVAMART STAFF APPROVAL. Only the mock company service changes synthetic in-memory records.
6. Review independent verification, monitoring and audit status.

## Scenario B — Leftovers and bounded retry
1. When an approved category still contains records after company execution, verification reports LEFTOVERS_FOUND.
2. The dashboard offers a retry action. The orchestrator re-scans the latest approved categories and creates a new company ticket for leftover IDs only.
3. Approve the new ticket explicitly, then verify again.
4. Three retry submissions are permitted. A further retry attempt is refused and escalated to human review.

The current seed dataset normally clears on the first approval. A deterministic replica-lag/failure injector and one-click scenario launcher are not implemented; a leftover must be deliberately present in a test fixture for a live retry demonstration.

## Scenario C — Human escalation
1. Use a request with persistent leftovers and submit/approve three retries.
2. If leftovers remain, request another retry. The orchestrator refuses it and opens a RETRY_LIMIT ticket.
3. Review it in the Human Review Queue. Marking it reviewed does not delete data or approve a company ticket.
4. POST /api/monitoring/check evaluates deadlines and opens DEADLINE_BREACH tickets for overdue nonterminal requests.

A simulated clock, deterministic repeated-failure mode, and one-click A/B/C controls remain future work. Do not claim these are automated in the current build.

## Judge talking points
- Six specialist agents coordinate through the orchestrator.
- The Deletion Request Agent submits requests; NovaMart remains responsible for approval and execution.
- Each retry is a new idempotent company ticket for leftover IDs only.
- Verification scans the full approved category scope.
- OTP delivery, company systems, records and approvals are offline simulations, not production integrations.
