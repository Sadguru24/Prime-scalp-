# Customer Connections, Telegram Alerts and Security Model

## Product model
PRIME SCALP CRYPTO is a subscription SaaS. Customers retain funds in their own exchange accounts. The service charges a disclosed recurring subscription fee; it does not take custody of customer deposits and does not charge a percentage of trading profits in the initial model. Do not imply that non-custodial architecture removes legal or regulatory obligations.

## Customer onboarding
1. Customer creates a PRIME SCALP CRYPTO account and completes required identity, eligibility and risk disclosures.
2. Customer selects a supported exchange and creates a dedicated API key at that exchange.
3. Customer enters API key and API secret only into the authenticated HTTPS connection flow in the app.
4. The backend validates the key with the exchange and checks available permissions. It must never request the customer's exchange login password.
5. Customer may optionally connect Telegram by providing a bot token and chat ID for notifications.
6. Customer explicitly chooses allowed products (spot/perpetual futures), symbols, risk limits and whether automated execution is enabled.
7. The service checks subscription entitlement before enabling paid features.

## Exchange credential permissions
- Request only the minimum permissions needed: read balances/positions/orders and trade permission only when the customer explicitly enables automated trading.
- Withdrawal, transfer, asset movement and account-management permissions must be disabled and rejected where the exchange exposes permission inspection.
- Prefer exchange IP allowlisting to fixed service egress IPs where supported.
- Provide disconnect, revoke-key guidance, credential rotation and emergency disable controls.
- Never send exchange API credentials to Telegram, analytics, crash reports, logs, support tickets or mobile push payloads.

## Telegram
- Telegram bot token is a secret and must be stored in the same protected secret store as other credentials.
- Chat ID is routing metadata, not an authentication secret; verify chat ownership with a one-time challenge before linking.
- Telegram is notifications-only in the initial product. Do not accept trading commands through Telegram.
- Notifications must not contain API secrets, passwords, recovery codes or unnecessarily sensitive account details.
- Support token rotation, unlinking and revocation.

## Encryption and key management
- Use TLS 1.2+ (prefer TLS 1.3) for all network connections.
- Encrypt each credential using envelope encryption with AES-256-GCM and a unique nonce; use authenticated associated data binding ciphertext to tenant ID, connection ID, credential type and version.
- Wrap data-encryption keys with a managed KMS/HSM key. Keep wrapping keys separate from the database and application source.
- Restrict decrypt permissions to the specific exchange worker identity that needs a credential; use short-lived workload identity and least privilege.
- Do not expose plaintext secrets to application logs, traces, metrics, error messages or admin dashboards. Mask all credential fields after initial submission.
- Implement rotation, revocation, deletion, access audit trails, key-version metadata, backup/restore controls and incident response.
- Add secret scanning to CI and block commits containing credentials.
- AES-256-GCM is an encryption component, not a guarantee of overall security. Security also depends on identity, authorization, key custody, runtime isolation, monitoring and operations.

## Trading and leverage policy
- Never automatically use the customer's maximum available balance or maximum exchange leverage.
- Determine position size from customer-approved risk per trade, stop distance, available margin, portfolio exposure, liquidation distance, instrument limits and exchange rules.
- Enforce hard caps for leverage, notional exposure, daily loss, drawdown, open positions and correlated exposure.
- Reject orders when balance, margin, price, instrument metadata or market data is stale or ambiguous.
- Apply reduce-only/close-only safeguards where supported, and maintain account-level and global kill switches.
- Show estimated liquidation price, margin use, fees, funding and worst-case loss before enabling a strategy where the exchange data supports it.
- No profit guarantee. Futures and leverage can cause rapid losses, including liquidation.

## Subscription model
- Monthly and annual subscription entitlements control access to strategy tiers, number of connected exchange accounts, alerting and automation features.
- Billing state must not silently change trading risk settings. On expiry or failed renewal, follow a documented customer policy: stop opening new positions, preserve protective risk controls, and provide a clear position-management notice. Do not abruptly abandon open positions.
- Keep subscription billing separate from exchange balances and trading P&L.

## Mandatory security and release gates
- Threat model and abuse-case review.
- Tenant-isolation and authorization tests.
- Credential encryption/decryption, rotation, revocation and key-compromise drills.
- API secret redaction tests across logs, traces and crash reports.
- Authentication, MFA and session security tests.
- Dependency, SAST, DAST and container/image scans.
- Exchange signature, timestamp, replay, rate-limit and IP allowlist tests.
- OMS idempotency, partial fill, timeout, unknown order state and reconciliation tests.
- Load, soak, failover, backup restore and incident-response exercises.
- Independent penetration test before production launch.
- Legal/compliance review for each target market and exchange/product.

## Explicit non-goals for initial release
- No custody or withdrawal/transfer of customer funds.
- No exchange account passwords.
- No Telegram-based trading commands.
- No automatic maximum leverage or all-balance exposure.
- No live execution until exchange-specific API, security and operational gates pass.
