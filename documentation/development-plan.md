# Development Plan

Baseline from the master skill's ten-week schedule, broken into milestones. Each milestone ends with: tests run, integration verified, documentation updated, progress reported, outstanding work listed.

| Milestone | Week | Scope | Exit criteria |
|---|---|---|---|
| M0 Approval gate | 1-2 | Architecture, ERD, permission matrix, open questions, design system and screen inventory | Owner approves docs and answers Q1-Q3 at minimum |
| M1 Foundation | 3 | Monorepo scaffold, Docker Compose (Postgres, Redis), Django project, custom user, estates, memberships, CI | CI green, migrations clean, `.env.example` per app |
| M2 Auth and roles | 3 | JWT login/refresh/logout, password reset, activation, role permissions, estate-scoped base queryset, audit log base | Permission tests green, negative IDOR tests |
| M3 Residents and properties | 4 | Properties, units, resident registration and approval, assignments | Approval flow tested end to end |
| M4 Access engine | 4 | Invitations, credentials, verify, check-in/out, override, one-time and multi-use, concurrency | Seven acceptance scenarios pass, concurrent-consume test passes |
| M5 Resident app | 5 | Design system package, auth, dashboard, create invitation, pass with QR and share, history, notifications | Runs on Android against the real API |
| M6 Security app | 6 | Login, shift, scanner, manual code, approve/reject, check-in/out, logs, incidents | Verify under 2 s on test conditions |
| M7 Admin dashboard | 7 | Overview, residents, units, visitors, gate monitoring, reports, audit logs, settings | Role restrictions tested |
| M8 Integration and notifications | 8 | FCM, end-to-end flows across all apps, reports export | End-to-end scenarios pass |
| M9 QA and security review | 9 | Functional, security, device, performance, UAT, defect fixes | Critical/high defects closed, security review documented |
| M10 Deployment | 10 | Production, backups, monitoring, signing, Play submission, training, handover | Rollback and recovery procedure tested |

## Parallel work

After M2 and approved API contracts, mobile and dashboard work can begin against the OpenAPI schema while M3 and M4 continue. Design (Phase 3) runs during M1-M2.

## Next action

On approval of the M0 documents: start M1 (monorepo scaffold, backend foundation, CI).
