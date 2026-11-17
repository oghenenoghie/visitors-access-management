# Database Design and ERD (Phase 2)

PostgreSQL via the Django ORM. Custom user model from the first migration. Externally exposed IDs are UUIDs.

Entities marked **[proposed]** extend the master skill's model list; fields marked **[proposed]** are additions to its field lists. Everything else matches the master skill.

```mermaid
erDiagram
  ESTATE ||--o{ ESTATE_MEMBERSHIP : has
  USER ||--o{ ESTATE_MEMBERSHIP : holds
  ESTATE ||--|| ESTATE_SETTINGS : configures
  ESTATE ||--o{ PROPERTY : contains
  PROPERTY ||--o{ RESIDENTIAL_UNIT : contains
  USER ||--o| RESIDENT_PROFILE : is
  ESTATE ||--o{ RESIDENT_PROFILE : registers
  RESIDENT_PROFILE ||--o{ RESIDENT_UNIT_ASSIGNMENT : assigned
  RESIDENTIAL_UNIT ||--o{ RESIDENT_UNIT_ASSIGNMENT : houses
  ESTATE ||--o{ VISITOR : scopes
  RESIDENT_PROFILE ||--o{ VISITOR : created_by
  VISITOR ||--o{ VISITOR_INVITATION : invited_as
  RESIDENT_PROFILE ||--o{ VISITOR_INVITATION : authorises
  RESIDENTIAL_UNIT ||--o{ VISITOR_INVITATION : destination
  VISITOR_INVITATION ||--o{ ACCESS_CREDENTIAL : issues
  ESTATE ||--o{ GATE_DEVICE : operates
  USER ||--o{ SECURITY_SHIFT : works
  GATE_DEVICE ||--o{ SECURITY_SHIFT : staffed_by
  VISITOR_INVITATION ||--o{ ACCESS_EVENT : records
  ACCESS_CREDENTIAL ||--o{ ACCESS_EVENT : presented
  GATE_DEVICE ||--o{ ACCESS_EVENT : at
  USER ||--o{ ACCESS_EVENT : officer
  ACCESS_EVENT ||--o| ACCESS_EVENT : exit_of
  USER ||--o{ NOTIFICATION : receives
  USER ||--o{ DEVICE_REGISTRATION : registers
  ESTATE ||--o{ AUDIT_LOG : scopes
  USER ||--o{ AUDIT_LOG : actor
  ESTATE ||--o{ INCIDENT : scopes
  USER ||--o{ INCIDENT : reports

  ESTATE {
    uuid id PK
    string name
    string estate_code UK
    string timezone
    string status
  }
  USER {
    uuid id PK
    string email UK
    string phone_number
    string password
    bool is_active
    bool is_verified
  }
  ESTATE_MEMBERSHIP {
    uuid id PK
    uuid user_id FK
    uuid estate_id FK
    string role
    string status
  }
  RESIDENT_PROFILE {
    uuid id PK
    uuid user_id FK
    uuid estate_id FK
    string resident_reference
    string approval_status
    uuid approved_by FK
  }
  VISITOR {
    uuid id PK
    uuid estate_id FK
    uuid created_by_resident_id FK
    string full_name
    string phone_number
    string vehicle_registration
  }
  VISITOR_INVITATION {
    uuid id PK
    uuid visitor_id FK
    uuid resident_id FK
    uuid estate_id FK
    uuid unit_id FK
    timestamptz valid_from
    timestamptz valid_until
    string access_type
    int usage_limit
    int usage_count
    string status
  }
  ACCESS_CREDENTIAL {
    uuid id PK
    uuid invitation_id FK
    uuid estate_id FK
    string credential_type
    string token_hash
    string status
    timestamptz expires_at
    int max_uses
    int uses_count
  }
  ACCESS_EVENT {
    uuid id PK
    uuid estate_id FK
    uuid invitation_id FK
    uuid credential_id FK
    uuid gate_device_id FK
    uuid officer_id FK
    uuid entry_event_id FK
    string event_type
    string event_status
    timestamptz event_time
    string rejection_reason
  }
```

Remaining entities (`Property`, `ResidentialUnit`, `ResidentUnitAssignment`, `GateDevice`, `SecurityShift`, `Notification`, `AuditLog`, `EstateSettings`) follow the master skill field lists exactly and are omitted from the field blocks above only for readability.

## Proposed additions

| Addition | Why |
|---|---|
| `EstateMembership` (user, estate, role, status) | Roles are estate-scoped; managers are limited to assigned estates; supports multi-estate later. `User.role` becomes the platform-level role only (super administrator or none). |
| `Visitor.estate_id`, `Visitor.created_by_resident_id` | Prevents one resident reaching another's visitor records. |
| `AccessCredential.estate_id` | Estate-scoped credential lookup at the gate. |
| `AccessEvent.entry_event_id` (self FK, EXIT only) | Links an exit to its original entry. |
| `Incident` (estate, reported_by, gate_device, severity, description, status, created_at) | Needed by the gate incident API and the dashboard Incidents module. |
| `DeviceRegistration` (user, platform, push_token, last_seen_at, is_active) | FCM tokens, invalid-token handling. |
| `AuditLog` extras: `object_label` optional | Readable audit entries without joins. Low priority. |

## Constraints and indexes

- `ResidentialUnit`: unique `(property_id, block, unit_number)`.
- `ResidentUnitAssignment`: at most one active primary assignment per resident; no overlapping active assignment to the same unit.
- `AccessCredential`: partial unique `(estate_id, token_hash)` where status is active; check `uses_count <= max_uses`.
- `VisitorInvitation`: check `valid_until > valid_from`; check `usage_count <= usage_limit` where a limit is set.
- `AccessEvent`: partial unique on `entry_event_id` for EXIT rows (one exit per entry); at most one open entry per invitation (an ENTRY with no linked EXIT), enforced in the check-in transaction and by constraint where PostgreSQL allows.
- Indexes: `AccessEvent(estate_id, event_time desc)`, `(gate_device_id, event_time desc)`, `(invitation_id)`; `VisitorInvitation(estate_id, status, valid_until)`, `(resident_id, created_at desc)`; `Notification(user_id, read_at)`; `AuditLog(estate_id, created_at desc)`, `(actor_id, created_at desc)`.

## Data handling

- `AuditLog`, `AccessEvent` and invitations are preserved; retention follows `EstateSettings` and an approved process. No hard deletes on these.
- Soft deletion only for users and residential records where history must be kept.
- `identification_reference` stays minimal and is encrypted at rest if it must be kept at all.
- Status fields are enums with database check constraints. All timestamps are `timestamptz`, displayed in the estate timezone.
- State changes that must be atomic (credential consumption, check-in, approval) happen inside `transaction.atomic()` in the service layer.
