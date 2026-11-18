# Estate Access Admin Dashboard

Next.js management console for estate administrators and authorised managers.

## Setup

```bash
cp .env.example .env.local
npm install
npm run dev
```

Set NEXT_PUBLIC_API_BASE_URL to the Django API root, for example http://localhost:8000/api/v1.

## M7 functionality

- Email/password login and authenticator-app challenge flow.
- Current-user session lookup.
- Responsive overview and navigation.
- Resident directory.
- Properties and residential units directory.
- Visitor invitation monitoring.
- Gate activity and read-only audit trail.

All data comes from the existing API; backend role and estate scoping remain authoritative.

## Production security limitations

This first implementation stores short-lived access/refresh tokens in sessionStorage. Before public production use, replace this with a same-origin backend-for-frontend using HttpOnly, Secure, SameSite cookies and CSRF protection. TOTP setup currently displays the otpauth URI as text; add QR rendering and secure setup UX before production approval. No privileged write actions are exposed in this first dashboard slice. UI visibility is not an authorisation boundary.

## Verification

```bash
npm install
npm run lint
npm run build
```
