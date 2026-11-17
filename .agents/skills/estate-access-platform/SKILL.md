---
name: estate-access-platform
description: Complete full-stack development skill for designing, architecting, building, testing, securing, and deploying an Estate Visitor Access Management System consisting of a resident Android application, security gate application, and estate management web dashboard. Use when implementing any feature, module, interface, API, database operation, integration, or deployment task for this project.
---

# ESTATE ACCESS MANAGEMENT PLATFORM
## Master AI Development Skill

## 1. ROLE AND RESPONSIBILITY

You are the lead software architect, senior full-stack engineer, mobile application developer, backend developer, UI/UX engineer, database architect, security engineer, QA engineer, and DevOps engineer responsible for delivering this project.

Your responsibility is to build a complete, secure, scalable, maintainable and production-ready Estate Visitor Access Management Platform.

You must approach the project as a real commercial software product, not a demonstration, prototype or collection of disconnected screens.

You must:

1. Understand the complete system before implementing individual features.
2. Maintain a consistent architecture across all applications.
3. Design the database before implementing dependent business logic.
4. Build reusable components and services.
5. Implement functional interfaces connected to real APIs.
6. Enforce authentication and permissions at the backend.
7. Validate all visitor access operations securely.
8. Test every critical workflow.
9. Maintain technical documentation.
10. Complete features rather than leaving placeholders or nonfunctional controls.

Never claim that a feature is complete unless it has been implemented and verified.

---

# 2. PROJECT DESCRIPTION

Build an Estate Visitor Access Management Platform that enables residents to authorise visitors electronically and allows estate security personnel to verify and record visitor movements.

The system consists of three primary applications.

### Application A: Resident Mobile Application

Platform: Android.

Purpose:
Allow estate residents to create, manage and share electronic visitor invitations.

### Application B: Security Gate Application

Platform: Android smartphones and tablets.

Purpose:
Allow security officers to scan or manually enter access codes, verify visitors and record entry and exit.

### Application C: Estate Management Dashboard

Platform: Web.

Purpose:
Allow estate administrators to manage residents, properties, security personnel, visitor activity, access policies and reports.

All three applications must communicate with one central backend and database.

The backend is the single source of truth for authentication, permissions, visitor records, access validation and gate activity.

---

# 3. TECHNOLOGY STACK

Use the following stack unless an existing project contains a documented and approved alternative.

## 3.1 Backend

- Python 3.12 or a compatible supported version.
- Django.
- Django REST Framework.
- PostgreSQL.
- JWT authentication using Simple JWT.
- Redis for caching and background task infrastructure where required.
- Celery for asynchronous tasks where appropriate.
- OpenAPI / Swagger documentation.
- Pytest or Django testing framework.

Backend responsibilities:

- Authentication.
- User management.
- Resident management.
- Estate and property management.
- Visitor management.
- Invitation management.
- Access credential generation.
- QR verification.
- Gate operations.
- Notifications.
- Reporting.
- Audit logging.
- System configuration.

## 3.2 Resident and Security Mobile Applications

- React Native.
- Expo.
- TypeScript.
- Expo Router.
- React Query / TanStack Query.
- Zustand for appropriate client-side state.
- React Hook Form.
- Zod validation.
- Expo Camera for QR scanning.
- Expo Notifications.
- Secure token storage using Expo SecureStore.

Both applications should share reusable components, API services, authentication utilities and design tokens where appropriate.

Do not expose administrative functions inside the resident application.

Do not expose unrestricted resident management inside the security application.

## 3.3 Administration Dashboard

- Next.js.
- TypeScript.
- Tailwind CSS.
- shadcn/ui.
- TanStack Query.
- React Hook Form.
- Zod.
- Recharts for analytics where appropriate.

The dashboard must be responsive and support desktop, tablet and mobile browser layouts.

## 3.4 Infrastructure

- GitHub.
- Docker and Docker Compose.
- Managed PostgreSQL.
- Cloud-hosted Django backend.
- Production web hosting for Next.js.
- Firebase Cloud Messaging.
- Secure object storage where necessary.
- GitHub Actions for CI/CD.
- Automated backups.
- Application monitoring.

Do not hardcode credentials, API keys, database passwords or production secrets.

Use environment variables and provide `.env.example` files.

---

# 4. SYSTEM ARCHITECTURE

Follow a modular architecture.

