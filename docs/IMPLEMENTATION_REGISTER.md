# PRIME SCALP CRYPTO — Implementation Register

Status: structure and source-inventory stage. This register does not certify modules as complete.

## Preservation rules
- Preserve legacy source and its provenance; never overwrite it during a port.
- Port one module at a time and record source file, destination, changes, reviewer notes and verification evidence.
- Do not create fake production implementations or placeholder adapters that appear live.
- Keep live order submission disabled by default.
- Treat the user's estimate of 70%+ prior completion as a planning estimate until the repository and Library sources are inventoried.

## Existing project evidence
- Architecture, roadmap, legacy audit, customer connection policy and security baseline are documented under `docs/`.
- The legacy v8.2 source passed Python syntax compilation in the earlier recorded audit.
- The seven named crypto adapters were identified as unsupported placeholders in that source; each requires independent official-API implementation and verification.
- No APK/AAB build, exchange live integration, backtest result, load-test result or production certification is claimed by this register.

## Module inventory

| Area | Intended destination | Current evidence | Next action |
|---|---|---|---|
| Legacy strategy/indicator source | `trading/strategies/` | Prior Library source audit | Locate exact source versions; inventory and preserve |
| Market data | `trading/market_data/` | Architecture defined | Define normalized contracts and feed validation |
| Risk and kill switch | `trading/risk/` | Reusable concepts identified | Port individually; test edge cases and persistence |
| OMS and idempotency | `trading/oms/` | Reusable contracts identified | Verify state machine and durable recovery |
| Exchange adapters | `trading/exchanges/` | Legacy crypto adapters are placeholders | Select first exchange; implement against official docs |
| Backend API and tenants | `backend/` | Architecture defined | Define auth, tenant and API contracts |
| Android app | `android/` | Kotlin/Compose selected | Inspect existing source before adding app code |
| Infrastructure | `infra/` | Target architecture defined | Add CI and deployment definitions only after contracts |
| Automated tests | `tests/` | Test plan pending | Build unit/contract/integration suites alongside each port |

## Completion definition
A module is complete only when its source is reviewed, tests exist, tests pass in CI, security implications are reviewed, and evidence is recorded. Syntax compilation alone is not functional verification.
