# Estate Visitor Access Management Platform

Estate platform connecting residents, security officers and administrators:

- **Resident app** (Android, Flutter): create visitor invitations, QR passes, history.
- **Security app** (Android, Flutter): scan or enter codes, verify, record entry and exit.
- **Admin dashboard** (Next.js): residents, units, gate monitoring, reports, audit logs.
- **Backend** (Django REST, PostgreSQL): single source of truth for auth, permissions and access decisions.

## Status

Architecture approved. M1 (foundation) and M2 (authentication and roles) are complete on `main`. M3 (residents and properties) is implemented on `feat/m3-residents-properties-ci`: property/unit APIs, resident approval, resident-unit assignments, encrypted identity documents and dry-run/atomic CSV imports. CI is green (130 tests). Production private-storage configuration remains a deployment decision.

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