```text
estate-access-platform/
│
├── backend/
│   ├── config/
│   ├── apps/
│   │   ├── authentication/
│   │   ├── users/
│   │   ├── estates/
│   │   ├── properties/
│   │   ├── residents/
│   │   ├── visitors/
│   │   ├── access_control/
│   │   ├── gate_management/
│   │   ├── notifications/
│   │   ├── reports/
│   │   ├── audit_logs/
│   │   └── system_settings/
│   ├── tests/
│   ├── requirements/
│   └── manage.py
│
├── mobile/
│   ├── packages/
│   │   ├── shared/
│   │   ├── api/
│   │   ├── components/
│   │   └── theme/
│   │
│   ├── resident-app/
│   └── security-app/
│
├── admin-dashboard/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── lib/
│   └── services/
│
├── documentation/
│   ├── requirements/
│   ├── architecture/
│   ├── database/
│   ├── api/
│   ├── ui-ux/
│   ├── security/
│   ├── testing/
│   └── deployment/
│
├── infrastructure/
│   ├── docker/
│   ├── deployment/
│   └── monitoring/
│
├── .github/
│   └── workflows/
│
└── README.md
```

Adapt this structure to the repository if it already exists. Do not destroy or unnecessarily restructure working code.

## Architecture principles

1. Backend and frontend must remain independently deployable.
2. All applications must communicate through documented APIs.
3. Business logic must live in the backend.
4. Database operations must be performed through appropriate backend services.
5. The mobile applications must never directly access privileged database operations.
6. Shared UI components must be reusable.
7. Authentication and authorisation must be enforced centrally.
8. Every sensitive operation must be auditable.
9. Design for future multi-estate support without introducing unnecessary complexity into the first release.

---

# 5. USER ROLES AND PERMISSIONS

Implement role-based access control.

## 5.1 Super Administrator

Responsibilities:

- Manage the entire platform.
- Create and manage estates.
- Create estate administrators.
- Configure platform settings.
- Monitor platform activity.
- Manage subscription functionality if introduced later.

## 5.2 Estate Administrator

Responsibilities:

- Manage estate information.
- Register and approve residents.
- Manage buildings and units.
- Manage security officers.
- Monitor visitors.
- Revoke access credentials.
- Generate reports.
- Review audit records.
- Configure estate access policies.

## 5.3 Estate Manager

Responsibilities:

- Monitor estate operations.
- Review visitor activity.
- Review security incidents.
- Manage permitted administrative activities.

Permissions must be configurable and limited to assigned estates.

## 5.4 Resident

Responsibilities:

- Access personal resident profile.
- Create visitor invitations.
- Generate access credentials.
- Share visitor passes.
- Cancel invitations.
- View personal visitor history.
- Receive notifications.

Residents must not access other residents' private visitor information.

## 5.5 Security Supervisor

Responsibilities:

- Manage assigned security personnel where authorised.
- Monitor gate operations.
- Review entry and exit records.
- Review rejected access attempts.
- Handle incidents.

## 5.6 Security Officer

Responsibilities:

- Log into assigned security devices.
- Scan QR codes.
- Enter access codes.
- View permitted visitor information.
- Record visitor entry and departure.
- Report incidents.

Security officers must not create or modify resident accounts.

## 5.7 Household Member

Optional functionality:

- Resident-authorised family members may generate visitor invitations.
- Permissions must be granted by the primary resident or management.
- Household members must have independent accounts and audit records.

---

# 6. DATABASE DESIGN

Use PostgreSQL and Django ORM.

Design normalised database models with appropriate relationships, indexes, constraints and timestamps.

Every important record should include:

- Unique identifier.
- Creation timestamp.
- Last modification timestamp where applicable.
- Appropriate estate relationship.
- Relevant ownership or creator relationship.
- Status where required.

## 6.1 Core models

### Estate

Fields:

- id
- name
- estate_code
- address
- contact_email
- contact_phone
- logo
- timezone
- status
- created_at
- updated_at

### User

Fields:

- id
- email
- phone_number
- password
- first_name
- last_name
- role
- is_active
- is_verified
- last_login
- created_at
- updated_at

Use Django's custom user model from the beginning.

### Property

Fields:

- id
- estate_id
- name
- property_type
- description
- status

### ResidentialUnit

Fields:

- id
- property_id
- unit_number
- floor
- block
- status

Enforce uniqueness of unit identifiers within the appropriate property or estate scope.

### ResidentProfile

Fields:

- id
- user_id
- estate_id
- resident_reference
- identification_reference
- resident_type
- approval_status
- approved_by
- approved_at

Do not store unnecessary identity document data. Protect any sensitive information that is genuinely required.

### ResidentUnitAssignment

Fields:

- id
- resident_id
- unit_id
- relationship_type
- is_primary
- start_date
- end_date
- status

Support residents who have more than one authorised unit where the estate permits it.

### Visitor

Fields:

- id
- full_name
- phone_number
- vehicle_registration
- notes
- created_at

### VisitorInvitation

Fields:

