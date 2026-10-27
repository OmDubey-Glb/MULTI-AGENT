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
