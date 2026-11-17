# Open Questions

## Decided (2026-11-17)

- **Q1** Suspension: revoke all of the resident's active credentials immediately.
- **Q2** Numeric manual-entry code: 8 digits, estate-scoped, rate limited.
- **Q3** Offline gate: fail closed; manual process, logged as an override afterwards.
- **Q11** Re-opening a pass: cached in SecureStore on the device; reissue revokes the old credential and creates a new one.

- **Q7** No SMS or email verification. Password recovery uses an administrator-issued single-use reset code; dashboard 2FA uses an authenticator app (TOTP).
- **Q13** Stack: Django backend, Flutter mobile apps, Next.js dashboard. The proposal's NestJS backend is replaced by Django, so proposal section 4.1 must be corrected before the client signs.

## Still open

Per the master skill, missing rules that affect access security, privacy or data integrity are decided by the project owner, not assumed.

| # | Question | Affects | Working default until answered |
|---|---|---|---|
| Q4 | First release: one estate or several estates live at once? | Onboarding, super admin UI | Schema multi-estate ready, one estate in use |
| Q5 | Visitor and access-event retention period | Privacy policy, Play data safety form | 12 months (proposal), then anonymise visitor data automatically; confirm with the Estate |
| Q6 | Resident self-registration: how is the estate reference verified (code issued by management, unit number plus phone, other)? | Registration flow | Management-issued estate reference, admin approval required |
| Q8 | Which cloud (AWS, Azure or GCP) in the Estate's account, plus Firebase and Play Console accounts | Phase 10, CI, Terraform | Docker plus Terraform, provider TBD |
| Q12 | Proposal says visitors give only name and phone, but the master skill adds optional vehicle registration and notes. Keep them? | Privacy notice, data minimisation | Keep vehicle registration optional; drop free-text notes unless needed |
| Q9 | Estate branding and logo, or use the default tokens for now? | Design system | Default navy/blue tokens |
| Q10 | Figma file for the designs, or design from scratch with the design skill? | Phase 3 | Design from scratch |