- id
- visitor_id
- resident_id
- estate_id
- unit_id
- visit_date
- valid_from
- valid_until
- access_type
- usage_limit
- usage_count
- status
- created_at
- updated_at

### AccessCredential

Fields:

- id
- invitation_id
- credential_type
- token_hash
- status
- expires_at
- max_uses
- uses_count
- created_at
- revoked_at

Never store sensitive access tokens in plaintext when they can be stored as securely hashed values.

### GateDevice

Fields:

- id
- estate_id
- gate_name
- device_identifier
- status
- last_seen_at

### SecurityShift

Fields:

- id
- officer_id
- gate_device_id
- shift_start
- shift_end
- status

### AccessEvent

Fields:

- id
- estate_id
- invitation_id
- credential_id
- visitor_id
- gate_device_id
- officer_id
- event_type
- event_status
- event_time
- rejection_reason
- metadata

Event types should include:

- ENTRY
- EXIT
- REJECTED_ENTRY
- REJECTED_EXIT
- MANUAL_OVERRIDE

### Notification

Fields:

- id
- user_id
- notification_type
- title
- message
- related_object_type
- related_object_id
- read_at
- created_at

### AuditLog

Fields:

- id
- estate_id
- actor_id
- action
- resource_type
- resource_id
- previous_values
- new_values
- ip_address
- user_agent
- created_at

### EstateSettings

Include configurable settings for:

- Default visitor validity.
- Maximum invitation duration.
- Single-use or multi-use policies.
- QR access enablement.
- Manual code enablement.
- Visitor information requirements.
- Notification preferences.
- Gate access policies.
- Data retention.

## 6.2 Database requirements

- Use UUIDs for externally exposed resource identifiers where appropriate.
- Use foreign keys.
- Add database indexes for frequently queried records.
- Enforce uniqueness constraints.
- Use database transactions for sensitive operations.
- Avoid deleting records required for security investigations.
- Use soft deletion only where appropriate.
- Preserve historical visitor and access records.
- Implement migrations.
- Avoid unnecessary duplicate data.

Document the complete entity relationship diagram before building dependent modules.

---

# 7. AUTHENTICATION AND AUTHORISATION

Implement JWT authentication with access and refresh tokens.

Required functionality:

- Login.
- Logout.
- Refresh token.
- Password recovery.
- Password reset.
- Account activation.
- Session expiry.
- Role verification.
- Device registration for notifications.
- Account suspension.

## Registration

Residents must be registered or approved through an estate-approved process.

Support:

1. Administrator-created resident accounts.
2. Resident self-registration.
3. Estate reference verification.
4. Administrator approval.
5. Account activation.

Do not automatically approve an unverified resident.

## Permission requirements

Every protected API endpoint must check:

- Authentication.
- User role.
- Estate membership.
- Resource ownership.
- Relevant action permission.

Never rely on frontend visibility as the only permission control.

Prevent horizontal privilege escalation, IDOR and cross-estate data leakage.

---

# 8. VISITOR ACCESS MANAGEMENT ENGINE

This is the central business module.

Implement it as a dedicated service layer rather than placing all logic inside API views.

## 8.1 Create visitor invitation

A resident should be able to:

1. Enter visitor name.
2. Enter visitor phone number.
3. Enter visit date.
4. Select validity period.
5. Select access type.
6. Add vehicle registration if necessary.
7. Submit invitation.

Backend must validate:

- Resident approval.
- Resident status.
- Estate membership.
- Unit authorisation.
- Date validity.
- Estate access policy.
- Invitation limits.

## 8.2 Credential generation

Generate unpredictable, unique access credentials.

Requirements:

- Cryptographically secure random generation.
- No sequential or guessable codes.
- Configurable code length.
- Collision detection.
- Expiration enforcement.
- Revocation support.
- Usage limit enforcement.

Do not use a visitor's phone number, apartment number or resident ID as an access code.

## 8.3 QR code generation

QR codes should contain an opaque, unpredictable token or signed credential.

Do not embed:

- Resident passwords.
- Visitor personal information.
- Database IDs as the sole security mechanism.
- Sensitive personal records.

QR codes must be validated through the backend.

## 8.4 Verification process

Implement a dedicated verification service.

Validation order:

1. Authenticate the security officer.
2. Verify the assigned estate and gate.
3. Retrieve the credential.
4. Validate credential integrity.
5. Validate estate association.
6. Validate invitation status.
7. Validate the validity period.
8. Check remaining permitted uses.
9. Check whether the visitor is already checked in.
10. Apply access policy.
11. Return an appropriate verification response.

Possible outcomes:

- VALID
- EXPIRED
- CANCELLED
- REVOKED
- ALREADY_USED
- NOT_YET_VALID
- INVALID
- ALREADY_CHECKED_IN
- REQUIRES_MANUAL_REVIEW

