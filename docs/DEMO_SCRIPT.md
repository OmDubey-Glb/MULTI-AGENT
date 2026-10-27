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


## 4-minute presenter script

### 0:00–0:40 — Problem and trust boundary
"Personal data is often spread across a company's CRM, vendor tools, and other systems. A request needs more than a chatbot response: it needs discovery, company-side action, verification, audit, and follow-up. Our system coordinates those steps. It does not take control of a real company's servers. The company remains responsible for approving and executing deletion."

### 0:40–1:20 — Architecture
"Here are our six specialist agents. Intake scopes and validates the request. Discovery finds matching records. Deletion Request submits a ticket to the company. Verification checks the result independently. Audit records a privacy-minimized trail. Monitoring tracks deadlines, retries, and escalation. The orchestrator coordinates them."

### 1:20–2:10 — Scenario A
"First, the happy path. I launch Scenario A. The system creates a synthetic request and discovers matching records. Now I act as the fictional company's staff member and approve the ticket. Notice that the company simulator—not the agent—executes the change. Verification performs a fresh scan and should report zero leftovers."

### 2:10–3:00 — Scenario B
"Now I demonstrate a realistic failure mode: replica lag. The first company approval intentionally leaves one EmailVendor copy. Verification catches that leftover instead of trusting the initial success response. The orchestrator creates a bounded retry for the leftover item only. I approve the new company ticket, and verification should pass."

### 3:00–3:40 — Scenario C and audit
"Scenario C keeps the synthetic records in place to demonstrate repeated failure. Each retry is bounded and requires a fresh company approval. When the retry budget is exhausted, the system opens a human-review ticket instead of looping forever. The audit panel shows the recorded workflow trail."

### 3:40–4:00 — Close
"Our key contribution is controlled coordination: preserve the user's scope, request company-authorized action, verify independently, record evidence, and escalate when automation should stop. This is an offline prototype with synthetic data; real deployment needs company integrations, production identity verification, security controls, and legal review."

## Rehearsal checklist

- [ ] Install dependencies and start with `python run.py`.
- [ ] Confirm the dashboard loads at port 8000 and NovaMart health is available on port 9000.
- [ ] Rehearse A, B, and C once before presenting.
- [ ] Keep the Human Review Queue and Audit panel visible for Scenario C.
- [ ] Explain that scenario launchers bypass OTP intentionally; do not describe them as identity-verified requests.
- [ ] State clearly that NovaMart is fictional and all records are synthetic.
- [ ] Do not claim production DPDP compliance, real SMS/email delivery, or real company integration.
