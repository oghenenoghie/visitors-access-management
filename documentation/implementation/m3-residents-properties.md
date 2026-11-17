# M3 — Residents and Properties Implementation

Status: **In progress — implementation complete for planned backend slices; verification pending**  
Working branch: `feat/m3-residents-properties`  
Baseline: M2 commit `8ef51d95d08aa7fa3a3137e33cb485751502bec3`

## Implemented

### Properties and residential units
- Estate-scoped property hierarchy: street, block, building and compound.
- Residential units with unit number, block, floor and active/inactive status.
- Uniqueness constraints for property names within a parent and unit locations within a property.
- Estate-scoped read APIs; create/update restricted to platform and estate administrators.
- Cross-estate parentage and reassignment validation.
- Delete is not exposed; records are deactivated instead.
- Append-only audit events for property/unit create and update.

### Resident registration and review
- Estate-specific resident profile with pending, approved, rejected and suspended states.
- Public registration accepts estate code, email, password, name, optional phone and optional identity document.
- New accounts remain inactive and have no estate membership until approved.
- Registration is rate limited to 5 attempts per hour and uses configured Django password validators.
- Estate administrators can list only residents in estates they administer; residents can retrieve only their own approved profile.
- Approval activates the account and creates an active resident membership.
- Rejection requires a reason and leaves the account inactive.
- Suspension suspends only the resident's membership in that estate; it does not disable other estate memberships.
- Registration and review actions are audited.

### Encrypted identity documents
- Accepts PDF, JPEG and PNG files up to 10 MB; validates extension against file signature.
- Generates a random per-file Fernet key and wraps it with `FIELD_ENCRYPTION_KEY`.
- Stores only encrypted file bytes through Django's configured default storage backend.
- Stores metadata, plaintext SHA-256 integrity digest and wrapped data key in PostgreSQL.
- List responses never expose storage keys or encryption keys.
- Document downloads are authorised through the resident's own profile or an administrator's estate-scoped profile access and are audited.
- No public storage URL is returned.

API routes:
- `POST /api/v1/residents/register/`
- `GET /api/v1/residents/`
- `GET /api/v1/residents/{id}/`
- `POST /api/v1/residents/{id}/approve/`
- `POST /api/v1/residents/{id}/reject/`
- `POST /api/v1/residents/{id}/suspend/`
- `GET /api/v1/residents/{id}/documents/`
- `POST /api/v1/residents/{id}/documents/`
- `GET /api/v1/residents/{id}/documents/{document_id}/download/`

### Resident-to-unit assignments
- Owner, tenant and occupant relationship types.
- Active/ended status, primary designation and start/end dates.
- Only approved residents and active units/properties may be assigned.
- Resident and unit must belong to the same estate.
- Estate administrators may create/end assignments only within their estate.
- Residents can read only their own assignments while their resident profile is approved.
- Overlapping active assignments for the same resident/unit are rejected.
- Overlapping primary assignments for the same resident are rejected.
- Database constraint prevents more than one active primary assignment.
- Assignment creation and ending are audited; deletion is not exposed.

API routes:
- `GET /api/v1/resident-unit-assignments/`
- `GET /api/v1/resident-unit-assignments/{id}/`
- `POST /api/v1/resident-unit-assignments/`
- `POST /api/v1/resident-unit-assignments/{id}/end/`

### CSV bulk import
- Estate administrators can preview or commit unit and resident CSV files.
- Dry-run is the default and does not write records.
- Commit revalidates the uploaded file and is atomic; any row error prevents partial import.
- CSV is UTF-8, up to 5 MB and 1,000 data rows.
- Unit import requires `property_id,unit_number`; `block` and `floor` are optional. Property must be active and belong to the selected estate.
- Resident import requires `email,first_name,last_name`; `phone_number` is optional.
- Duplicate rows, existing units, existing accounts, invalid emails/phone numbers, cross-estate property IDs and overlong values return row-level errors.
- Imported residents receive inactive accounts with unusable passwords and pending profiles; no estate membership is created. An administrator must approve each resident, then issue a password-reset code through the M2 admin workflow.

API routes:
- `POST /api/v1/imports/units/`
- `POST /api/v1/imports/residents/`

Send multipart fields `estate_id`, `file`, and optional `dry_run`. Use `dry_run=true` for preview (default), then upload the same corrected file with `dry_run=false` to commit.

## Security decisions and limitations
- Estate code is a routing/reference value only, not proof of occupancy. It does not grant access. Administrator verification and approval remain mandatory.
- Suspension is membership-scoped.
- The configured Django default storage backend must be private and non-public in production. The application encrypts file contents before storage, but Q8 remains open for provider selection and deployment configuration.
- Back up `FIELD_ENCRYPTION_KEY` securely. Loss of this key makes existing identity documents permanently unreadable; rotation requires a documented rewrapping procedure.
- Do not log raw documents, passwords, wrapped keys or storage paths.
- Estate managers remain read-only for resident/property administration until configurable permissions are implemented.

## Remaining M3 work
1. Run full CI: Ruff lint/format, Django checks, migration consistency, OpenAPI validation and pytest.
2. Add/adjust edge-case and negative tests based on CI findings.
3. Confirm production storage backend privacy, key backup/rotation and retention controls before deployment.
4. Complete security review and mark M3 done only after all checks pass.

## Verification commands
- `ruff check . && ruff format --check .`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py spectacular --file /tmp/schema.yml --validate --fail-on-warn`
- `pytest --cov=apps --cov-report=term-missing`