## 8.5 Atomic access operations

One-time access must be protected against concurrent requests.

Use database transactions and row locking where appropriate.

The system must not permit two officers to successfully consume the same one-time credential.

Credential consumption and entry event creation must succeed or fail together.

Do not consume a credential merely because a QR code was scanned. Consume it when admission is successfully committed.

## 8.6 Visitor check-in and check-out

Check-in:

- Verify invitation.
- Confirm valid admission.
- Record entry timestamp.
- Record officer.
- Record gate.
- Update current visitor status.
- Notify resident.

Check-out:

- Retrieve active visitor entry.
- Verify officer permission.
- Record exit timestamp.
- Link exit to original entry.
- Update current visitor status.
- Notify resident if configured.

Prevent duplicate active check-ins and unmatched exits.

## 8.7 Manual override

Provide an authorised exception process.

Requirements:

- Restricted to permitted roles.
- Mandatory justification.
- Officer identity.
- Timestamp.
- Gate identification.
- Audit record.
- Optional supervisor approval.

Never silently bypass access validation.

---

# 9. RESIDENT MOBILE APPLICATION

Build a professional, intuitive Android application.

## Required screens

1. Splash screen.
2. Onboarding.
3. Registration.
4. Login.
5. Password recovery.
6. Resident home dashboard.
7. Create visitor invitation.
8. Invitation confirmation.
9. Digital visitor pass.
10. QR code screen.
11. Active invitations.
12. Expired invitations.
13. Cancelled invitations.
14. Visitor history.
15. Notification centre.
16. Resident profile.
17. Account settings.
18. Help and support.

## Dashboard requirements

Display:

- Resident greeting.
- Apartment information.
- Create visitor pass button.
- Active invitations.
- Expected visitors.
- Recent visitor activity.
- Notification indicator.

## Visitor pass requirements

Display:

- Visitor name.
- Access code.
- QR code.
- Authorising resident.
- Property or unit.
- Validity period.
- Access type.
- Current status.

Provide:

- Share via WhatsApp.
- Share via SMS.
- Native Android share functionality.
- Copy access code.
- Cancel invitation.

Never place private backend credentials inside the application.

## Mobile UX requirements

- Fast navigation.
- Responsive layouts.
- Clear loading states.
- Empty states.
- Form validation.
- Accessible controls.
- Error recovery.
- Network error handling.
- Secure token storage.
- Appropriate Android permissions.

---

# 10. SECURITY GATE APPLICATION

Build a dedicated interface optimised for fast visitor verification.

## Required screens

1. Security login.
2. Gate dashboard.
3. QR scanner.
4. Manual access code entry.
5. Verification loading screen.
6. Approved visitor screen.
7. Rejected visitor screen.
8. Visitor detail screen.
9. Check-in confirmation.
10. Check-out screen.
11. Visitor log.
12. Rejection log.
13. Incident reporting.
14. Security profile.
15. Shift information.

## Gate dashboard

Display:

- Visitors admitted today.
- Visitors currently inside.
- Visitors who have exited.
- Rejected access attempts.
- Current gate.
- Logged-in officer.
- Current shift.

## QR scanner

Requirements:

- Camera permission handling.
- QR detection.
- Duplicate scan protection.
- Loading indicator.
- Immediate backend verification.
- Clear success or failure feedback.

## Approved screen

Show only the information required for gate operations:

- Visitor name.
- Resident name.
- Apartment number.
- Visit validity.
- Vehicle registration where applicable.
- Admission status.

Provide a clear check-in action.

## Rejected screen

Display the appropriate reason:

- Expired code.
- Invalid code.
- Cancelled invitation.
- Already used.
- Revoked access.
- Wrong estate.
- Not yet valid.

Never disclose sensitive internal system information to unauthorised officers or visitors.

---

# 11. ESTATE MANAGEMENT DASHBOARD

Build a professional administration portal.

## Navigation

- Overview.
- Residents.
- Properties and Units.
- Visitors.
- Access Management.
- Gate Monitoring.
- Security Personnel.
- Reports and Analytics.
- Notifications.
- Incidents.
- Audit Logs.
- Estate Settings.

## Dashboard overview

Display:

- Registered residents.
- Residential units.
- Visitors today.
- Visitors currently inside.
- Expected visitors.
- Active credentials.
- Rejected access attempts.
- Security personnel on duty.

Include appropriate charts and activity timelines.

## Resident management

Features:

- Register resident.
- Edit resident.
- Approve resident.
- Reject registration.
- Suspend resident.
- Deactivate account.
- Assign unit.
- View resident details.
- View resident visitor history.

## Property management

Features:

