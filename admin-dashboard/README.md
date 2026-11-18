# Estate Access Admin Dashboard

Next.js management console for estate administrators and authorised managers.

## Setup

```bash
cp .env.example .env.local
npm install
npm run dev
```

Set `ESTATE_API_BASE_URL` to the Django API root, for example `http://localhost:8000/api/v1`. This is a server-only environment variable: do not rename it with the `NEXT_PUBLIC_` prefix or expose the API origin to browser code. Development defaults to the local Django API when omitted; production requests fail closed if it is missing.

## Current functionality

- Email/password login and authenticator-app challenge flow.
- TOTP enrolment with a locally rendered QR code and one-time recovery-code handoff.
- HttpOnly-cookie sessions managed by the same-origin backend-for-frontend (BFF).
- Current-user session lookup and refresh-token rotation.
- Responsive overview and navigation.
- Resident directory.
- Properties and residential units directory.
- Visitor invitation monitoring.
- Gate activity and read-only audit trail.

All data comes from the existing API; backend role and estate scoping remain authoritative. UI visibility is not an authorisation boundary.

## Session and deployment security

- Access and refresh tokens are stored in HttpOnly cookies scoped to `/api/bff`.
- Cookies use SameSite=Strict and Secure in production.
- State-changing BFF requests require an exact same-origin `Origin` header.
- BFF responses are not cached; security response headers are applied when relaying upstream responses.
- Concurrent refresh conflicts do not clear cookies, preventing a losing response from deleting a winning response's rotated session.
- Configure `ESTATE_API_BASE_URL` in the production hosting environment and use HTTPS.
- Keep the Django API origin private to server-side code; never use a `NEXT_PUBLIC_` variable for it.

No privileged write actions are exposed in this dashboard slice. Browser-level concurrent-refresh verification against a deployed staging environment remains an explicit release check; CI lint/build success alone is not browser E2E evidence.

## Verification

```bash
npm install
npm run lint
npm run build
```
