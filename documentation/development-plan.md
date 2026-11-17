# Development Plan

Baseline from the master skill's ten-week schedule, broken into milestones. Each milestone ends with: tests run, integration verified, documentation updated, progress reported, outstanding work listed.

| Milestone | Week | Scope | Exit criteria |
|---|---|---|---|
| M0 Approval gate | 1-2 | Architecture, ERD, permission matrix, open questions, design system and screen inventory | Owner approves docs and answers Q1-Q3 at minimum |
| M1 Foundation | 3 | Monorepo scaffold, Docker Compose (Postgres, Redis), Django project, custom user, estates, memberships, CI | CI green, migrations clean, `.env.example` per app |
| M2 Auth and roles | 3 | JWT login/refresh/logout, admin-issued password reset codes, TOTP 2FA for dashboard accounts, activation by approval, role permissions, estate-scoped base queryset, audit log base | Permission tests green, negative IDOR tests. **Status: done** (95 tests, 98% coverage) |
| M3 Residents and properties | 4 | Properties, streets, units, resident registration with encrypted ID upload, approval, assignments, bulk data import | Approval flow tested end to end. **Status: in progress** (property/unit API foundation on `feat/m3-residents-properties`) |
| M4 Access engine | 4 | Invitations, credentials, verify, check-in/out, override, one-time and multi-use, concurrency | Seven acceptance scenarios pass, concurrent-consume test passes |
| M5 Resident app | 5 | Design system package, auth, dashboard, create invitation, pass with QR and share, history, notifications | Runs on Android against the real API |
| M6 Security app | 6 | Login, shift, scanner, manual code, approve/reject, check-in/out, logs, incidents | Verify under 2 s on test conditions |
| M7 Admin dashboard | 7 | Overview, residents, units, visitors, gate monitoring, reports, audit logs, settings | Role restrictions tested |
| M8 Integration and notifications | 8 | FCM, end-to-end flows across all apps, reports export | End-to-end scenarios pass |
| M9 QA and security review | 9 | Functional, security, device, performance, UAT, defect fixes | Critical/high defects closed, security review documented |
| M10 Deployment | 10 | Production, backups, monitoring, signing, Play submission, training, handover | Rollback and recovery procedure tested |

## Alignment with the proposal

The proposal fixes client-facing phases: discovery W1, architecture and design W2-W3, development W4-W7, integration and testing W8-W9, deployment W10. The milestone weeks above follow the master skill; M1-M2 may begin during W2-W3 as design work so that the proposal's development window (W4-W7) is not squeezed. Proposal assumptions: the Estate's representative approves within three business days; resident and unit data arrive by end of W3 (needs an import tool, added to M3).

## Parallel work

After M2 and approved API contracts, mobile and dashboard work can begin against the OpenAPI schema while M3 and M4 continue. Design (Phase 3) runs during M1-M2.

## Next action

Continue M3 on `feat/m3-residents-properties`: implement resident profiles and approval, resident-unit assignments, the encrypted identity-document storage adapter, and validated bulk import. Before selecting a production storage provider or finalising self-registration verification, resolve open questions Q6 and Q8. Run the full backend CI suite and verify the OpenAPI schema before merging.