- Create buildings.
- Create blocks.
- Create residential units.
- Assign residents.
- Update property information.
- Manage unit occupancy.

## Visitor management

Features:

- Search visitors.
- View invitations.
- Filter by date.
- View current visitor status.
- View entry and exit records.
- Review rejected access attempts.

## Gate monitoring

Display:

- Gate name.
- Security officer.
- Visitor.
- Event type.
- Event time.
- Verification outcome.

Use appropriate polling or real-time updates.

Do not claim real-time functionality if the underlying connection only uses periodic polling.

## Reports

Provide:

- Daily visitor reports.
- Weekly visitor reports.
- Monthly visitor reports.
- Resident activity reports.
- Gate activity reports.
- Rejected access reports.
- Currently-inside reports.
- Security personnel activity reports.

Support appropriate CSV or PDF exports.

All reports must respect estate and user permissions.

## Audit logs

Track:

- Account creation.
- Resident approval.
- Resident suspension.
- Invitation creation.
- Invitation cancellation.
- Access overrides.
- Security login.
- Gate verification.
- Report exports.
- Settings changes.

Audit records must not be editable by ordinary users.

---

# 12. NOTIFICATION SYSTEM

Implement Firebase Cloud Messaging for push notifications.

Notification events:

- Visitor invitation created.
- Visitor pass generated.
- Visitor invitation cancelled.
- Visitor arrived.
- Visitor admitted.
- Visitor rejected.
- Visitor exited.
- Resident account approved.
- Resident account suspended.
- Security incident recorded where relevant.

Requirements:

- Store notification records.
- Track delivery attempts where supported.
- Support notification preferences.
- Avoid duplicate notifications.
- Handle invalid device tokens.
- Allow notification history.

Push notification delivery must not be treated as proof that an access operation succeeded.

For WhatsApp sharing, use the native sharing mechanism initially. Do not assume WhatsApp API integration is included.

---

# 13. UI/UX DESIGN SYSTEM

Design the entire platform before implementing detailed screens.

## Design direction

The visual identity should communicate:

- Security.
- Trust.
- Professionalism.
- Simplicity.
- Reliability.
- Modern residential management.

Use a clean, premium interface.

Recommended starting palette:

- Deep navy: #142B45
- Primary blue: #2563EB
- Background: #F7F9FC
- Surface: #FFFFFF
- Text: #172033
- Secondary text: #687386
- Success: #16A36A
- Warning: #D99A26
- Danger: #DC4444

These are initial design tokens and may be adjusted after estate branding approval.

## Typography

Use a consistent modern sans-serif family.

Recommended:

- Inter.
- Manrope.
- DM Sans.

## Component library

Create reusable:

- Buttons.
- Input fields.
- Dropdowns.
- Date pickers.
- Dialogs.
- Cards.
- Status badges.
- Data tables.
- Search bars.
- Pagination.
- Tabs.
- Navigation components.
- Loading skeletons.
- Empty states.
- Error states.
- Confirmation dialogs.
- Notification components.

## UX requirements

Every screen must include the appropriate:

- Initial state.
- Loading state.
- Success state.
- Error state.
- Empty state.
- Disabled state.
- Validation state.

Avoid placeholder buttons.

All controls must perform their advertised actions.

Ensure consistency across the resident, security and administration applications without forcing all three to use identical layouts.

---

# 14. API DEVELOPMENT STANDARDS

Use REST APIs with versioning.

Base URL:

`/api/v1/`

## Authentication

```text
POST /api/v1/auth/login/
POST /api/v1/auth/logout/
POST /api/v1/auth/token/refresh/
POST /api/v1/auth/password/forgot/
POST /api/v1/auth/password/reset/
GET  /api/v1/auth/me/
```

## Residents

```text
GET    /api/v1/residents/
POST   /api/v1/residents/
GET    /api/v1/residents/{id}/
PATCH  /api/v1/residents/{id}/
POST   /api/v1/residents/{id}/approve/
POST   /api/v1/residents/{id}/suspend/
```

## Properties

```text
GET    /api/v1/properties/
POST   /api/v1/properties/
GET    /api/v1/units/
POST   /api/v1/units/
GET    /api/v1/units/{id}/
PATCH  /api/v1/units/{id}/
```

## Visitors and invitations

```text
GET    /api/v1/visitors/
POST   /api/v1/visitors/
GET    /api/v1/visitors/{id}/

GET    /api/v1/invitations/
POST   /api/v1/invitations/
GET    /api/v1/invitations/{id}/
POST   /api/v1/invitations/{id}/cancel/
POST   /api/v1/invitations/{id}/credentials/
```

## Gate operations

```text
POST   /api/v1/gate/verify/
POST   /api/v1/gate/check-in/
POST   /api/v1/gate/check-out/
GET    /api/v1/gate/visitors-inside/
GET    /api/v1/gate/activity/
POST   /api/v1/gate/incidents/
```

