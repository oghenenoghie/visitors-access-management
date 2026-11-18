# M9C — Dashboard security headers

## Changes

The admin dashboard now sends a baseline Content Security Policy and browser security headers on every route:

- `default-src 'self'`, `object-src 'none'`, `base-uri 'self'`, and `frame-ancestors 'none'`
- Same-origin form submissions and API connections
- No `unsafe-eval`
- HSTS in production only, with a one-year max age and subdomain coverage
- `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, strict-origin referrer policy, and a restrictive Permissions Policy

The current Next.js dashboard uses inline React style attributes and framework hydration scripts, so this baseline permits `'unsafe-inline'` for scripts and styles. It is a hardening step, not a nonce-based strict CSP. A nonce migration should be done separately with a verified Next.js rendering strategy and browser tests before removing those allowances.

The recovery-code copy action now joins codes with actual newline characters.

## Verification

CI runs dashboard lint and production build. Before production sign-off, verify the policy against deployed assets and integrations, inspect browser CSP reports/console output, confirm HTTPS and HSTS behavior, and exercise login, TOTP setup, recovery-code copy, and dashboard navigation.

## Not included

This change does not solve simultaneous refresh-token rotation across multiple BFF instances. That requires shared, durable coordination at the API/session layer; a process-local JavaScript lock is not an acceptable production fix.
