# M8A — Notification foundation and push delivery

## Delivered scope

This increment establishes the server-side notification contract used by the resident and gate applications.

- Persisted, user-scoped notification inbox.
- Mark-as-read endpoint with ownership enforcement.
- FCM device registration and de-registration endpoints.
- FCM tokens are HMAC-indexed and encrypted at rest with the existing FIELD_ENCRYPTION_KEY; raw tokens are never returned by the API.
- Firebase Cloud Messaging delivery is asynchronous through Celery and is disabled by default.
- Invalid/unregistered device tokens are deactivated.
- Residents receive inbox notifications when an invitation is cancelled, a visitor checks in or checks out, or a supervisor override admits a visitor.

## API

All endpoints require a valid authenticated access token.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/v1/notifications/ | Paginated inbox for the signed-in user only |
| POST | /api/v1/notifications/{id}/read/ | Mark one owned notification as read |
| POST | /api/v1/devices/push-token/ | Register or refresh a device token |
| DELETE | /api/v1/devices/push-token/ | Deactivate the signed-in user's device token |

Device registration request:

```json
{
  "token": "<FCM registration token>",
  "platform": "android"
}
```

Supported platforms are android and ios. Device tokens are secrets: send them only over TLS and do not log them.

## Firebase configuration

1. Create a Firebase project and register each Android application with its exact application ID.
2. Add the generated google-services.json to each app's local Android configuration; do not commit service-account credentials.
3. Provision a Firebase service account with only the Firebase Cloud Messaging permissions required to send messages.
4. Store the service-account JSON as a secret in the deployment platform and expose it to Django as FCM_SERVICE_ACCOUNT_JSON.
5. Set FCM_ENABLED=true only after the Celery worker and broker are deployed and verified.
6. Keep FIELD_ENCRYPTION_KEY stable and backed up; it is needed to decrypt registered device tokens.

The API persists inbox notifications even while FCM is disabled. This supports local development and gives users an in-app notification history independent of push delivery.

## Worker

Run the worker alongside the Django API:

```bash
celery -A config worker --loglevel=info
```

The broker is configured by CELERY_BROKER_URL (defaults to REDIS_URL when present). Do not enable FCM until the worker can reach the broker and Firebase.

## Security and operational notes

- Every inbox query is filtered by the authenticated user; IDs belonging to another user return 404.
- Registration is bound to the authenticated account. Registering an existing token transfers it to the currently authenticated account, which supports logout/login on a shared device.
- Token hashes are keyed with a purpose-specific HMAC; encrypted token values are required only by the sender.
- Push payloads contain opaque resource IDs and short event text only. Do not put visitor phone numbers, identity documents, QR credentials, or manual access codes in push data.
- Delivery is best-effort. The persisted inbox remains the source of truth.
- Mobile Firebase initialization, foreground presentation, notification tap/deep-link handling and end-to-end device verification remain part of the next M8 integration slice.
