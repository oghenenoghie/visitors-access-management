# M3 — Residents and Properties Implementation

Status: **In progress**  
Working branch: `feat/m3-residents-properties`  
Baseline: M2 commit `8ef51d95d08aa7fa3a3137e33cb485751502bec3`

## Scope and sequencing

M3 builds the estate's property inventory first, then resident identity and unit assignments. Resident access must remain disabled until an administrator approves the profile. No resident should gain visitor-invitation permissions merely by supplying a unit number.

### Implemented in the first slice

- New `apps.properties` Django app.
- Estate-scoped `Property` hierarchy with street, block, building and compound types.
- Estate-scoped `ResidentialUnit` records with unit number, block, floor and active/inactive status.
- PostgreSQL uniqueness constraints for property names within a parent and unit locations within a property.
- Read APIs scoped through active estate membership.
- Create/update restricted to platform administrators and estate administrators. Delete is intentionally not exposed; records are deactivated instead.
- Audit entries for property and unit creation/update.
- API routes: `GET/POST/PATCH /api/v1/properties/` and `GET/POST/PATCH /api/v1/residential-units/` (detail routes follow the DRF router conventions).
- Initial API tests cover creation, resident read-only access, cross-estate isolation, cross-estate parent rejection and non-deletion.

## Remaining M3 work

1. Resident profile and status model, linked to the existing custom user and an estate.
2. Administrator-created resident registration and pending self-registration, with activation only after approval.
3. Approval/rejection/suspension endpoints and audit events. Suspension must revoke the resident's active credentials once the access engine exists.
4. Resident-to-unit assignments, including primary assignment and active date ranges; prevent overlapping or cross-estate assignments.
5. Identity-document metadata and an encrypted storage adapter with private access and audit-on-view.
6. CSV bulk import with dry-run validation, row-level errors, duplicate detection and an atomic/explicit commit step.
7. OpenAPI descriptions, permission/IDOR tests, migration checks and full CI.

## Decisions and blockers

- **Q6 — estate reference verification remains open.** The documented working default is a management-issued estate reference plus administrator approval. Do not treat apartment details alone as proof of residency.
- **Q8 — cloud provider remains open.** The client proposal requires private object storage with per-file encryption. Implement a storage interface and tests, but do not select a cloud provider or claim production document storage is ready until the estate chooses AWS, Azure or GCP.
- **Identity document policy:** collect only the minimum required fields; never return raw document bytes in list/detail serializers; audit every authorised document view; use short-lived download access.
- **Role policy:** estate administrators manage properties and residents. Estate managers remain read-only by default until configurable permissions are implemented. Residents can read only their own profile and assignments.

## Verification required before merge

- `ruff check . && ruff format --check .`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py spectacular --file /tmp/schema.yml --validate --fail-on-warn`
- `pytest --cov=apps --cov-report=term-missing`

Do not mark M3 complete until the resident approval flow, assignment rules, import validation and encrypted document-storage path are implemented and tested.
