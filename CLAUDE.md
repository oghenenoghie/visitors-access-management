# Estate Access — Project Instructions

Estate Visitor Access Management Platform: a resident Android app, a security gate app, an estate admin dashboard and a Django REST backend.

## Source of truth

Skills live in `.agents/skills/`. Read the relevant ones before working:

- `estate-access-platform` — master skill and source of truth. Requirements, architecture, roles, data model, API contracts, workflow phases. Specialist skills supplement it and must not override it.
- Specialists, used only when relevant to the task: `estate-backend-engineer`, `estate-mobile-engineer`, `estate-ui-ux-designer`, `estate-security-engineer`, `estate-qa-engineer`, `estate-devops-engineer`.

If this file and the master skill disagree, the master skill wins. Missing requirements that affect access security, privacy or data integrity: ask, do not invent.

## Stack

- Backend: Python, Django, Django REST Framework, PostgreSQL, Simple JWT.
- Mobile (resident and security apps): Flutter and Dart (Android first), go_router, Riverpod, dio with an OpenAPI-generated client, mobile_scanner, qr_flutter, firebase_messaging, flutter_secure_storage. Decision 2026-11-17, following the client proposal.
- Admin dashboard: Next.js, TypeScript, Tailwind CSS, shadcn/ui.
- Package manager for the Node dashboard: pnpm.

## Repository layout

Follow the master skill's monorepo layout: `backend/`, `mobile/` (`resident_app/`, `security_app/`, shared Dart `packages/`), `admin-dashboard/`, `documentation/`, `infrastructure/`. Shared code (API client, theme tokens, common widgets) goes in `mobile/packages/`, not copied between apps. Keep screens, state and API access in separate layers.

## Design direction

Premium, modern, enterprise-grade. Use the master skill's design tokens (deep navy `#142B45`, primary blue `#2563EB`, soft grey background `#F7F9FC`), Inter typography, 16–20px rounded cards, subtle shadows, light and dark themes, restrained motion.

Avoid generic template looks, excessive gradients, oversized decoration, inconsistent spacing and unnecessary animation.

## QR and access rules

- Never trust a QR code by its appearance. Verify every token through the backend.
- Check expiry, cancellation/revocation, usage limits and estate/gate; prevent reuse.
- Consume a credential only when admission is committed, not on scan.
- Record every verification attempt, including rejections.
- Show clear offline and network-error states.

## Architecture rules

- Strict typing (Dart analysis, TypeScript strict on the dashboard); reusable components; screens separate from business logic.
- API services in a dedicated directory, typed responses, centralised auth.
- Role-based navigation; resident and security permissions stay separate. No admin functions in the resident app.
- Never put secrets in frontend code.
- Do not invent API endpoints; confirm contracts (master skill section 14, then the OpenAPI docs) before integrating.

## Workflow

Before a feature: inspect the structure, review the design system, reuse existing components, check the relevant Flutter and package docs, then implement. After: test on Android (primary) and iOS compatibility, check loading/empty/error/success states, report files created or changed.

Do not rewrite working functionality without a clear reason. Do not claim a Figma design was imported unless it was.

## MCP servers

`.mcp.json` configures Figma. Run `/mcp` in Claude Code to authenticate it. A custom Estate MCP server is deferred until backend auth and permissions exist.
