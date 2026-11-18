# M5 — Resident Android App

## Objective

Deliver the first Flutter resident application slice against the merged Django REST API. This client is resident-only; gate operations and management features belong to later milestones.

## Technology

- Flutter stable / Dart
- Material 3 design tokens
- Riverpod providers
- go_router
- Dio HTTP client
- flutter_secure_storage (Android Keystore-backed)
- qr_flutter
- share_plus
- intl

## Implemented

1. Resident sign-in via `POST /api/v1/auth/login/`.
2. TOTP challenge via `/auth/2fa/setup/`, `/auth/2fa/confirm/` and `/auth/2fa/verify/`.
3. JWT access/refresh token storage and refresh-token rotation.
4. Resident dashboard using `/auth/me/`, `/residents/` and `/invitations/`.
5. Active home assignment lookup through `/resident-unit-assignments/?status=active`.
6. Invitation creation using the existing backend serializer fields.
7. One-time QR token and manual access code stored in secure device storage.
8. Pass detail, QR rendering, native share sheet and invitation cancellation.

## Contract and security decisions

- Login states `authenticated`, `two_factor_required` and `two_factor_setup_required` are handled.
- Residents must be active and approved by estate management before sign-in.
- Invitation creation submits the selected assigned unit UUID, visitor details, validity window and access type.
- Plaintext credentials are returned once by the API. The app never expects invitation detail to reveal them.
- A pass created on another device cannot be reconstructed because the backend stores only credential digests.
- The backend remains authoritative for resident ownership, estate scope, validity and access decisions.

## Deferred

- Public resident registration and pending-approval onboarding.
- FCM device registration and push delivery (M8).
- Security gate scanner (M6).
- Estate admin web dashboard (M7).
- Android signing, production API configuration and Play Store release.

## Verification

The mobile CI workflow runs Flutter dependency resolution, Dart formatting, static analysis and widget tests. Physical-device and emulator acceptance testing requires a configured Android SDK and a reachable API environment.
