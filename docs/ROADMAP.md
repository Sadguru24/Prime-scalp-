# PRIME SCALP CRYPTO — Delivery Roadmap

## Phase 0 — Repository and source audit
- [x] Confirm the Sadguru24 Prime-scalp repository and write access.
- [x] Initialize an empty repository with a README.
- [x] Create the development branch.
- [x] Retrieve and syntax-compile the legacy v8.2 Python source.
- [x] Record which crypto adapters are placeholders rather than live integrations.
- [ ] Audit remaining strategy, indicator, kill-switch and setup source documents.

## Phase 1 — Secure foundation
- [ ] Define API contracts, domain models and tenant boundaries.
- [ ] Add configuration validation and secret-management interfaces.
- [ ] Add database migrations, audit events and observability.
- [ ] Add CI: formatting, lint, type checks, unit tests, dependency/security scans.
- [ ] Establish a strict no-live-orders-by-default execution policy.

## Phase 2 — Trading core
- [ ] Port validated indicator and strategy modules with provenance and tests.
- [ ] Port risk rules and kill-switch logic; test edge cases and persistence.
- [ ] Implement durable OMS state machine and idempotent order intents.
- [ ] Implement reconciliation from exchange truth; handle partial fills and unknown states.
- [ ] Add deterministic tests using clearly identified fixtures (never production market data claims).

## Phase 3 — First exchange integration
- [ ] Select one exchange based on official API support and legal/account availability.
- [ ] Implement authentication, market data, instruments/precision, balances, orders, order status, cancellation and positions.
- [ ] Verify signatures, timestamps, rate limits, reconnects, WebSocket sequence gaps and API error handling.
- [ ] Run integration tests against an exchange-provided sandbox only if officially available; clearly distinguish sandbox from live.
- [ ] Keep live trading disabled until an explicit release gate is approved.

## Phase 4 — SaaS and Android
- [ ] Implement subscriptions and entitlement enforcement.
- [ ] Build Android app: sign-in, onboarding, exchange connection, strategy settings, risk settings, orders, positions, alerts and account controls.
- [ ] Add admin/support console and customer data export/deletion workflows.
- [ ] Build signed APK and AAB through CI; verify artifact signatures, installability and release metadata.

## Phase 5 — Production readiness
- [ ] Tenant-isolation, auth, API-key storage and penetration/security tests.
- [ ] Load, soak, rate-limit, outage, reconnect, crash-recovery and disaster-recovery tests.
- [ ] Verify order lifecycle and reconciliation under partial/duplicate/timeout/unknown responses.
- [ ] Complete legal/compliance review for target markets and subscription operations.
- [ ] Obtain separate explicit approval before enabling live trading or production deployment.

## Release gates
A phase is complete only with recorded test evidence. A green syntax compile or successful CI run alone is not production certification. No performance/profit guarantee is made.
