# Resident Android App

Flutter application for residents to authenticate, create visitor invitations and share digital access passes.

## Requirements

- Flutter stable and Dart SDK >= 3.4
- Android Studio / Android SDK
- Running Estate Access Django API

## Run

From this directory:

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1/
```

For a physical Android device, replace `10.0.2.2` with the development machine's LAN address. The API must be reachable from the device; do not use localhost on a physical phone.

## Included in the M5 vertical slice

- Material 3 design system and Flutter navigation.
- Email/password sign-in against `POST /auth/login/`.
- Required TOTP challenge and first-time authenticator enrolment.
- JWT access/refresh token storage using Android secure storage.
- Refresh-token rotation and authenticated API requests.
- Resident dashboard backed by `/auth/me/`, `/residents/` and `/invitations/`.
- Active home assignment lookup through `/resident-unit-assignments/?status=active`.
- Visitor invitation creation against `POST /invitations/`.
- Digital pass with QR and manual code, secure local credential storage, native share sheet and cancellation.

## Security

- Never commit API credentials, signing keys or production secrets.
- Tokens and one-time invitation credentials use `flutter_secure_storage`.
- Backend remains authoritative for permissions, invitation validity and access decisions.
- Credentials are returned once. A pass created on another device cannot be reconstructed by this client.
- Do not use the emulator API URL for production.
- FCM is intentionally deferred until M8.

## Device testing

The GitHub Actions mobile workflow runs dependency resolution, Dart formatting, static analysis and widget tests. Android emulator/device testing requires an Android SDK and a reachable backend configured with the API URL.
