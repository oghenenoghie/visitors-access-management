# M3 — Residents and Properties Implementation

Status: **In progress — backend foundations implemented; verification pending**  
Working branch: `feat/m3-residents-properties`  
Baseline: M2 commit `8ef51d95d08aa7fa3a3137e33cb485751502bec3`

## Scope

M3 establishes the estate's property inventory, resident identity and resident-to-unit assignments. Resident access remains disabled until an estate administrator approves the registration. A unit number or estate code alone is never proof of residence.

## Implemented

### Properties and residential units

- New `apps.properties` Django app.
- Estate-scoped property hierarchy: street, block, building and compound.
- Residential units with unit number, block, floor and active/inactive status.
- Uniqueness constraints for property names within a parent and unit locations within a property.
- Estate-scoped read APIs; create/update restricted to platform and estate administrators.
- Cross-estate parent and reassignment validation.
- Delete is intentionally not exposed; records are deactivated instead.
- Append-only audit events for property/unit create and update.

### Resident registration and review

- New `apps.residents` app and estate-specific resident profile.
- Public registration endpoint accepts estate code, email, password, name and optional phone number.
- Registration creates an inactive user and a pending profile; it creates no estate membership.
- Registration is rate limited to 5 attempts per hour per throttle identity.
- Passwords are validated using the configured Django password validators.
- Estate administrators can list residents only in estates they administer.
- Residents can retrieve only their own profile.
- Approve creates an active resident membership and activates the account.
- Reject requires a reason and leaves the account inactive.
- Suspend marks the estate membership suspended. It does not deactivate the global user account, so memberships in other estates are unaffected.
- Review actions and registration submissions are written to the append-only audit log.

API routes:
- `POST /api/v1/residents/register/`
- `GET /api/v1/residents/`
- `GET /api/v1/residents/{id}/`
- `POST /api/v1/residents/{id}/approve/`
- `POST /api/v1/residents/{id}/reject/`
- `POST /api/v1/residents/{id}/suspend/`

### Resident-to-unit assignments

- Resident assignments support owner, tenant and occupant relationships.
- Assignments have active/ended status, primary designation and start/end dates.
- Only approved residents and active units/properties may be assigned.
- Resident and unit must belong to the same estate.
- Estate administrators may create and end assignments only within their estate.
- Residents can read only their own assignments.
- Overlapping active assignments for the same resident/unit are rejected.
- Overlapping primary assignments for the same resident are rejected.
- A database uniqueness constraint prevents more than one active primary assignment.
- Assignment creation and ending are audited; deletion is not exposed.

API routes:
- `GET /api/v1/resident-unit-assignments/`
- `GET /api/v1/resident-unit-assignments/{id}/`
- `POST /api/v1/resident-unit-assignments/`
- `POST /api/v1/resident-unit-assignments/{id}/end/`

## Security and product decisions

- Estate code is a routing/reference value only. It is not a secret and does not prove occupancy.
- Self-registration remains pending and inactive until an estate administrator performs independent verification and approves it.
- No resident gains access to visitor functions merely by registering or knowing a unit number.
- Estate suspension is membership-scoped. It does not disable a user's unrelated memberships in other estates.
- Estate managers remain read-only for resident and property administration until configurable permissions are implemented.
- Q6 remains open for the estate's definitive resident verification evidence and policy. The approval workflow is designed to require that evidence before approval.
- Q8 remains open for the private object-storage provider. No provider has been selected.

## Remaining M3 work

1. Identity-document metadata, private encrypted storage adapter, authorised access and audit-on-view.
2. CSV bulk import with dry-run validation, row-level errors, duplicate detection and explicit commit.
3. Additional tests for concurrent primary assignment creation, rejection/suspension edge cases and API schema.
4. Run full backend CI, migration consistency check and OpenAPI validation.

## Verification commands

- `ruff check . && ruff format --check .`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py spectacular --file /tmp/schema.yml --validate --fail-on-warn`
- `pytest --cov=apps --cov-report=term-missing`

Do not mark M3 complete until encrypted document handling, bulk import and all verification gates are complete.
