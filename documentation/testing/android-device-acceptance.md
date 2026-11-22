# Android device and API acceptance checklist (M5, M6)

Run on a real Android phone (and one emulator) against a backend seeded with one estate, one admin, one resident with an assigned unit and one security officer. Record result, date, device and build for each row. A failure in any **Security** row blocks release.

## Setup

1. Start the API (`docker compose up`), create the seed users, and register one gate device. Note its UUID.
2. Resident app: `flutter run --dart-define=API_BASE_URL=http://<LAN-IP>:8000/api/v1/`. Use the machine's LAN address on a phone, `10.0.2.2` on the emulator.
3. Security app: add `--dart-define=GATE_DEVICE_ID=<gate-uuid>`.
4. Confirm the phone reaches `GET /api/v1/health/` in its browser before testing.

## Resident app

| # | Check | Expected | Result |
|---|---|---|---|
| R1 | Sign in with a valid resident | Dashboard shows name, unit and invitations | |
| R2 | Sign in with a wrong password | Generic error, no hint whether the email exists | |
| R3 | Five wrong passwords, then the correct one | Locked out with a clear message | |
| R4 | Sign in as a pending (unapproved) resident | Cannot sign in | |
| R5 | Create a one-time invitation | Pass shows QR and 8-digit manual code | |
| R6 | Close and reopen the app, open the pass | Pass still shown from secure storage | |
| R7 | Share the pass through the native share sheet | Share sheet opens; no secret appears in the URL or log | |
| R8 | Cancel the invitation | Pass shows cancelled; gate rejects it (G6) | |
| R9 | Create an invitation with a past date or invalid period | Validation error from the API is shown | |
| R10 | Airplane mode, then create an invitation | Clear offline message, no crash, nothing half-created | |
| R11 | Let the access token expire (15 min) and use the app | Silent refresh, no sign-out | |
| R12 | Sign out, then reuse the old refresh token (API) | Rejected | |
| R13 | Admin suspends the resident while signed in | Next request fails; app returns to sign-in | |
| R14 | Rotate the phone, switch dark and light theme | Layout intact, text readable | |

## Security gate app

| # | Check | Expected | Result |
|---|---|---|---|
| G1 | Sign in as a security officer | Gate screen opens; no 2FA prompt | |
| G2 | Launch without `GATE_DEVICE_ID` | Clear "not configured" error, no gate action possible | |
| G3 | Scan a valid one-time pass | Verified: visitor, unit, validity shown | |
| G4 | Verify, then abandon without admitting, then verify again | Still valid. Scanning must not consume it | |
| G5 | Admit the visitor (check-in), then scan the same pass | Rejected as already used | |
| G6 | Scan a cancelled or expired pass | Rejected with the reason; attempt recorded | |
| G7 | Scan a QR from another estate | Rejected; no data about the other estate appears | |
| G8 | Scan a photo or printout of a valid pass after it was used | Rejected | |
| G9 | Scan random or tampered QR content | Rejected, no crash | |
| G10 | Enter the 8-digit code manually | Same result as scanning | |
| G11 | Enter wrong codes repeatedly | Rate limited or locked out | |
| G12 | Check out an admitted visitor | Visitor leaves the "inside" list | |
| G13 | Airplane mode, then scan | Fails closed with a clear offline state; nothing is admitted | |
| G14 | Double-tap Admit, or tap on a flaky network | One check-in only | |
| G15 | Camera permission denied | Explains the problem and offers manual entry | |
| G16 | Two phones scan the same multi-use pass at once | Limit respected, no over-admission | |
| G17 | Admin dashboard: open the audit log and gate activity | Every attempt above, including rejections, is listed with actor and gate | |

## API integration acceptance (curl or the dashboard)

| # | Check | Expected |
|---|---|---|
| A1 | Resident requests another resident's invitation by ID | 404 |
| A2 | Resident calls any `/gate/` endpoint | 403 |
| A3 | Security officer calls `/residents/`, `/invitations/`, `/admin/` | 403 |
| A4 | Estate B admin lists estate A data | Empty or 404, never a leak |
| A5 | Replay a used verify or check-in request with the same idempotency key | Same result, one admission |
| A6 | Run 20 concurrent check-ins on one one-time credential | Exactly one succeeds |
| A7 | Open `/api/v1/schema/` and confirm the apps' calls match it | No call to an endpoint absent from the schema |

## Sign-off

Release candidates need every row passing on one physical device, A6 passing in CI or by script, and the failures from this run filed with their build number.
