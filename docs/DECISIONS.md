# Architecture Decision Records

These records explain the main design choices in the current hackathon prototype.

## ADR-001: Company remains responsible for deletion execution

**Decision:** The Deletion Request Agent submits a scoped request to a company-authorized interface. It does not directly delete arbitrary company production data.

**Reason:** The company owns and controls its systems. A coordinator should not pretend it has authority to mutate third-party infrastructure.

**Implementation:** The fictional NovaMart API issues tickets and performs simulated execution only after an explicit demo approval action.

**Trade-off:** The demo needs a separate company simulator and approval step, but the trust boundary is visible and safer.

## ADR-002: Six specialist agents plus one orchestrator

**Decision:** Keep six specialist agents: Intake, Discovery, Deletion Request, Verification, Audit, and Monitoring. The orchestrator coordinates them and is not a seventh specialist.

**Reason:** Clear responsibilities make hand-offs and outcomes understandable to judges and maintainers.

## ADR-003: Preserve the user's selected categories

**Decision:** The chosen category IDs remain the scope across discovery, company submission, retries, and verification. A retry narrows to discovered leftover item IDs but does not silently add categories.

**Reason:** Prevent scope expansion and make the request auditable.

## ADR-004: Use a fictional offline company service

**Decision:** Use a separate FastAPI NovaMart service on port 9000 with generated synthetic records.

**Reason:** Demonstrate company-side authorization and execution without connecting to real company systems, requiring API keys, or risking real personal data.

**Trade-off:** State is in-memory and resets on process restart. It is a simulator, not a production integration.

## ADR-005: Deterministic workflow and fault injection

**Decision:** Implement predictable A/B/C scenarios: normal completion, replica lag, and persistent failure.

**Reason:** Judges can see a successful path, a feedback-driven retry, and a bounded failure/escalation path in a short demo.

**Trade-off:** These scenario modes are test fixtures, not machine-learning predictions or real infrastructure failures.

## ADR-006: Independent verification and bounded retries

**Decision:** Verification performs a fresh scoped discovery after company execution. Leftovers can trigger up to three new company request submissions; every new ticket requires explicit company approval.

**Reason:** A success response alone is insufficient evidence that all scoped copies disappeared. A retry cap prevents endless loops.

## ADR-007: Privacy-minimized hash-chain audit

**Decision:** Store workflow metadata and a keyed subject hash rather than raw contact identifiers in the audit table. Link entries using a SHA-256 hash chain.

**Reason:** Support traceability while reducing sensitive data copied into audit records.

**Limit:** A hash chain is tamper-evident for ordinary row edits, not an absolute defense against a privileged administrator rewriting the entire database.

## ADR-008: Offline demo OTP

**Decision:** Display generated OTPs in a local Dev Inbox rather than sending real email or SMS.

**Reason:** Keep the hackathon demo offline, reproducible, and free of external credentials.

**Limit:** This does not establish real-world identity or contact ownership and must be replaced before production.

## ADR-009: Explicit human review

**Decision:** Unresolved leftovers, policy-review cases, retry exhaustion, and deadline breaches can create human-review tickets.

**Reason:** The system should surface uncertainty and exceptional conditions rather than claim completion automatically.

**Limit:** The current local dashboard's review action records that a ticket was reviewed; it does not execute deletion or approve a company request.

## ADR-010: GitHub Actions test workflow

**Decision:** Run the Python test suite on pushes and pull requests using Python 3.11.

**Reason:** Catch regressions consistently as the team integrates agent modules.

**Limit:** A green CI run is evidence for the automated tests only, not proof of production readiness or a full browser/end-to-end validation.
