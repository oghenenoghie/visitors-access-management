# M9D — Distributed refresh-token rotation protection

## Problem

The admin BFF stores the refresh token in an HttpOnly cookie and may send it from several concurrent requests. A process-local mutex in the Next.js runtime cannot coordinate requests handled by different serverless or application instances. Without API-side coordination, two workers can both validate the same refresh token before either worker blacklists it.

## Implementation

The API refresh endpoint now uses a custom Simple JWT refresh serializer:

1. Verify the refresh token signature and expiry to obtain its JTI.
2. Start a database transaction and acquire a row-level lock on that token's `OutstandingToken` record.
3. While holding the lock, run the standard Simple JWT serializer, including blacklist validation, refresh rotation, and blacklisting of the old token.
4. Commit the old-token blacklist and replacement-token record together.

Concurrent refresh requests for the same token are serialized by PostgreSQL. The first valid request rotates the token. A waiting request then observes the old token's blacklist and is rejected. This is shared coordination across API workers; it does not depend on process memory or Redis.

The endpoint fails closed with HTTP 503 if the configured database backend does not support `SELECT ... FOR UPDATE`. Do not deploy this refresh flow on SQLite or another database without equivalent row-level locking.

## Verification

The authentication test suite retains the sequential rotation/replay test and adds a two-thread API test that submits the same refresh token concurrently. The expected result is exactly one HTTP 200 and one HTTP 401, followed by rejection of any further replay.

CI uses PostgreSQL, which is required to exercise the locking behavior. Review the Backend CI run on this pull request before merging.

## Operational notes and residual risks

- PostgreSQL is the coordination authority; every API instance must use the same primary database for refresh operations.
- Do not route refresh requests to independent writable database primaries.
- A failed or disconnected refresh request may leave the client unsure whether rotation committed. The client should re-read the session state and re-authenticate if the replacement cookie was not received; this implementation intentionally does not make old-token replay idempotent.
- The BFF can still receive simultaneous 401 responses from requests that raced with a successful refresh. A separate browser/session UX pass should ensure a losing request does not unnecessarily clear a newer cookie written by the winning response.
- Access tokens remain short-lived. Existing logout, password reset, account deactivation, and session revocation behavior is unchanged.
