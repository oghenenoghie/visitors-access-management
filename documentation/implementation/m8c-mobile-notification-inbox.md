# M8C — Mobile notification inbox

## Scope

M8C adds a persistent notification inbox to the resident and security Flutter apps.

- Fetches the signed-in user's notification history from `GET /api/v1/notifications/`.
- Fetches an authoritative unread total from `GET /api/v1/notifications/unread-count/`.
- Marks a notification read through `POST /api/v1/notifications/{uuid}/read/`.
- Supports pull-to-refresh, an unread-only filter, empty/loading/error states, and visible read/unread styling.
- The resident app opens the inbox from the home-screen notification action.
- The security app exposes the inbox as a third bottom-navigation destination.
- Notification records and unread counts remain user-scoped by the backend.

## API addition

`GET /api/v1/notifications/unread-count/` returns:

```json
{
  "unread_count": 3
}
```

The endpoint requires authentication and counts only records where `user=request.user` and `read_at IS NULL`. It does not expose another user's notification data.

## Read state

Opening the inbox does not silently mark every item as read. A user marks an individual notification as read using its trailing action or by tapping the unread row. The client updates the item and unread total only after the API confirms the read operation.

## Verification

Backend tests cover authentication and per-user unread-count isolation. Mobile CI covers Dart formatting, static analysis, Flutter tests, and Android debug builds for both apps.

## Deployment notes

The inbox uses the persisted notification API and does not depend on Firebase being configured. FCM delivery still requires the estate's Firebase project configuration and server-side delivery secrets described in the M8B documentation.
