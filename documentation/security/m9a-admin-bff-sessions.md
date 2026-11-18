# M9A — Admin dashboard BFF sessions

## Scope

Replace browser-readable JWT storage with a same-origin Next.js backend-for-frontend (BFF) boundary for the administrator dashboard.

- Access and refresh JWTs are stored only in HttpOnly cookies scoped to `/api/bff`.
- Cookies use `Secure` in production and `SameSite=Strict`.
- The browser never receives access or refresh token values.
- Dashboard API requests use same-origin `/api/bff/*`; the BFF attaches the access token server-side.
- On an upstream 401, the BFF attempts one refresh-token rotation and retries the original request once.
- Logout blacklists the refresh token through the existing backend endpoint and clears both cookies.
- Mutating requests require an exact same-origin `Origin` header.
- Responses are marked `Cache-Control: no-store`; upstream redirects are not followed.

## Configuration

Set `ESTATE_API_BASE_URL` in the Next.js server runtime to the Django API root, e.g. `https://api.example.com/api/v1`. Do not expose this variable with the `NEXT_PUBLIC_` prefix. The legacy public variable remains a development fallback for migration compatibility and should be removed from production deployment configuration.

## Security boundaries and limitations

- The Django API remains the authority for authentication, role checks and estate-level permissions.
- BFF cookies are scoped to the BFF path and are not readable by JavaScript.
- SameSite and Origin checks mitigate cross-site request forgery; production must serve the dashboard and BFF on one origin.
- The BFF is a token-handling boundary, not a substitute for CSP, TLS, backend rate limiting, account controls or server-side authorisation.
- The authenticator setup URI is still rendered as text in the login UI. QR rendering and a dedicated secure enrolment/recovery experience remain follow-up work.
- Access JWTs already issued before logout/password reset remain valid until their 15-minute expiry; refresh tokens are blacklisted. Consider a per-user token-version check if immediate access-token revocation is required.
- Configure a trusted reverse proxy and `BEHIND_PROXY` consistently; do not trust arbitrary forwarded client-IP headers.

## Verification

CI must run admin-dashboard lint/build plus backend authentication tests. Manual security checks should confirm:
1. No JWT is present in localStorage, sessionStorage, browser-visible response bodies or JavaScript-readable cookies.
2. Cookies are HttpOnly, Secure in production, SameSite=Strict and path-scoped to `/api/bff`.
3. Login, TOTP setup/confirm/verify, authenticated API calls, refresh rotation and logout work end-to-end.
4. Cross-origin POST/PUT/PATCH/DELETE requests receive 403.
5. Refresh failure clears the BFF cookies and requires a new login.
6. Backend role/estate isolation tests continue to pass.

This is a scoped implementation note, not a production security certification.
