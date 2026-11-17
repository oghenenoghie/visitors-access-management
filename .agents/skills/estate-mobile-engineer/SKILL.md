---
name: estate-mobile-engineer
description: Develop the resident and security Android applications for the Estate Visitor Access Management Platform using React Native, Expo and TypeScript. Use for mobile architecture, screens, navigation, API integration, QR scanning, secure storage, notifications, accessibility and Android releases.
---

# Estate Mobile Engineer Skill

## Mission
Build two dependable Android experiences:
1. Resident app for managing visitor invitations and passes.
2. Security app for verifying credentials and recording visitor movements.

Both apps use the same documented backend APIs. They may share code, theme tokens and components, but must retain separate navigation, permissions and user experiences.

## Required stack
- React Native
- Expo and Expo Router
- TypeScript with strict checking where practical
- TanStack Query for server state
- Zustand only for appropriate client state
- React Hook Form and Zod
- Expo Camera or an approved QR scanning library
- Expo SecureStore for sensitive tokens
- Expo Notifications / Firebase Cloud Messaging
- Native share sheet for WhatsApp, SMS and other installed apps

Inspect the existing app and Expo SDK before adding or upgrading packages.

## Repository and app structure
Prefer a workspace/monorepo only if it is already established or clearly beneficial. A possible structure:

```text
mobile/
  packages/
    api/
    shared/
    components/
    theme/
  resident-app/
  security-app/
```

Keep API clients, types and genuinely shared components centralised. Do not force the two apps to share screens or navigation that should differ.

## Shared engineering rules
- Use TypeScript types for API contracts.
- Keep API calls out of presentation components.
- Use a shared, configured API client with token refresh handling.
- Handle expired sessions and revoked accounts centrally.
- Use server state for backend-owned records.
- Do not duplicate server data in Zustand without a clear reason.
- Validate forms on the client for usability and again on the backend for security.
- Include loading, empty, error, offline and success states.
- Do not hardcode production endpoints or secrets.
- Never store passwords or raw long-lived secrets in ordinary AsyncStorage.
- Do not log access credentials, tokens or visitor PII.

## Resident app requirements
Required flows:
- splash and onboarding
- login and password recovery
- approved resident registration/activation
- resident home
- create invitation
- invitation confirmation
- visitor pass and QR display
- active, expired and cancelled invitations
- visitor history
- notification centre
- profile and settings
- support/help

Resident home should prioritise:
- create visitor pass
- active invitations
- expected visitors
- recent visitor activity
- notifications

Invitation form should support visitor name, phone, visit date, validity window, access type and optional vehicle registration/purpose according to estate policy.

The pass should display only approved information: visitor, host, unit, validity, access type, status, QR and numerical code. Provide native sharing and copy actions. Sharing must not expose private resident account data.

## Security app requirements
Required flows:
- officer login
- assigned gate/shift context
- gate dashboard
- QR scanner
- manual code entry
- verification result
- visitor detail
- check-in confirmation
- check-out
- visitor log
- rejected attempts
- incident reporting
- profile and shift information

Optimise the scanner for speed and reliability:
- request camera permission with clear explanation
- provide manual-entry fallback
- prevent repeated scans while a request is pending
- debounce scanner events
- show a clear progress state
- display an unambiguous result
- require an explicit check-in action if the business flow requires confirmation
- refresh/revalidate at final admission

A scan result is not proof of admission. The backend must authorise and commit the check-in.

## Access result presentation
Use clear, accessible status treatments:
- valid/approved
- expired
- cancelled
- revoked
- already used
- not yet valid
- invalid
- already checked in
- manual review required

Do not show internal stack traces or sensitive validation details to gate users. Show enough information to make a safe operational decision.

## Network and offline behaviour
Gate verification is online by default. If connectivity is lost:
- clearly show that live verification is unavailable;
- do not present cached credentials as currently valid unless a formally approved offline design exists;
- do not silently queue an admission and imply it was approved;
- provide a safe escalation path.

Resident app may cache non-sensitive read-only information where appropriate, but must clearly distinguish stale data from current backend state.

## Notifications
Register device tokens securely and associate them with the authenticated user. Handle token refresh, logout and invalidation. Deep links must validate the current session and permissions before displaying protected content.

## UI/UX
Use the approved project design system. Build reusable inputs, buttons, cards, status indicators, dialogs, skeletons, empty states and error views.

Ensure:
- accessible contrast and touch targets
- readable typography
- keyboard-safe forms
- responsive layouts on phones and tablets
- support for Android back navigation
- clear destructive-action confirmation
- consistent spacing and iconography

Avoid decorative complexity on the security app. Its critical actions must be obvious and usable under time pressure.

## Testing
Test:
- authentication and token refresh
- route protection
- form validation
- invitation creation and cancellation
- QR display
- camera permissions and scan behaviour
- duplicate scan prevention
- manual code entry
- API failure and timeout
- notification registration and deep links
- logout and account suspension
- accessibility and device-size layouts

Use mocked APIs for component tests but verify critical workflows against a real test backend before release.

## Android release
Before production build:
- verify application IDs and package names
- configure signing securely
- configure environment-specific API URLs
- verify notification credentials
- review Android permissions
- test on supported physical devices
- verify camera behaviour and low-light scanning
- test upgrade and session migration
- prepare store assets and privacy declarations where applicable

The security app may be distributed privately or through managed devices rather than publicly listed, subject to the estate's distribution needs.

## Working procedure
Inspect the app and API contracts before changing code. Implement one coherent flow at a time. Run type checks, linting and tests. Report tested devices/emulators, known limitations and release status accurately.
