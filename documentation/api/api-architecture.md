# API Architecture (Phase 2)

Base path `/api/v1/`. Endpoint list: master skill section 14 (proposed contracts). This document fixes conventions; exact request/response schemas will be generated from OpenAPI (drf-spectacular) and become the contract that all three clients code against.

## Conventions

- **Auth**: `Authorization: Bearer <access JWT>`. Refresh via `/auth/token/refresh/`.
- **IDs**: UUIDs.
- **Time**: ISO 8601 UTC in the API; clients render in the estate timezone.
- **Pagination**: cursor for event/log lists, page-number for admin tables. Envelope `{ "count"?, "next", "previous", "results": [] }`.
- **Filtering/search**: query params (`?status=`, `?from=`, `?to=`, `?search=`); documented per endpoint.
- **Errors**: one shape for all failures:

```json
{ "error": { "code": "invitation_expired", "message": "Human readable text", "details": { "field": ["..."] } } }
```

- **Status codes**: 200/201/204 success, 400 validation, 401 unauthenticated, 403 forbidden, 404 not found (also used for out-of-scope objects, so existence is not leaked), 409 state conflict, 429 rate limited.
- **Idempotency**: `Idempotency-Key` header required on `gate/check-in`, `gate/check-out` and invitation creation. Same key and payload returns the original result.
- **Rate limits**: tight on login, password recovery and `gate/verify` (per device and per officer); default for the rest.
- **Audit**: sensitive endpoints write an `AuditLog` row from the service layer.

## Gate verify (contract sketch)

Request:

```json
{ "credential": "<qr token or numeric code>", "method": "QR" }
```

Response (valid):

```json
{
  "outcome": "VALID",
  "invitation_id": "uuid",
  "display": {
    "visitor_name": "…", "resident_name": "…", "unit": "…",
    "valid_from": "…", "valid_until": "…", "vehicle_registration": null
  }
}
```

Response (rejected): `{ "outcome": "EXPIRED" }` with no display data. Gate and estate come from the officer's active shift, never the body.

## Gate check-in (contract sketch)

Request: `{ "invitation_id": "uuid", "credential": "<same value>" }` plus `Idempotency-Key`. The server re-validates under a row lock; the earlier verify result is not trusted. `409` with an outcome code if it no longer holds.

## Client rules

- API clients are generated from the OpenAPI schema into `mobile/packages/api` and the dashboard's `services/`; no hand-written duplicate clients.
- No client invents an endpoint; contract changes go through the OpenAPI schema and a documented change.
