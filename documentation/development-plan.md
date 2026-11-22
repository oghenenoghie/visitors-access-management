# Development Plan

Baseline from the master skill's ten-week schedule, broken into milestones. Each milestone ends with: tests run, integration verified, documentation updated, progress reported, outstanding work listed.

| Milestone | Week | Scope | Exit criteria |
|---|---|---|---|
| M0 Approval gate | 1-2 | Architecture, ERD, permission matrix, open questions, design system and screen inventory | Owner approves docs and answers Q1-Q3 at minimum |
| M1 Foundation | 3 | Monorepo scaffold, Docker Compose (Postgres, Redis), Django project, custom user, estates, memberships, CI | CI green, migrations clean, `.env.example` per app |
| M2 Auth and roles | 3 | JWT login/refresh/logout, admin-issued password reset codes, TOTP 2FA for dashboard accounts, activation by approval, role permissions, estate-scoped base queryset, audit log base | **Done** — permission tests and negative IDOR tests pass (95 tests, 98% coverage) |
| M3 Residents and properties | 4 | Properties, streets, units, resident registration with encrypted ID upload, approval, assignments, bulk data import | **Done** — resident approval/rejection/suspension, assignments, encrypted identity storage and atomic CSV import; 130 tests pass |
| M4 Access engine | 4 | Invitations, credentials, verify, check-in/out, override, one-time and multi-use, concurrency | **Done and merged** — PR #6 merged 18 Nov 2026 at `78ef1e877cd5ba936e36af540780ea756a9fd4dd`; PostgreSQL-backed test suite: 141 passed |
| M5 Resident app | 5 | Flutter design system, authentication, dashboard, invitation creation, digital pass/QR, sharing and visitor history | **In progress** — first API-connected Flutter slice on `feat/m5-resident-app`; Mobile CI is green on `main`. Remaining: Android device verification and API integration acceptance, run from `documentation/testing/android-device-acceptance.md` |
| M6 Security app | 6 | Login, shift, scanner, manual code, approve/reject, check-in/out, logs, incidents | Verify under 2 s on test conditions |
| M7 Admin dashboard | 7 | Overview, residents, units, visitors, gate monitoring, reports, audit logs, settings | **Done and merged** — PR #10 plus ESLint fixes #11/#12; dashboard and backend CI passed for #12 |
| M8 Integration and notifications | 8 | FCM, end-to-end flows across all apps, reports export | **In progress** — server notification inbox, encrypted FCM device registration, Celery delivery and visitor-event notifications in PR #13; mobile SDK integration and end-to-end verification remain |
| M9 QA and security review | 9 | Functional, security, device, performance, UAT, defect fixes | Critical/high defects closed, security review documented |
| M10 Deployment | 10 | Production, backups, monitoring, signing, Play submission, training, handover | Rollback and recovery procedure tested |

## Alignment with the proposal

The proposal fixes client-facing phases: discovery W1, architecture and design W2-W3, development W4-W7, integration and testing W8-W9, deployment W10. The milestone weeks above follow the master skill; M1-M2 may begin during W2-W3 as design work so that the proposal's development window (W4-W7) is not squeezed. Proposal assumptions: the Estate's representative approves within three business days; resident and unit data arrive by end of W3 (needs an import tool, added to M3).

## Parallel work

After M2 and approved API contracts, mobile and dashboard work can begin against the OpenAPI schema while M3 and M4 continue. Design (Phase 3) runs during M1-M2.

## Next action

Complete M8 integration: add Firebase initialization and token lifecycle to both Flutter apps, implement foreground/background notification handling and safe deep links, verify delivery against a Firebase test project, then finish report exports and cross-application end-to-end scenarios.

M3 is complete in code and CI. The estate-code registration path creates only a pending, inactive account; it is not proof of residence. Keep administrator approval mandatory. Q8 remains open: production deployment must configure a private Django storage backend and securely back up `FIELD_ENCRYPTION_KEY` before collecting real identity documents.