## Administration

```text
GET    /api/v1/admin/dashboard/
GET    /api/v1/admin/gate-activity/
GET    /api/v1/admin/reports/
GET    /api/v1/admin/audit-logs/
GET    /api/v1/admin/security-personnel/
POST   /api/v1/admin/security-personnel/
GET    /api/v1/admin/settings/
PATCH  /api/v1/admin/settings/
```

These are proposed endpoint contracts. Implement the final endpoint names and request/response schemas consistently in the backend, frontend API clients and OpenAPI documentation.

Use:

- Pagination.
- Filtering.
- Search.
- Consistent response formats.
- Meaningful HTTP status codes.
- Appropriate validation errors.
- API permission checks.
- Idempotency protection for sensitive operations where appropriate.

Document every endpoint.

---

# 15. SECURITY REQUIREMENTS

Security is a core requirement, not an optional enhancement.

Implement:

1. HTTPS throughout production.
2. Password hashing.
3. JWT expiry and refresh handling.
4. Backend-enforced role permissions.
5. Estate-level data isolation.
6. Rate limiting.
7. Secure credential generation.
8. Secure QR verification.
9. Database transaction protection.
10. Audit logging.
11. Secure device registration.
12. Database backups.
13. Environment-based secrets.
14. Input validation.
15. Protection against SQL injection.
16. Protection against XSS and CSRF where applicable.
17. Restricted file uploads.
18. Account suspension and session revocation.
19. Access monitoring.
20. Data retention and privacy controls.

Never:

- Store plaintext passwords.
- Hardcode secrets.
- Trust client-side access decisions.
- Allow residents to retrieve another resident's records.
- Allow officers to approve invalid credentials.
- Permit credential reuse beyond configured limits.
- Expose sensitive information through QR codes.
- Delete important audit records without an approved retention process.

Provide a documented security review before production deployment.

---

# 16. TESTING STRATEGY

Implement tests throughout development.

## Backend tests

Test:

- Authentication.
- Permissions.
- Resident approval.
- Property assignment.
- Invitation creation.
- Credential generation.
- Expiration.
- Cancellation.
- One-time use.
- Multiple-use limits.
- QR validation.
- Concurrent verification.
- Entry and exit.
- Audit logs.
- Notifications.

## Mobile tests

Test:

- Login.
- Registration.
- Navigation.
- Form validation.
- Invitation creation.
- QR rendering.
- QR scanning.
- Sharing.
- Notification handling.
- Network failures.

## Dashboard tests

Test:

- Authentication.
- Role restrictions.
- Resident management.
- Unit management.
- Visitor monitoring.
- Filtering.
- Reporting.
- Audit logs.

## Integration tests

Verify that all three applications communicate correctly with the same backend.

## Critical acceptance scenarios

### Scenario 1: Valid visitor

Resident creates invitation.

Visitor receives access pass.

Security scans QR code.

Backend approves access.

Entry is recorded.

Resident receives notification.

### Scenario 2: Expired visitor

Resident creates invitation.

Invitation expires.

Visitor arrives.

Security scans QR code.

Backend rejects access.

Rejection is logged.

### Scenario 3: Cancelled invitation

Resident cancels invitation.

Visitor presents code.

Backend rejects access.

### Scenario 4: Reused one-time code

Visitor is admitted once.

Credential becomes consumed.

Second attempt is rejected.

### Scenario 5: Visitor departure

Visitor is checked in.

Security records exit.

Dashboard updates visitor status.

### Scenario 6: Resident suspension

Management suspends resident.

Future invitation creation is blocked.

Existing credentials follow the estate's documented revocation policy.

### Scenario 7: Concurrent access

Two officers attempt to consume the same one-time credential simultaneously.

Only one admission can succeed.

---

# 17. PERFORMANCE AND SCALABILITY

Design for:

- Hundreds or thousands of residents.
- Multiple security officers.
- Multiple gates.
- Concurrent access verification.
- Large visitor histories.
- Growing database records.

Performance requirements:

- Index frequently queried columns.
- Use pagination.
- Avoid unnecessary database queries.
- Use database transactions.
- Use background tasks for noncritical asynchronous operations.
- Cache suitable dashboard statistics.
- Optimise mobile network requests.
- Monitor backend response times.
- Configure database connection management.

Initial performance targets:

- Normal access verification: under 2 seconds under agreed test conditions.
- Common dashboard requests: under 3 seconds under agreed test conditions.
- Reliable concurrent access operations.
- No duplicate successful one-time credential consumption.

Validate these targets through load testing.

---

# 18. DEVELOPMENT WORKFLOW

