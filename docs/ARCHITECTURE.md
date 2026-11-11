# PRIME SCALP CRYPTO — Initial Architecture

## Product
A multi-tenant automated cryptocurrency trading SaaS with an Android client distributed as APK (direct installation/testing) and AAB (Google Play submission). The backend and trading workers run in cloud infrastructure; the Android app is not responsible for holding exchange secrets or executing strategies locally.

## High-level components
1. Android client — Kotlin, Jetpack Compose; authentication, subscription status, exchange connection setup, strategy controls, positions, orders, risk settings, alerts and reports.
2. API service — Python/FastAPI; authentication, authorization, tenant/account management, subscription entitlements and customer-facing APIs.
3. Trading control plane — strategy configuration, approvals, risk policies, scheduling and kill-switch control.
4. Market-data services — exchange WebSocket/REST clients, normalized instruments/tickers/candles, freshness and integrity checks.
5. Strategy engine — indicator calculation, setup evaluation, signal ranking and strategy versioning.
6. Risk engine — position sizing, exposure/leverage limits, loss limits, stale-feed checks, duplicate prevention and kill switches.
7. Execution/OMS — durable order intents, idempotency, exchange acknowledgements, state transitions, fills, cancellation and reconciliation.
8. Persistence — PostgreSQL for durable business/trading state; Redis only for cache/queues/ephemeral coordination.
9. Workers — isolated exchange and tenant workloads, retry policies, dead-letter handling and rate-limit governance.
10. Observability — structured logs, metrics, traces, audit events, alerts and incident controls.
11. Subscription/billing — plans, entitlements, invoices/payment-provider integration and renewal/cancellation workflows.
12. Admin console — tenant support, exchange health, operational controls and auditable administrative actions.

## Security boundaries
- Customer funds remain on the customer's exchange account.
- API keys must be trade-only where supported; withdrawal permissions must remain disabled.
- Encrypt secrets with managed key encryption; never log secrets or store them in source control.
- Tenant-scoped authorization must be enforced at every API and data-access boundary.
- Separate customer API service from trading workers; least-privilege service identities.
- Require explicit customer opt-in and risk acknowledgement before enabling automated execution.
- Live execution remains disabled until the exchange adapter, risk gates, recovery behavior and compliance review pass.

## Initial repository layout
```text
.
├── android/                 # Kotlin Android app; APK/AAB build
├── backend/
│   ├── api/
│   ├── auth/
│   ├── tenants/
│   ├── subscriptions/
│   └── admin/
├── trading/
│   ├── market_data/
│   ├── strategies/
│   ├── risk/
│   ├── oms/
│   ├── execution/
│   ├── reconciliation/
│   └── exchanges/
├── infra/
├── tests/
├── docs/
├── .github/workflows/
└── README.md
```

## First exchange
Choose one exchange as the first fully supported integration only after verifying its official API documentation, jurisdictional availability, account eligibility, rate limits, product types and current order/position endpoints. Do not advertise all seven legacy exchange names as supported until each is verified.
