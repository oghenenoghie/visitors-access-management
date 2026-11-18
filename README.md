# Estate Visitor Access Management Platform

Estate platform connecting residents, security officers and administrators:

- **Resident app** (Android, Flutter): create visitor invitations, QR passes, share credentials and view visitor history.
- **Security app** (Android, Flutter): scan or enter codes, verify, record entry and exit.
- **Admin dashboard** (Next.js): residents, units, gate monitoring, reports, audit logs.
- **Backend** (Django REST, PostgreSQL): single source of truth for auth, permissions and access decisions.

## Status

M1 (foundation), M2 (authentication and roles), M3 (residents and properties) and M4 (access engine) are merged to `main`. M4 PR #6 was merged on 18 November 2026 at `78ef1e877cd5ba936e36af540780ea756a9fd4dd`. The access engine includes estate-scoped invitations, hashed QR/manual credentials, gate verification, transactional check-in/out, supervisor override and append-only access events. Its PostgreSQL-backed test suite passed with 141 tests.

M5 is in progress on `feat/m5-resident-app`. The first Flutter vertical slice includes Material 3 foundations, resident sign-in and TOTP challenge handling, secure JWT storage/refresh, resident dashboard, active unit lookup, invitation creation, QR/manual pass display, native sharing and cancellation. FCM remains scheduled for M8. See [M5 implementation notes](documentation/implementation/m5-resident-app.md).

## Documentation

- [Project assessment](documentation/requirements/00-project-assessment.md)
- [Proposal reconciliation](documentation/requirements/proposal-reconciliation.md)
- [Open questions](documentation/requirements/open-questions.md)
- [System architecture](documentation/architecture/system-architecture.md)
- [Database design and ERD](documentation/database/erd.md)
- [Permission matrix](documentation/security/permission-matrix.md)
- [API architecture](documentation/api/api-architecture.md)
- [Development plan](documentation/development-plan.md)

## AI agent setup

Project instructions are in `CLAUDE.md`. Skills are in `.agents/skills/`; `estate-access-platform` is the source of truth and the six specialist skills supplement it. `.mcp.json` configures the Figma MCP server.
