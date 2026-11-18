# Estate Security Gate App

Flutter Android client for authorised security officers and supervisors.

## Configure

Run from this directory:

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=https://YOUR_API_HOST/api/v1/ --dart-define=GATE_DEVICE_ID=REGISTERED_GATE_DEVICE_UUID
```

For Android emulator development, the default API URL is `http://10.0.2.2:8000/api/v1/`.

The gate UUID must identify an active `GateDevice` registered by an estate administrator. The app deliberately blocks gate operations when this value is absent. Do not commit production gate identifiers or credentials.

## Implemented in M6

- Email/password sign-in and authenticator-app challenge flow.
- Access and refresh tokens stored with Android secure storage.
- Refresh-token rotation and logout.
- QR scanning and manual credential entry.
- Live verification against `POST gate/verify/`.
- Explicit check-in against `POST gate/check-in/`.
- Gate activity from `GET gate/activity/`.
- Check-out against `POST gate/check-out/`.
- Clear no-network failure state; no offline admission.

The backend remains authoritative. A successful preview is not an admission; entry is only confirmed after the check-in endpoint records an accepted event.

## API contract limitations

The current backend does not expose a gate-device discovery/assignment endpoint, so deployment must inject the administrator-provisioned gate UUID. The current verification response does not include an invitation identifier, so the app does not offer an unsafe direct check-out from a scan preview; check-out is available from the server activity record.

The current backend has no incident-reporting endpoint or incident model. Incident reporting is therefore intentionally not represented as a working control in this app and must be delivered with the incident-management backend milestone. Manual override remains restricted to supervisor/admin roles by the backend and should be added only after the invitation lookup workflow is available in the admin/security API.

## Verification

```bash
dart format --output=none --set-exit-if-changed lib
flutter analyze
flutter test
flutter build apk --debug
```