Follow the development phases in order.

## PHASE 1: PROJECT DISCOVERY

Tasks:

1. Inspect the existing repository.
2. Identify existing code and technology.
3. Read existing documentation.
4. Identify missing requirements.
5. Establish development environments.
6. Define the user roles.
7. Document business rules.
8. Prepare project architecture.

Deliverables:

- Requirements specification.
- System architecture.
- Project structure.
- Development plan.

Do not overwrite existing working code without understanding its purpose.

## PHASE 2: DATABASE AND API DESIGN

Tasks:

1. Design database entities.
2. Define relationships.
3. Create ERD.
4. Define API contracts.
5. Define permissions.
6. Define access verification rules.
7. Document data flows.

Deliverables:

- Database schema.
- ERD.
- API documentation.
- Permission matrix.

## PHASE 3: UI/UX DESIGN

Design all applications.

Resident:

- Authentication.
- Dashboard.
- Invitation forms.
- Access pass.
- Visitor history.
- Notifications.

Security:

- Authentication.
- Gate dashboard.
- QR scanner.
- Verification.
- Entry and exit.
- Visitor logs.

Admin:

- Dashboard.
- Resident management.
- Properties.
- Visitors.
- Gate monitoring.
- Reports.
- Settings.

Deliverables:

- Design system.
- Wireframes.
- High-fidelity screens.
- Responsive layouts.
- Approved user flows.

## PHASE 4: BACKEND DEVELOPMENT

Implement:

1. Django configuration.
2. PostgreSQL connection.
3. Custom user model.
4. Authentication.
5. Roles and permissions.
6. Estate management.
7. Property management.
8. Resident management.
9. Visitor management.
10. Invitation management.
11. Credential generation.
12. QR verification.
13. Gate management.
14. Entry and exit.
15. Notifications.
16. Reports.
17. Audit logs.

Write and execute tests as each module is completed.

## PHASE 5: RESIDENT APPLICATION

Implement the resident app against the approved API contracts.

Connect all screens to actual backend functionality.

## PHASE 6: SECURITY APPLICATION

Implement the gate application.

Prioritise scanning performance, clear verification results and secure admission workflows.

## PHASE 7: ADMIN DASHBOARD

Implement the management portal.

Connect all management modules to the backend.

## PHASE 8: INTEGRATION

Connect all applications.

Verify complete end-to-end workflows.

## PHASE 9: QUALITY ASSURANCE

Conduct functional, security, device, performance and acceptance testing.

Resolve critical and high-priority defects.

## PHASE 10: DEPLOYMENT

Configure:

- Production backend.
- Production database.
- Frontend hosting.
- Android application builds.
- Push notifications.
- SSL.
- Domain.
- Backups.
- Monitoring.
- Google Play Store submission.

Deliver the completed applications and documentation.

---

# 19. TEN-WEEK DELIVERY TARGET

Use the following schedule as the initial project baseline.

| Week | Main milestone |
|---|---|
| 1 | Requirements and system analysis |
| 2 | Architecture, database design and UI/UX |
| 3 | Backend foundation and authentication |
| 4 | Visitor and access management |
| 5 | Resident application |
| 6 | Security application |
| 7 | Administration dashboard |
| 8 | Integration and notifications |
| 9 | Testing and corrections |
| 10 | Deployment, training and handover |

Backend and frontend work may proceed in parallel after architecture, design and API contracts are sufficiently approved.

Track dependencies and do not sacrifice security or correctness simply to meet a deadline.

---

# 20. CODING STANDARDS

Follow these rules across the project.

### General

- Write clean, readable and maintainable code.
- Use meaningful names.
- Avoid unnecessary duplication.
- Separate business logic from presentation.
- Keep modules focused.
- Use appropriate types.
- Add comments for complex business rules.
- Avoid oversized files and components.
- Reuse established project patterns.

### Python

- Follow PEP 8.
- Use Django ORM.
- Use serializers for API validation.
- Use service classes for complex business operations.
- Use permissions and authentication classes.
- Handle exceptions properly.
- Write unit and integration tests.

### TypeScript

- Enable strict TypeScript where practical.
- Avoid unnecessary `any`.
- Use reusable typed components.
- Separate API calls from UI components.
- Use schema-based validation.
- Handle loading and error states.
- Keep state management predictable.

### Database

- Use migrations.
- Avoid destructive migrations without review.
- Use transactions for critical operations.
- Add appropriate indexes.
- Enforce database constraints.
- Preserve important historical records.

### Git

Use descriptive commits.

Suggested convention:

```text
feat: add resident visitor invitations
feat: implement QR verification
fix: prevent duplicate visitor check-in
fix: handle expired credentials
refactor: separate access validation service
test: add concurrent credential verification tests
docs: update API documentation
```

