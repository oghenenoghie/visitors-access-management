# M9E — BFF concurrent refresh response handling

## Problem

The backend now serializes refresh-token rotation. When two BFF requests arrive with the same expired access token and refresh cookie, one request can rotate successfully while the other receives a rejected-refresh response. Previously, the losing BFF request cleared both session cookies. Because HTTP responses can arrive in either order, that stale response could delete the replacement cookies set by the winning request.

## Behavior

- A failed refresh attempt after an upstream 401 returns HTTP 409 with `Cache-Control: no-store`.
- The conflict response deliberately does not set or clear either session cookie. The request may have lost a race to another request that has already rotated the refresh token.
- The successful refresh response remains responsible for setting the replacement HttpOnly cookies.
- The dashboard's initial current-user request retries a 409 response up to three times with a short increasing delay, allowing the winning response's Set-Cookie headers to be applied.
- Ordinary upstream 401 responses still clear the session when no concurrent refresh conflict was detected.
- Logout continues to clear the browser's local session cookies regardless of upstream availability.

## Security properties retained

- Access and refresh tokens remain HttpOnly cookies scoped to `/api/bff`.
- Cookies retain SameSite=Strict and Secure in production.
- BFF requests remain no-store and state-changing requests require an exact same-origin Origin header.
- JWTs are not moved into browser storage.

## Verification

The backend CI validates the distributed refresh-token rotation test on PostgreSQL. The dashboard CI runs ESLint and a production Next.js build. Browser-level concurrency verification should still be performed against a running deployment: expire the access token, trigger two protected BFF requests concurrently, and confirm the winning replacement cookies remain present after both responses complete.
