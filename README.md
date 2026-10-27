# DPDP Erasure Orchestrator

A privacy-conscious Multi-Agent AI prototype coordinating personal-data erasure requests with a company's authorized systems.

## Six specialist agents

1. Intake — validates requests and handles demo OTP verification.
2. Discovery — finds matching data in configured demo systems.
3. Deletion Request — prepares/submits authorized requests to the company API and tracks responses. It does not directly delete arbitrary company data.
4. Verification — independently checks outcomes and triggers bounded retries.
5. Audit — records privacy-minimized, tamper-evident events.
6. Monitoring — tracks deadlines, retries, tickets, and system health.

The orchestrator coordinates these six agents; it is not a seventh specialist agent.

## Demo safety boundary

NovaMart is a fictional company simulator. Only generated demo records may be changed by its simulated company-authorized service. The agents do not access or delete real third-party production data.

## Planned stack

Python 3.11+, FastAPI, Uvicorn, Pydantic v2, asyncio, httpx, PyYAML, SQLite, vanilla HTML/CSS/JavaScript, and Server-Sent Events.

## Local services

- Dashboard/API: http://127.0.0.1:8000
- Fictional NovaMart simulator: http://127.0.0.1:9000

## Run

```bash
python run.py
```

The offline Dev Inbox displays demo OTPs locally; it does not prove ownership of a real phone number or email address. Legal rules and deadlines are illustrative configuration and require qualified review before real-world use.


## Judge preparation

- [Architecture diagram and workflow](docs/ARCHITECTURE.md)
- [3-scenario live demo instructions](docs/DEMO_SCRIPT.md)
- [Viva guide: agent roles, design, limitations, and likely questions](docs/VIVA_GUIDE.md)
- [Architecture decision records](docs/DECISIONS.md)

## Local setup

Use Python 3.11 or newer.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

python -m pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:8000. The launcher starts the local NovaMart simulator on port 9000 and waits for its health endpoint before starting the dashboard. Stop both services with Ctrl+C.

## Validation

GitHub Actions runs `pytest -q` on pushes and pull requests to `main`. Check the repository's Actions tab for the latest result. A passing unit-test workflow does not replace a local browser/demo rehearsal.

## Current implementation status

This is a hackathon prototype, not a production DPDP compliance product. The NovaMart company API, demo identities, and scenario fault modes are synthetic. OTP delivery is local-only, legal rules are illustrative, and company approval is simulated. Production use would require qualified legal review, real identity verification, authenticated company operators, secure company integrations, durable state, and production-grade security controls.
