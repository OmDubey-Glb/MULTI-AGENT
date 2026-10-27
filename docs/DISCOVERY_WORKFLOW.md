# Discovery milestone

The Intake API now hands a verified request to the Discovery Agent. The agent forwards the exact customer ID and selected category IDs to the separate fictional NovaMart service on port 9000.

## Run

From the repository root, activate the virtual environment, install requirements, then run:

```powershell
python run.py
```

This starts the orchestrator at http://127.0.0.1:8000 and the NovaMart mock company API at http://127.0.0.1:9000. Stop both with Ctrl+C in the terminal running the script.

## Demo

Use customer ID `CUST-1001`, choose Personal profile and Email address, complete the offline OTP flow, then submit. The Discovery Agent should report matching synthetic records for only those selected categories. Try selecting only Personal profile to confirm contact details are not returned.

Health checks:
- http://127.0.0.1:8000/api/health
- http://127.0.0.1:9000/health

## Safety boundary

The NovaMart service contains generated fictional records only. Discovery is read-only. It does not contact real companies, access real customer data, or execute deletion. In production, this adapter must be replaced with a company-authorized API and its access controls, consent, and audit requirements.
