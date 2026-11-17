# Open Questions

## Decided (2026-11-17)

- **Q1** Suspension: revoke all of the resident's active credentials immediately.
- **Q2** Numeric manual-entry code: 8 digits, estate-scoped, rate limited.
- **Q3** Offline gate: fail closed; manual process, logged as an override afterwards.
- **Q11** Re-opening a pass: cached in SecureStore on the device; reissue revokes the old credential and creates a new one.

## Still open (blocking approval)

Per the master skill, missing rules that affect access security, privacy or data integrity are decided by the project owner, not assumed.

| # | Question | Affects | Working default until answered |
|---|---|---|---|
| Q4 | First release: one estate or several estates live at once? | Onboarding, super admin UI | Schema multi-estate ready, one estate in use |
| Q5 | Visitor and access-event retention period | Privacy policy, Play data safety form | Configurable in `EstateSettings`, no automatic purge |
| Q6 | Resident self-registration: how is the estate reference verified (code issued by management, unit number plus phone, other)? | Registration flow | Management-issued estate reference, admin approval required |
| Q7 | Which provider sends activation and password-reset messages (email, SMS, both)? | Auth, cost | Email first |
| Q8 | Hosting and accounts (backend, Postgres, Vercel, Firebase, Play Console) | Phase 10, CI | Proposed in `system-architecture.md` |
| Q9 | Estate branding and logo, or use the default tokens for now? | Design system | Default navy/blue tokens |
| Q10 | Figma file for the designs, or design from scratch with the design skill? | Phase 3 | Design from scratch |
