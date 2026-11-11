# Legacy PRIME SCALP source audit

Audit date: 2026-11-12

## Source inspected
- Library source: `prime_scalp_all_in_one_v8_2_HQ.py`
- Size: 21,958 bytes; 783 lines
- Python syntax compilation: PASS (Python 3)
- AST inventory: 41 top-level classes and 8 top-level functions

## Reusable foundations (subject to targeted tests and refactoring)
- Decimal-based order intent and instrument-rule validation
- Canonical hashing and idempotency-store interface
- Explicit production-environment gate
- Kill-switch and health-gate concepts
- Strict market snapshot validation
- Order/result/position contracts
- Reconciliation interface and final trade approval gate

## Not production-ready / must not be represented as complete
- The 7 crypto adapter classes (Delta Exchange, CoinDCX, CoinSwitch, Mudrex, Shark Exchange, Pi42, WazirX) inherit methods that deliberately raise `UnsupportedLiveAPIError`. They are registry placeholders, not working exchange integrations.
- Broker-specific authentication, live market-data, order placement, order status, cancellation, balances and positions must be implemented against each exchange's current official API and tested independently.
- The source mixes Indian broker adapters with crypto adapter slots. Only crypto-relevant contracts should be extracted into the crypto package.
- A successful syntax compile is not proof of correct trading behavior, API connectivity, security or production readiness.

## Adoption decision
Use the source as an audited reference foundation, not as a drop-in live trading engine. Port components individually with unit tests, type/contract checks and code review. Keep live order execution disabled until exchange-specific verification and release approvals pass.

## Hard safety requirements
- No fake market data, fake fills, fake order IDs or fabricated P&L in production.
- No withdrawal permission requested for customer API keys.
- Encrypt credentials at rest; never commit secrets.
- Enforce tenant isolation, least privilege, idempotency, reconciliation and global/per-account kill switches.
- Fail closed when an exchange API is unsupported, stale, ambiguous or unavailable.
