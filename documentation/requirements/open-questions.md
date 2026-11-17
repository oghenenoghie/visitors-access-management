# Open Questions (blocking approval)

Per the master skill, missing rules that affect access security, privacy or data integrity are decided by the project owner, not assumed.

| # | Question | Affects | Working default until answered |
|---|---|---|---|
| Q1 | When a resident is suspended, what happens to credentials they already issued? (a) revoke all immediately, (b) let them expire, (c) per-estate setting | Scenario 6, credential model | Block new invitations only; no automatic revocation. Not production-safe. |
| Q2 | Numeric manual-entry code length and expiry. Longer is safer; shorter is easier to read out at a gate. | Credential generation, brute-force risk | 8 digits, estate-scoped, rate limited |
| Q3 | Offline gate behaviour. Fail closed (no app admission) or allow a cached emergency list? | Gate app, security | Fail closed |
| Q4 | First release: one estate or several estates live at once? | Onboarding, super admin UI | Schema multi-estate ready, one estate in use |
| Q5 | Visitor and access-event retention period | Privacy policy, Play data safety form | Configurable in `EstateSettings`, no automatic purge |
| Q6 | Resident self-registration: how is the estate reference verified (code issued by management, unit number plus phone, other)? | Registration flow | Management-issued estate reference, admin approval required |
| Q7 | Which provider sends activation and password-reset messages (email, SMS, both)? | Auth, cost | Email first |
| Q8 | Hosting and accounts (backend, Postgres, Vercel, Firebase, Play Console) | Phase 10, CI | Proposed in `system-architecture.md` |
| Q9 | Estate branding and logo, or use the default tokens for now? | Design system | Default navy/blue tokens |
| Q10 | Figma file for the designs, or design from scratch with the design skill? | Phase 3 | Design from scratch |
| Q11 | Re-opening a pass: tokens are stored only as hashes, so the server cannot show a QR again. Cache the pass on the resident's device, store tokens encrypted (reversible), or reissue on demand? | Resident app, credential security | Cache in SecureStore; reissue revokes the old credential |
