# Milestone 2 — Intake workflow

The first functional workflow is available in the dashboard.

## Flow
1. Load the NovaMart category catalog from `GET /api/companies`.
2. Select one or more categories. The selected identifiers are preserved exactly in the request.
3. Choose either email or mobile and request a six-digit OTP using `POST /api/intake/otp`.
4. In this offline hackathon build, the OTP is shown in `GET /api/dev-inbox`; no email or SMS is sent.
5. Verify with `POST /api/intake/verify`, then submit with `POST /api/intake/submit`.

## Safeguards in this prototype
- OTP expires after five minutes; at most three verification attempts are allowed.
- A 30-second resend cooldown is applied per customer/channel.
- OTP values are stored as SHA-256 hashes in the session state; only the development inbox holds the demo delivery code.
- A verified session can submit only once.
- The request cannot be submitted before OTP verification.
- Category IDs are validated against the configured NovaMart catalog. The system does not expand the selected scope.
- Policy actions are illustrative demo configuration, not legal advice or an automatic deletion instruction.

## Current boundary
This milestone records an intake request and emits live dashboard events. It does not yet discover, delete, or verify data. A later Deletion Request Agent will submit an authorized request to the fictional NovaMart company API or prepare a staff ticket. The company-owned system remains responsible for executing deletion.

## Run
Install dependencies with `pip install -r requirements.txt`, then run `python run.py`. Open the local dashboard and use the Offline Dev Inbox displayed below the intake form.
