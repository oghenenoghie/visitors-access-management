# Role and Permission Matrix (Phase 2)

Status: draft for approval. Roles come from master skill section 5. Enforcement is in the backend on every endpoint (authentication, role, estate membership, ownership, action). Frontend visibility is never the control.

Legend: ✅ allowed · 🔒 own records only · 🏢 within assigned estate · ⚙️ configurable per estate · ❌ not allowed · — not applicable.

| Capability | Super Admin | Estate Admin | Estate Manager | Resident | Household Member | Security Supervisor | Security Officer |
|---|---|---|---|---|---|---|---|
| Create / manage estates | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Create estate administrators | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Estate settings and access policy | ✅ | 🏢 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Register / approve / suspend residents | ✅ | 🏢 | ⚙️ | ❌ | ❌ | ❌ | ❌ |
| Self-register (pending approval) | — | — | — | ✅ | ❌ | ❌ | ❌ |
| Manage properties and units | ✅ | 🏢 | ⚙️ | ❌ | ❌ | ❌ | ❌ |
| Manage security personnel | ✅ | 🏢 | ❌ | ❌ | ❌ | 🏢 assigned | ❌ |
| Create visitor invitation | ❌ | ❌ | ❌ | 🔒 | 🔒 if granted | ❌ | ❌ |
| Cancel invitation | ✅ | 🏢 | ⚙️ | 🔒 | 🔒 if granted | ❌ | ❌ |
| Revoke credentials | ✅ | 🏢 | ⚙️ | 🔒 own | ❌ | ❌ | ❌ |
| View visitor records | ✅ | 🏢 | 🏢 | 🔒 | 🔒 | 🏢 | gate-relevant only |
| Verify credential (scan or code) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ on shift | ✅ on shift |
| Check in / check out | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ on shift | ✅ on shift |
| Manual override | ❌ | ⚙️ | ❌ | ❌ | ❌ | ✅ with justification | ⚙️ needs supervisor approval |
| Report incident | ✅ | 🏢 | 🏢 | ❌ | ❌ | ✅ | ✅ |
| Review incidents | ✅ | 🏢 | 🏢 | ❌ | ❌ | 🏢 | own reports |
| Gate monitoring and rejected attempts | ✅ | 🏢 | 🏢 | ❌ | ❌ | 🏢 | own gate, own events |
| Reports and exports | ✅ | 🏢 | 🏢 | ❌ | ❌ | 🏢 gate reports | ❌ |
| View resident ID document (each view audited) | ✅ | ✅ authorised only | ❌ | ❌ | ❌ | ❌ | ❌ |
| Issue password reset code | ✅ | 🏢 (not for platform admins) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Audit logs (read-only) | ✅ | 🏢 | ⚙️ | ❌ | ❌ | ❌ | ❌ |
| Edit or delete audit logs | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Notifications | — | 🏢 | 🏢 | 🔒 | 🔒 | 🔒 | 🔒 |

## Rules

- Dashboard accounts (all management roles) require two-factor authentication with an authenticator app (no SMS or email).
- Password reset codes are issued only by administrators; every issue and redemption is audited.
- Resident ID documents open only through short-lived access by authorised administrators; each view is written to the audit log.

- The mobile resident app exposes no administrative functions; the security app exposes no resident management.
- Estate Manager capabilities marked ⚙️ are granted per estate by an Estate Administrator; the default is read-only monitoring.
- Household members act under the primary resident's authority and are granted by that resident or management. Their invitations carry their own identity in the audit trail.
- Security Officer visitor detail is limited to what gate operations need: visitor name, resident name, unit, validity window, vehicle registration, admission status.
- Security roles act only through an active shift at a registered gate device in their estate.
- Suspension of a user revokes all refresh tokens and invalidates sessions immediately.
- Suspending a resident revokes all of their active credentials immediately and blocks new invitations (decision Q1).
- Super Administrator cross-estate reads are audited.

## Test requirement

For each endpoint, tests cover: allowed role, forbidden role, other estate, other resident's object, suspended user, and expired token.
