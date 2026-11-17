# Project Assessment (Phase 1)

Date: 2026-11-17. Status: draft for approval.

## What exists

| Area | State |
|---|---|
| Repository | Greenfield. `main` holds only agent skills, `CLAUDE.md` and `.mcp.json`. |
| Applications | None. |
| Dependencies | None installed. |
| Database config | None. |
| UI components / design files | None. No Figma file linked yet. |
| API / authentication | None. |
| Skills | `estate-access-platform` (master) plus six specialists in `.agents/skills/`. |

## What is missing

Everything in the master skill's section 4 layout: `backend/`, `mobile/`, `admin-dashboard/`, `infrastructure/`, `.github/workflows/`, environment templates, CI, and any design.

## Gaps and inconsistencies found in the specification

These are decisions the master skill leaves open or that need a change to its model. They are listed in `open-questions.md`; the proposed handling is in the architecture docs.

1. **Roles are estate-scoped, but `User.role` is a single field.** Estate Managers must be limited to assigned estates, and multi-estate is a stated future goal. Proposed: an `EstateMembership` table (user, estate, role).
2. **No offline behaviour is specified for the gate app.** Verification is backend-only by rule, so a gate with no connectivity cannot admit by app. Proposed: fail closed, with the manual-override process as the only fallback, and explicit offline state in the UI.
3. **Numeric access codes are low entropy.** Hashing does not protect a short numeric code from guessing. Needs estate-scoped lookup, rate limiting and lockout (see architecture).
4. **Suspension policy for existing credentials is undefined** (acceptance scenario 6 says "follows the documented revocation policy", but none exists).
5. **Exit-to-entry link and "currently inside" have no fields.** Proposed: `AccessEvent.entry_event` self reference and a constraint allowing one open entry per invitation.
6. **`Visitor` has no estate or owner**, so one resident's visitor records could be reachable by another. Proposed: add `estate_id` and `created_by_resident_id`.
7. **`AccessCredential` has no estate**, which the gate lookup needs for isolation. Proposed: denormalised `estate_id`.
8. **Incidents** are in the API and screens but have no model. Proposed: `Incident`.
9. **Push device tokens** have no model. Proposed: `DeviceRegistration`.
10. **Admin dashboard "real-time"**: use polling and label it as such (master skill rule).

## Risks

| Risk | Mitigation |
|---|---|
| Double admission on one-time credentials | Row lock plus transaction on check-in, concurrency test in CI from M4. |
| Cross-estate or cross-resident data leakage (IDOR) | Estate-scoped querysets by default, object-level permissions, negative tests per endpoint. |
| Short-code brute force at the gate | Per-device and per-officer rate limit, lockout, audit of failed attempts. |
| Gate unusable with poor connectivity | Lightweight verify payload, clear offline UI, override process. Needs on-site connectivity check before launch. |
| Scope: three apps plus backend in ten weeks | Backend and contracts first, apps in parallel after API contracts are approved. Do not trade security for dates. |
| Play Store requirements (privacy policy, data safety form) | Start the privacy policy in M2; it also drives data-retention settings. |

## Dependencies

Figma file (optional but wanted for design-to-code), Firebase project for FCM, SMS or email provider for activation and password reset, hosting accounts, Google Play developer account, estate branding approval.
