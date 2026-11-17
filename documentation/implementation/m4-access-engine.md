# M4 — Access Engine

## Status

Backend foundation implemented on `feat/m4-access-engine`. This milestone is not complete until CI, API schema validation, acceptance tests and concurrency verification pass.

## Delivered in this implementation slice

- Estate-scoped visitor invitations tied to an approved resident profile and a currently active resident-to-unit assignment.
- Single-use and bounded multi-use invitations (maximum 100 uses).
- Time-bounded invitations (maximum 30 days).
- Cryptographically random QR token and eight-digit manual code.
- HMAC-SHA256 credential digests using `CREDENTIAL_PEPPER`; plaintext credentials are returned only in the creation response and are never persisted.
- Backend verification with explicit results: `VALID`, `EXPIRED`, `REVOKED`, `CANCELLED`, `ALREADY_USED`, `NOT_YET_VALID`, `INVALID`, and `ALREADY_CHECKED_IN`.
- Gate-device and officer estate matching.
- Transactional credential consumption and entry creation. The credential row is locked before invitation state is checked, so concurrent one-time admission attempts serialize.
- Check-in/check-out with the exit event linked to the exact entry event.
- Supervisor/estate-admin override requiring a justification.
- Append-only access events enforced by model methods and a PostgreSQL trigger.
- Every creation, cancellation, verification rejection, admission, departure and override writes an append-only audit log record.
- Resident suspension immediately cancels active invitations and revokes their credentials.

## API

All endpoints are under `/api/v1/`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `invitations/` | List invitations visible to the caller |
| POST | `invitations/` | Create an invitation and issue credentials |
| POST | `invitations/{id}/cancel/` | Cancel invitation and revoke credential |
| POST | `gate/verify/` | Validate QR token or manual code without consuming it |
| POST | `gate/check-in/` | Atomically consume a use and record entry |
| POST | `gate/check-out/` | Record departure linked to the active entry |
| POST | `gate/override/` | Supervisor/admin override with mandatory reason |
| GET | `gate/activity/` | Estate-scoped gate event history |

### Invitation creation request

```json
{
  "visitor_name": "Ada Visitor",
  "visitor_phone": "+2348012345678",
  "vehicle_registration": "ABC-123XY",
  "unit": "residential-unit-uuid",
  "valid_from": "2026-11-18T08:00:00Z",
  "valid_until": "2026-11-18T18:00:00Z",
  "access_type": "single_use"
}
```

For `multi_use`, pass `max_uses` between 2 and 100. Single-use invitations always have one use.

The successful creation response includes `qr_token` and `access_code` once. The QR should encode only the opaque `qr_token`; do not encode visitor details, resident details or database identifiers. Clients must not expect the backend to reveal either secret again.

### Gate request

```json
{
  "gate_device": "gate-device-uuid",
  "credential": "opaque-qr-token-or-eight-digit-code"
}
```

For check-out, send `gate_device` and `invitation`. For override, send those fields plus a non-empty `reason`.

## Security decisions and boundaries

- A resident may create an invitation only for a unit to which they have an active, date-valid assignment in the same estate.
- A gate must be active and belong to an estate where the authenticated officer has an active security-officer, security-supervisor or estate-admin membership.
- Only the invitation creator or an estate administrator can cancel it.
- Only security supervisors and estate administrators can override a failed/exceptional admission. Platform administrators can operate across estates.
- A supervisor override consumes one pass use. Single-use or exhausted credentials become consumed; multi-use credentials retain any remaining uses after the visitor exits.
- Suspending a resident cancels all their active passes immediately. This is the selected policy for already-issued credentials.
- A verification scan does not consume a use. A successful check-in does.
- Rejected gate attempts are persisted as access events and audit records. Check-in rejection responses return the recorded event so the transaction does not roll back the evidence.
- Access events cannot be updated or deleted through the ORM; PostgreSQL enforces append-only behaviour with a trigger.
- The numeric code has eight digits. Unique hash constraints detect collisions and issuance retries up to five times before returning a controlled validation error.
- Notifications are not sent in this slice. Push notification delivery and resident-facing history are integration work for later milestones.

## Gate provisioning

Gate devices are provisioned by an administrator through Django admin in this slice. Device records must be assigned to the correct estate before officers can use them. A dedicated estate-admin API for gate/device lifecycle is not included yet.

## Verification still required

- Run Ruff lint and format.
- Run Django system checks and migration consistency.
- Validate the OpenAPI schema.
- Run all backend tests plus the M4 acceptance suite.
- Confirm the concurrent-consume test against PostgreSQL (SQLite is not an acceptable substitute for row-lock verification).
- Review the generated schema and all access response payloads before mobile clients consume them.

## Deferred

- FCM notifications and resident app integration.
- Gate device enrolment/heartbeat and device-specific credentials.
- Multi-gate operational policies and supervisor second-person approval.
- Idempotency keys for unreliable mobile network retries.
- Configurable estate-level invitation duration and usage policies.
- QR image rendering is a client concern; the API returns only opaque QR material.
