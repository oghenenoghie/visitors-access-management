# M8B — Mobile push notification integration

## Implemented

Both Flutter applications now include an optional Firebase Cloud Messaging integration:

- Firebase is initialized at application startup. Missing native Firebase configuration is caught and push is disabled without blocking app startup.
- Notification permission is requested after a user authenticates.
- FCM registration tokens are sent to the authenticated `POST /api/v1/devices/push-token/` endpoint with the `android` or `ios` platform.
- Token refresh events re-register the current token.
- Logout attempts to deactivate the current token through `DELETE /api/v1/devices/push-token/` before clearing the local session. Network failures do not block logout.
- Foreground notification messages are displayed using local notifications.
- Background/terminated notification taps are handled by Firebase Messaging and local-notification response callbacks.
- Tap navigation accepts only a UUID-shaped opaque resource identifier. Resident taps open the invitation detail route; security-app taps open gate activity. QR credentials, manual access codes and raw push tokens are never used for navigation.
- Registration and delivery are best-effort. The persisted notification inbox remains the source of truth.

## Mobile dependencies

Both apps use:

- `firebase_core`
- `firebase_messaging`
- `flutter_local_notifications`

Run `flutter pub get` in each app after pulling this change.

## Firebase project setup (required for real push delivery)

Firebase credentials and app identifiers are intentionally not committed. Configure each app against the actual Firebase project:

1. Confirm the Android application ID and iOS bundle identifier for each app. Do not use guessed identifiers; use the identifiers selected for the release builds.
2. In Firebase Console, create or select the estate-access Firebase project and register both mobile applications with their exact identifiers.
3. Install the FlutterFire CLI and run `flutterfire configure` separately from `mobile/resident-app` and `mobile/security-app`, selecting the correct Firebase project and platforms.
4. Ensure the generated Android `google-services.json` and iOS `GoogleService-Info.plist` correspond to the correct app. The Android Google Services Gradle plugin and iOS Firebase configuration must be applied by the generated native project.
5. Keep local Firebase configuration files out of Git unless the release owner explicitly approves publishing non-secret client configuration. Never commit Firebase Admin/service-account JSON, APNs private keys, or device tokens.
6. For iOS delivery, configure APNs authentication in Firebase Console and enable Push Notifications and Background Modes in the iOS target.
7. Install and run each app on a physical device. Emulators/simulators may not provide the same APNs/FCM behavior.

The current repository CI creates Android platform folders during its workflow and deliberately has no Firebase project credentials. CI verifies compilation and tests without attempting live push delivery. A successful CI build therefore does not mean Firebase delivery has been configured.

## Backend delivery remains separately gated

The backend persists notifications regardless of FCM configuration. Live server-to-device delivery still requires all of the following in the deployment environment:

- `FIELD_ENCRYPTION_KEY` remains stable and available.
- `FCM_SERVICE_ACCOUNT_JSON` contains the Firebase service account JSON as a protected secret.
- `CELERY_BROKER_URL` (or the configured Redis broker) is reachable.
- A Celery worker is running and can reach Firebase.
- Only after those checks pass, set `FCM_ENABLED=true`.

Do not enable server-side FCM merely because the mobile apps compile. Keep TLS enabled for API traffic and never log device tokens.
