# Deletion Request Agent milestone

After a verified request, the Discovery Agent searches the selected categories through the fictional NovaMart API. The Deletion Request Agent then submits a company-side request only for categories marked `DELETE` by the illustrative demo policy.

NovaMart receives a company ticket in `PENDING_COMPANY_APPROVAL`. The execution field remains `NOT_EXECUTED`. No agent deletes records, modifies databases, contacts a real company, or bypasses company authorization.

Categories marked `REVIEW` or `RETAIN` are not included in the deletion request. The selected scope is not expanded.

## Demo flow

1. Submit a verified request for CUST-1001.
2. Select Personal profile and Email address.
3. Discovery finds the corresponding synthetic records.
4. Deletion Request Agent sends only those categories assessed DELETE.
5. Dashboard displays the NovaMart ticket and `PENDING_COMPANY_APPROVAL`.

Company API endpoints:
- `POST /company/v1/erasure-requests`
- `GET /company/v1/erasure-requests`

The in-memory company ticket register is a local prototype. Production needs authenticated company APIs, durable ticket storage, authorization, idempotency guarantees, and a company-operated execution/approval process.
