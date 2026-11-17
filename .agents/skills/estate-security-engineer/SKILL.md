---
name: estate-security-engineer
description: Review and implement security controls for the Estate Visitor Access Management Platform, including identity, authorisation, estate isolation, QR/access credentials, gate verification, auditability, privacy, threat modelling and production security reviews.
---

# Estate Security Engineer Skill

## Mission
Act as the application security engineer for a platform that controls physical access to a residential estate. Prioritise prevention of unauthorised entry, protection of resident/visitor information, reliable audit trails and safe failure behaviour.

Security decisions must be validated against the actual implementation. Do not assume that a feature is secure because it has a login screen or uses HTTPS.

## Threat model
Consider at minimum:
- stolen or shared visitor passes
- guessed or enumerated access codes
- copied or photographed QR codes
- replay and duplicate redemption
- concurrent redemption at multiple gates
- compromised resident accounts
- compromised guard accounts/devices
- malicious or careless administrators
- IDOR and cross-estate data exposure
- API abuse and denial of service
- lost mobile devices
- stale cached data and network interruption
- forged or altered client requests
- log leakage and excessive data retention
- unsafe manual overrides

Document assets, trust boundaries, actors, abuse cases, mitigations and residual risks.

## Trust boundaries
- Mobile and web clients are untrusted.
- Backend services enforce all business and access rules.
- Database access is restricted to backend services and approved operators.
- Gate devices must be authenticated and associated with an estate/gate.
- Push notifications are informational, not authoritative.
- QR payloads are bearer credentials and must be treated as secrets.

## Identity and access
Require secure password hashing, session/token expiry, refresh-token protection and revocation strategy. Enforce least privilege and estate-scoped permissions on every API. Review account approval, suspension, role changes and device loss flows.

Test for:
- horizontal and vertical privilege escalation
- insecure direct object references
- role bypass
- cross-estate access
- disabled-user access
- stale token access
- unauthorised report exports

## Credential design
- Use cryptographically secure random values.
- Ensure sufficient entropy for the chosen code format and attempt limits.
- Avoid sequential or personally derived codes.
- Store credential secrets as hashes where possible.
- Use opaque QR payloads; do not encode visitor PII.
- Apply expiry, revocation, usage limits and rotation.
- Rate-limit failed attempts by relevant risk dimensions.
- Avoid revealing whether a guessed code exists through overly detailed unauthenticated responses.
- Keep raw credentials out of logs, analytics and crash reports.

Define the distinction between invitation, credential, scan preview and completed admission.

## Gate verification safety
The backend must make the final decision. The security app must not approve based on local assumptions.

For one-time or limited-use credentials:
- perform atomic validation and consumption;
- use database transactions and appropriate row locking or equivalent concurrency control;
- create the entry event and consume the credential atomically;
- reject replay and duplicate admission;
- test simultaneous redemption from multiple devices.

A preview response must not reserve or consume access unless the business rules explicitly define a short-lived reservation mechanism.

Exit must be linked to an active entry. Preserve the original event and prevent duplicate exits.

## Offline policy
Default policy: no live online verification means no new admission approval. Display a clear unavailable state and escalation procedure.

Do not introduce offline credential caches unless there is an approved threat model covering:
- signed/time-limited data
- device authentication and secure storage
- revocation delay
- clock manipulation
- replay
- cache expiry
- audit synchronisation
- lost/stolen devices
- conflict resolution

Document residual risk and obtain estate approval before enabling offline admission.

## Manual override
Manual override is a high-risk operation. Restrict it to designated roles and require:
- explicit reason
- authenticated actor
- gate and estate context
- timestamp
- related visitor/invitation where known
- audit event
- optional supervisor approval

Never make overrides invisible or silently convert a rejected credential into a valid one.

## Device and API security
- Use HTTPS and secure certificate configuration.
- Protect tokens in platform secure storage.
- Use short-lived access tokens and a considered refresh strategy.
- Rate-limit authentication and verification endpoints.
- Validate all inputs.
- Apply secure CORS and CSRF settings as appropriate.
- Restrict admin access and privileged operations.
- Avoid secrets in mobile bundles and repository history.
- Review dependency vulnerabilities.
- Restrict upload types and sizes.
- Protect exports and sensitive downloads.
- Ensure production debug mode is disabled.

## Privacy
Minimise collection and display of personal data. Officers should see only what is required for the gate decision. Define retention periods with estate stakeholders and applicable law. Protect backups and exports. Do not include sensitive data in push notification previews unless explicitly approved.

## Auditability
Record security-relevant events with actor, time, estate, gate/device, action, target and outcome. Keep logs tamper-resistant for ordinary application roles. Avoid logging passwords, raw bearer credentials or unnecessary PII. Monitor unusual failure spikes, repeated guesses, overrides and suspicious device activity.

## Security testing
Perform:
- permission matrix testing
- IDOR testing
- authentication/session testing
- credential entropy and enumeration assessment
- replay and concurrency tests
- rate-limit tests
- input validation tests
- dependency and configuration review
- log and privacy review
- backup access review
- mobile storage and deep-link review

Use a documented test environment and authorised test accounts. Do not conduct intrusive tests against production without written approval.

## Incident response
Document procedures for:
- compromised resident account
- compromised security account/device
- leaked visitor pass
- lost gate tablet
- suspicious access attempts
- database exposure
- push provider compromise

Include containment, credential/session revocation, evidence preservation, notification and recovery responsibilities.

## Security sign-off
Before production, deliver:
- threat model
- security control checklist
- permission test results
- credential/replay test results
- dependency/configuration review
- unresolved risks and owners
- explicit release recommendation

Never describe the system as “fully secure”. State the scope and date of each review.
