# File-by-file verification register

This is the authoritative checklist for inspecting existing files and newly added modules one at a time.

## Required record per file
- File path and source provenance
- Purpose and public interfaces
- Imports/dependencies and configuration requirements
- Security and tenant-isolation impact
- Error handling, retries, idempotency and recovery behavior (where relevant)
- Static checks and unit/contract tests
- Integration evidence, if applicable
- Result: NOT REVIEWED / PASS / FAIL / BLOCKED
- Defects and follow-up commit

## Verification sequence
1. Repository tree and source provenance
2. Configuration, domain models and shared contracts
3. Authentication, authorization and tenant isolation
4. Market data and instrument normalization
5. Indicators and strategy modules
6. Risk engine and kill switches
7. OMS, execution and reconciliation
8. Exchange adapters, one exchange at a time
9. Subscription, notifications and admin
10. Android client and build pipeline
11. Security, load, soak and recovery testing

## Evidence rules
- Never mark a file PASS merely because it exists or compiles.
- Never represent fixtures as real exchange data or fills.
- Record exact commands, CI run links, test counts and failures when available.
- Live trading and production deployment remain separate approval gates.