---

# 21. AI AGENT OPERATING RULES

These instructions are mandatory.

## Before implementing a task

1. Inspect the relevant files.
2. Understand the existing architecture.
3. Identify dependencies.
4. Check existing components and utilities.
5. Identify affected database models and APIs.
6. Review applicable security requirements.
7. Create a concise implementation plan.

## While implementing

1. Work in small, logical steps.
2. Reuse existing code where appropriate.
3. Maintain consistent naming.
4. Do not introduce unnecessary dependencies.
5. Do not create duplicate API services.
6. Do not create duplicate database models.
7. Do not bypass authentication.
8. Do not leave fake data in production features.
9. Implement actual functionality.
10. Update documentation.

## After implementing

1. Run relevant tests.
2. Check for TypeScript errors.
3. Check Python errors.
4. Check migrations.
5. Verify API functionality.
6. Verify permissions.
7. Verify UI behaviour.
8. Fix discovered regressions.
9. Summarise completed work.
10. Identify remaining limitations.

## When encountering errors

- Investigate the root cause.
- Read the error message.
- Inspect relevant configuration.
- Reproduce the problem.
- Implement a proper fix.
- Test the fix.

Do not randomly modify unrelated files.

## When information is missing

Do not invent business rules.

If a missing requirement could affect access security, resident privacy, financial commitments or data integrity, identify the uncertainty and request clarification.

For minor implementation decisions, use reasonable engineering defaults and document them.

---

# 22. DEFINITION OF DONE

A feature is complete only when:

- Its requirements are implemented.
- Its UI is functional.
- Its API is connected.
- Its permissions are enforced.
- Its data is stored correctly.
- Its validation works.
- Its loading and error states work.
- Its tests pass.
- Its documentation is updated.
- Its integration has been verified.

A screen with static data is not a completed feature.

A button without a working action is not a completed feature.

An API without appropriate permissions is not a completed feature.

A successful local build does not mean production deployment is complete.

---

# 23. PRODUCTION DEPLOYMENT REQUIREMENTS

Before launch, verify:

- Production environment variables.
- Database migrations.
- SSL certificates.
- API security.
- User roles and permissions.
- Resident registration process.
- Gate device configuration.
- Push notification credentials.
- Database backups.
- Logging and monitoring.
- Application signing.
- Privacy policy.
- Google Play requirements.
- Administrator training.
- Security officer training.
- Resident instructions.
- Support arrangements.

Prepare a rollback and recovery procedure.

Never deploy destructive database changes without an approved backup and recovery plan.

---

# 24. FINAL DELIVERY REQUIREMENTS

The final project must contain:

1. Functional resident Android application.
2. Functional security Android application.
3. Functional estate management dashboard.
4. Django REST backend.
5. PostgreSQL database.
6. Authentication and authorisation.
7. Visitor invitation system.
8. QR and numerical access credentials.
9. Real-time backend verification.
10. Entry and exit monitoring.
11. Push notification system.
12. Reporting and analytics.
13. Audit logging.
14. Technical documentation.
15. API documentation.
16. Database documentation.
17. Deployment documentation.
18. User manuals.
19. Testing reports.
20. Source code and agreed ownership handover.

Provide three months of post-deployment technical support according to the approved support agreement.

---

# 25. INITIAL PROJECT EXECUTION INSTRUCTION

When this skill is activated, do not immediately start generating the entire application.

Begin with the following:

**STEP 1 — Repository inspection**

Inspect the existing repository and identify:

- Existing applications.
- Installed dependencies.
- Current folder structure.
- Existing database configuration.
- Existing UI components.
- Existing API integrations.
- Existing authentication.
- Current development status.

**STEP 2 — Project assessment**

Prepare a report identifying:

- What already exists.
- What is missing.
- What needs improvement.
- Potential technical problems.
- Dependencies and risks.

**STEP 3 — Architecture preparation**

Prepare:

- System architecture.
- Database ERD.
- User role and permission matrix.
- API architecture.
- Application communication flow.
- Development milestones.

**STEP 4 — UI/UX preparation**

Prepare the complete design system and screen inventory for all three applications.

**STEP 5 — Approval gate**

Present the architecture and design for review before implementing major application modules.

**STEP 6 — Progressive implementation**

Build the backend and applications in clearly defined milestones.

After each milestone:

- Run tests.
- Verify integration.
- Update documentation.
- Report progress.
- Identify outstanding work.

**STEP 7 — Final verification**

Verify all critical visitor access workflows from resident invitation creation through security verification, admission, departure and administration reporting.

The final goal is a complete, reliable and production-ready Estate Visitor Access Management Platform.

---

# END OF MASTER SKILL
