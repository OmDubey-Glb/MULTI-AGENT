# Verification Agent workflow

After NovaMart reports company execution, the Verification Agent independently scans every record in the exact company-approved category scope. It does not limit the scan to the original discovery IDs, so newly appearing records in those categories are also visible.

A pending ticket returns WAITING_FOR_COMPANY. A full-scope scan with no remaining records returns VERIFIED. Remaining records return LEFTOVERS_FOUND with their item IDs.

## Bounded retry

When leftovers remain, `POST /api/retry/{request_id}` re-scans the latest executed ticket and submits a new NovaMart ticket containing only the leftover IDs and the same approved categories. Each retry uses a distinct idempotency key and requires a fresh explicit company approval. The orchestrator permits three retry submissions. If leftovers remain after those attempts, a subsequent retry call is refused and a human-review ticket is opened.

The retry API never executes deletion. The company approval endpoint is the only demo path that mutates synthetic in-memory records.

## Demo limits

This is a local hackathon simulation, not a connection to NovaMart or any real company. Ticket state and synthetic data reset when services restart. A deterministic replica-lag/failure injector and one-click scenario launcher are not implemented yet. Production needs authenticated company operators, durable ticket records, company-owned execution, and comprehensive verification across systems.
