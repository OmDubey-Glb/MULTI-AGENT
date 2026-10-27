# Verification Agent workflow

The Deletion Request Agent submits a scoped request to NovaMart and does not execute deletion. A separate, explicit dashboard action represents a demo NovaMart operator approving the ticket. The mock company service changes only generated in-memory synthetic records.

After the company reports execution, the Verification Agent independently calls NovaMart discovery for the ticket categories and compares remaining item IDs with the submitted item IDs. It returns VERIFIED only when none of the requested items remain. A pending ticket returns WAITING_FOR_COMPANY; remaining items return LEFTOVERS_FOUND.

## Demo
1. Submit an OTP-verified request for CUST-1001.
2. Select Personal profile and Email address.
3. Review the NovaMart ticket in PENDING_COMPANY_APPROVAL / NOT_EXECUTED.
4. Click the explicit SIMULATE NOVAMART STAFF APPROVAL button.
5. The local NovaMart mock service applies the approved action to synthetic in-memory records only.
6. The Verification Agent performs a fresh discovery scan and reports the result.

This is a local hackathon simulation, not a connection to NovaMart or any real company. Ticket state and synthetic data reset when services restart. Production needs authenticated company operators, durable ticket records, company-owned execution, comprehensive verification across systems, and controlled backup/replica handling.