# M6 — Security/Gate Staff Android App

## Scope

Deliver a dedicated Flutter Android app for security officers and supervisors. It uses the existing Django APIs; it does not make admission decisions locally.

## Implemented client workflows

- Authenticate with the existing login and TOTP challenge endpoints.
- Store JWTs using platform secure storage and rotate refresh tokens.
- Scan an opaque QR bearer token or enter the manual access code.
- Request live verification from the assigned gate device.
- Display backend result states without interpreting unknown states as valid.
- Require a separate explicit check-in action after a valid preview.
- Read gate activity and record exit against an existing invitation.
- Fail closed when the API is unavailable.

## Existing API contracts used

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `auth/login/` | Authenticate officer |
| POST | `auth/2fa/setup/` | Begin required authenticator setup |
| POST | `auth/2fa/confirm/` | Confirm authenticator |
| POST | `auth/2fa/verify/` | Verify authenticator |
| POST | `auth/token/refresh/` | Rotate/refresh session |
| POST | `auth/logout/` | Revoke refresh session |
| POST | `gate/verify/` | Validate QR/manual credential |
| POST | `gate/check-in/` | Record admission |
| GET | `gate/activity/` | Read estate gate activity |
| POST | `gate/check-out/` | Record exit |

All requests use the existing `/api/v1/` prefix.

## Explicitly deferred backend dependencies

1. **Gate assignment/discovery:** No authenticated endpoint currently lists gate devices or assigns the signed-in officer to an active gate. M6 takes the administrator-provisioned gate UUID through build-time configuration. A later gate-management API should replace this deployment-time setting.
2. **Incident reporting:** No incident model, serializer, permission policy or endpoint exists. Do not ship a fake incident form or store incidents only on the device.
3. **Manual override:** The existing backend supports override for security supervisors and estate administrators and requires a reason, but the current APIs require an invitation UUID. The current gate verification response does not expose that UUID and there is no safe invitation lookup endpoint for the security role. The client therefore does not expose override yet.
4. **Shift management:** No shift API is currently available.

## Security requirements

- Backend role/estate checks remain authoritative.
- No local/offline admission.
- Never log QR tokens, manual codes, JWTs or visitor details.
- Do not cache credentials for later approval.
- Distinguish preview from committed entry.
- Show a safe unavailable state during network failure.

## Acceptance criteria

- Flutter formatter, static analysis, tests and debug Android build pass.
- A security officer can authenticate and verify a valid/invalid credential.
- A valid preview requires a second explicit action to check in.
- A failed or unavailable API never appears as an approval.
- Entry/exit records are read from the server.
- Supervisor override and incident reporting remain blocked until the required API contracts are implemented and tested.
