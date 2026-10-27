# Audit Agent workflow

The Audit Agent stores a privacy-minimized record of important workflow actions in a local SQLite database at `data/audit.sqlite3`.

## Recorded events

- Intake request accepted
- Scoped discovery completed
- Company deletion request submitted
- Explicit NovaMart demo staff approval/execution
- Independent verification result

Each record includes an opaque request ID, an HMAC-SHA256 subject token, agent/action/outcome, item count, selected category IDs, UTC timestamp, previous hash, and event hash. Raw customer identifiers, email addresses, mobile numbers, OTPs, and discovered item contents are not written to the audit table.

## Integrity

Records are appended in a SQLite transaction. Each event hash is SHA-256 over canonical JSON and includes the previous event hash. `GET /api/audit` returns the newest records; `GET /api/audit/verify` checks the complete chain from the GENESIS marker.

The dashboard's Compliance & Audit Trail panel shows records and chain status.

## Demo security boundaries

The default `AUDIT_HMAC_KEY` fallback is for local demonstration only. Set a strong, private environment variable before any shared deployment. Protect the SQLite file and backups with appropriate access controls. Hash chaining is tamper-evident, not tamper-proof: an attacker able to rewrite the entire database and recompute every hash can forge a new chain. Production should anchor signed checkpoints in a separately controlled system and enforce filesystem/database write restrictions.

This local prototype exposes no audit edit/delete API. A database administrator can still alter the SQLite file directly; the verification endpoint is designed to detect ordinary row changes.
