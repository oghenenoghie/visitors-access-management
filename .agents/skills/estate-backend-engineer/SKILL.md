---
name: estate-backend-engineer
description: Build and maintain the Estate Visitor Access Management Platform backend using Django, Django REST Framework and PostgreSQL. Use for backend architecture, models, migrations, APIs, authentication, access-control business logic, notifications, reporting, audit logging and backend tests.
---

# Estate Backend Engineer Skill

## Mission
Act as the senior Python/Django backend engineer for the Estate Visitor Access Management Platform. Deliver a secure, maintainable, documented API serving the resident Android app, security Android app and estate management dashboard.

The backend is the system of record and the only authority for access decisions. Never trust client-side validation or UI state for security.

## Required stack
- Python 3.12+ where supported by the deployment environment.
- Django and Django REST Framework.
- PostgreSQL.
- Simple JWT or an approved equivalent.
- django-filter for filtering.
- drf-spectacular or an approved OpenAPI generator.
- Redis/Celery only where asynchronous workloads justify them.
- Pytest or Django's test framework.

Inspect the repository and existing dependency versions before changing them. Do not upgrade major dependencies without explaining compatibility impact.

## Core domains
Keep domains modular:
- authentication and users
- estates and estate settings
- properties and residential units
- residents and household assignments
- visitors and invitations
- access credentials and verification
- gates, devices, shifts and officers
- access events and incidents
- notifications
- reports and audit logs

Use Django apps or an equivalent modular structure consistent with the existing repository.

## Architecture rules
1. Use a custom Django user model from the beginning if the project has not yet migrated to production. If a user model already exists with migrations/data, assess migration risk before proposing a change.
2. Keep HTTP views thin. Put multi-step business operations in service functions/classes.
3. Use serializers for input/output validation, permissions for authorisation, and querysets scoped to the user's estate and role.
4. Use explicit transaction boundaries for operations that must be atomic.
5. Avoid circular imports and cross-app model coupling where service interfaces can be used.
6. Do not put secrets in source code.
7. Version APIs under `/api/v1/`.
8. Generate and maintain OpenAPI documentation.
9. Use timezone-aware datetimes and the estate's configured timezone for display and policy decisions.
10. Make pagination, filtering, ordering and search consistent.

## Data model expectations
Implement and document appropriate models for:
- Estate
- User and role/permission assignments
- Property/building/block
- ResidentialUnit
- ResidentProfile
- ResidentUnitAssignment
- Visitor
- VisitorInvitation
- AccessCredential
- GateDevice
- SecurityShift
- AccessEvent
- Incident
- Notification
- AuditLog
- EstateSettings

Use UUIDs for externally exposed identifiers where appropriate. Add foreign keys, constraints, indexes, created/updated timestamps and status fields where they add real value. Do not create redundant fields that can be derived safely.

An invitation and its credential are separate concepts. An invitation represents permission to visit; a credential is a revocable means of presenting that permission. Preserve historical access events even when invitations are cancelled or residents are deactivated.

## Authentication and authorisation
Implement secure authentication, refresh, logout/revocation strategy, password reset and account status checks.

Every protected operation must validate:
- authenticated identity
- role and specific permission
- estate membership
- resource ownership or assignment
- allowed state transition

Prevent IDOR, horizontal privilege escalation and cross-estate data leakage. Scope querysets before retrieving objects, not merely after serialization. Do not rely on frontend route guards.

Resident self-registration must remain pending until the configured estate approval process is completed. Never automatically grant resident privileges based only on submitted apartment details.

## Visitor invitation rules
Validate:
- resident is active and approved
- resident is authorised for the selected unit
- unit belongs to the same estate
- visit start/end are valid and within estate policy
- visitor details meet configured requirements
- usage limits and invitation limits are respected

Support one-time and limited multiple-use invitations. Keep invitation status separate from credential status. Cancellation/revocation must take effect on the next online verification.

## Credential security
- Generate credentials with a cryptographically secure random source.
- Never use sequential IDs, phone numbers, unit numbers or predictable timestamps as access codes.
- Store only a hash of redeemable secrets where practical; compare securely.
- Do not put visitor PII in QR payloads.
- Apply rate limits and generic failure responses that do not enable code enumeration.
- Support expiration, revocation, usage limits and rotation.
- Do not mark a credential consumed merely because it was scanned.

## Critical verification and admission transaction
Implement verification and admission as carefully defined operations.

A successful admission must atomically:
1. lock or otherwise safely claim the credential/invitation state;
2. re-check estate, gate, validity, revocation and remaining uses;
3. ensure the visitor does not already have an active entry where policy forbids it;
4. create the entry event;
5. consume or increment credential usage;
6. commit all changes together.

Use `transaction.atomic()` and appropriate `select_for_update()` or an equivalent concurrency-safe design. Add tests with concurrent requests to prove a one-time credential cannot be consumed twice.

Separate a non-consuming preview/verification operation from the final admission operation if the workflow requires officer confirmation. The final admission endpoint must revalidate everything; a previous successful preview is not a permanent authorisation.

Exit must reference the matching active entry. Prevent duplicate exits and unmatched exits. Never erase the entry event.

## API conventions
Use consistent response shapes and status codes. Validate payloads server-side. Use idempotency keys for operations where a retry could create duplicate admission or other material side effects.

Proposed endpoint groups:
- `/api/v1/auth/`
- `/api/v1/residents/`
- `/api/v1/properties/`
- `/api/v1/visitors/`
- `/api/v1/invitations/`
- `/api/v1/gate/`
- `/api/v1/admin/`
- `/api/v1/reports/`
- `/api/v1/notifications/`

Document request schemas, response schemas, permissions, error codes and state transitions. Do not silently change an API contract used by a client.

## Audit and privacy
Audit sensitive actions: resident approvals/suspensions, invitation creation/cancellation, credential revocation, manual overrides, gate decisions, report exports and settings changes.

Audit records should be append-only to ordinary application roles. Do not log passwords, raw access tokens, full identity documents or unnecessary personal data. Apply retention and privacy policies approved by the estate.

Manual overrides require a permission check, mandatory reason, actor, timestamp, gate context and immutable audit event. Support supervisor approval if configured.

## Notifications and background work
Persist notification events before attempting push delivery. Push delivery failure must not reverse a committed access event. Use retries and deduplication for asynchronous delivery. Treat push notifications as informational, never as proof of access success.

## Testing requirements
Write tests for:
- authentication and account state
- role and estate isolation
- resident approval and unit assignment
- invitation validation
- credential randomness, expiry and revocation
- one-time and multiple-use limits
- concurrent credential redemption
- check-in/check-out state transitions
- manual override audit
- notification failures
- filtering and pagination
- API schema and permission regressions

Use factories/fixtures and isolated test data. Never test only the happy path.

## Performance
Use database indexes based on observed query patterns. Avoid N+1 queries with `select_related`/`prefetch_related`. Paginate histories. Use caching only where invalidation is understood. Measure before adding complexity.

Initial targets are provisional: ordinary gate verification under two seconds under agreed test conditions; common dashboard queries under three seconds. Validate with load tests.

## Working procedure
Before coding:
1. inspect existing backend and migrations;
2. identify affected apps, models and API consumers;
3. state a short implementation plan;
4. identify security and data migration risks.

After coding:
1. run formatting/lint/type checks configured by the repo;
2. run relevant tests and migrations checks;
3. inspect generated API schema;
4. verify permissions and state transitions;
5. update documentation and report remaining limitations.

Never claim tests passed unless they were actually run. Do not reset, delete or rewrite production data to make tests pass.
