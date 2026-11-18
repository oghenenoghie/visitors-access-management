# M9B — Authenticator QR enrolment and recovery-code handoff

## Changes

- Render the backend-provided TOTP provisioning URI as an SVG QR code using `qrcode.react` in the browser.
- Keep QR generation local; do not send the provisioning URI or secret to an external QR-code service.
- Provide the raw setup key as a manual-entry fallback for authenticator apps that cannot scan.
- After first-time TOTP confirmation, keep the administrator on a one-time recovery-code screen rather than immediately redirecting.
- Allow copying recovery codes to the clipboard. Codes remain in component memory only and are not persisted in browser storage.
- Continue to the dashboard only after the administrator acknowledges saving the codes.

## Security considerations

- The setup secret and provisioning URI are sensitive enrolment material. They are delivered only over the authenticated same-origin BFF challenge flow and should never be logged or placed in analytics.
- The recovery codes are displayed once and are not stored by the client after the page is left or refreshed. If the administrator loses them, an authorised administrator must reset 2FA and repeat enrolment.
- The BFF stores JWTs in HttpOnly cookies; recovery codes remain in the JSON response because the administrator must save them.
- The browser clipboard is an explicit user action; users should paste only into a trusted password manager or secure offline store.

## Verification

- Admin dashboard lint and production build.
- Manual first-enrolment test with Google Authenticator, Microsoft Authenticator or another standards-compliant TOTP app.
- Confirm the code succeeds, recovery codes appear once, each code is single-use, and subsequent logins request TOTP.
- Inspect browser storage and network traffic: no QR vendor request, no JWT in response body after BFF processing, and no client persistence of recovery codes.
