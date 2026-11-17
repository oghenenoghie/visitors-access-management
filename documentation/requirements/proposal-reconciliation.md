# Proposal Reconciliation

Source: *Estate Gate Access & Visitor Management System* proposal, Aqvessa Technologies, ref AQV-PRO-2026-[000] v1.0, November 2026 (17 pages, all read). This is the client-facing commitment. The master skill is the engineering specification. Where they differ, this document records the difference and the handling.

## Conflicts that need a decision

| # | Proposal says | Master skill / our docs say | Handling |
|---|---|---|---|
| C1 | Mobile: **Flutter**. Backend: **Node.js, NestJS, TypeScript** (section 4.1) | Mobile: **Expo React Native**. Backend: **Django, DRF** | Blocks M1. Asked of the project owner. Docs stay stack-neutral where possible. |
| C2 | Hosting in the **Estate's own cloud account** (AWS, Azure or GCP), provisioned with **Terraform**; provider agreed in discovery | Docs proposed Railway and Vercel | Our hosting proposal is withdrawn as a default. Docker stays; add Terraform to infrastructure. Provider agreed with the Estate. |
| C3 | Resident registration includes **upload of a valid ID**, encrypted per file, viewable only by authorised admins with every view logged, deleted on account closure | `identification_reference` kept minimal, no document storage | Adopt the proposal: add `ResidentIdDocument` and ID-view auditing (see below). |
| C4 | Visitors provide **only name and telephone number** (data minimisation) | `Visitor` also has `vehicle_registration` and `notes` | Keep vehicle registration optional; decision Q12 on whether the minimisation statement needs an exception. |
| C5 | Visitor records **deleted or anonymised automatically** after an Estate-set period (**12 months proposed**) | Master: preserve historical visitor and access records; no deletes without an approved retention process | Compatible: the proposal is the approved retention process. Anonymise visitor PII after the period; keep event rows and the audit log. Default 12 months. |
| C6 | Reports exportable to **PDF and Excel** | CSV or PDF | Use PDF and Excel (xlsx); CSV optional. |
| C7 | **Password recovery by one-time code**, SMS gateway for OTP and alerts | Docs defaulted to email | SMS OTP is primary; email optional. Updates Q7. |
| C8 | **Two-factor authentication for all dashboard accounts**; session expiry and remote sign-out | Not specified | Add. |
| C9 | QR carries a **digitally signed token**, forged QR rejected before the database is checked | Opaque random token | Combine: random token plus a signature tag checked before lookup. |
| C10 | Timeline: discovery 1 wk, architecture/design 2 wks, **development 4 wks (W4-W7)**, integration and testing 2 wks, deployment 1 wk | Master: backend in W3-W4, apps W5-W7 | Client commitments follow the proposal; plan realigned below. |

## Requirements the proposal adds (not in the master skill or our docs)

- **Resident ID documents**: private object storage, no public link, per-file encryption with provider-managed keys, short-lived access for administrators, every view audited, deleted when the account closes. Acceptance criterion 8: unreadable in storage without keys.
- **Data subject rights** (Nigeria Data Protection Act 2023): privacy notice shown at registration; residents can view, correct and request deletion of their data. The Estate is controller; Aqvessa is processor (a data processing agreement is a contract item, not code).
- **Throttling and flagging**: repeated failed lookups from a gate device are throttled and flagged to Estate Management (an alert, not only a log entry).
- **Remote device disable**: an officer's registered phone can be disabled remotely if lost.
- **Streets**: management of streets, blocks, units and apartment numbers. Master model has blocks and units but no street level.
- **Bulk data import**: the Estate supplies resident and unit data in an agreed format by week 3, so a validated import tool is needed.
- **Code states**: Issued, Shared, Presented, Verified, Admitted, Exited, or Expired, Cancelled, Rejected. The server cannot know a code was shared, so "Shared" is treated as a client-side label, not a stored state.
- **Password hashing**: Argon2 or bcrypt.
- **Security testing**: OWASP ASVS and MASVS, then an independent vulnerability scan; acceptance criterion 9: no open critical or high findings.
- **Source ownership**: code sits in a repository owned by the Estate, with credentials and admin access transferred on final payment. This repo is currently under a personal GitHub account and will need transferring.
- **Support SLAs**: P1 gate-cannot-verify response 1 hour, resolution 8 hours; handled 06:00-22:00 daily.

## Acceptance criteria (proposal section 8)

1. All section 3 functions work per the signed requirements.
2. Valid code verified in under 2 s on normal mobile data.
3. One-time code rejected on every attempt after first successful use.
4. Expired, cancelled and invalid codes rejected with the correct reason.
5. Each role accesses only its own functions and data.
6. Reports reconcile with underlying visitor records.
7. Residents' app approved and live on Google Play.
8. ID documents unreadable in storage without keys; every view audited.
9. Security test report shows no open critical or high findings.

Deemed accepted five business days after handover if no critical defect is reported.
