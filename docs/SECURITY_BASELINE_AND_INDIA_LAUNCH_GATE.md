# PRIME SCALP CRYPTO — Security Baseline (Target Controls)

This is the engineering baseline, not a claim of certification. Controls must be implemented, tested and independently assessed before launch.

## Identity and customer account security
- Passkeys (WebAuthn/FIDO2) as preferred sign-in; TOTP authenticator MFA fallback. Do not use SMS as the sole second factor.
- Strong password hashing with Argon2id for password-based accounts; breached-password screening and secure recovery.
- Short-lived access tokens, rotating refresh tokens, session/device management, re-authentication for sensitive actions.
- RBAC/ABAC authorization, tenant-scoped object access, deny-by-default policies and rate limits.
- Optional customer IP/device alerts and new-device verification.

## Exchange and Telegram secrets
- API keys must be dedicated to this app, least-privilege, trade-only where required, with withdrawals/transfers disabled.
- AES-256-GCM envelope encryption with per-secret data keys; KMS/HSM-wrapped keys; strict workload identity and audited decrypt operations.
- Never store exchange account passwords. Never expose plaintext API keys after submission.
- Telegram token treated as a secret; chat ID ownership verified. Telegram is notifications-only in v1.
- Redact secrets from logs, traces, crash reports, analytics, support exports and admin screens.
- Support rotation, revoke/disconnect, deletion and emergency credential disable.

## Application, API and infrastructure
- TLS 1.3 preferred (TLS 1.2 minimum where required); HSTS and secure mobile network configuration.
- WAF, DDoS protection, API gateway, schema validation, request size limits, per-user/IP throttling and bot/credential-stuffing detection.
- Private subnets, no public database/Redis, network segmentation, egress allowlists and fixed egress IPs for exchange allowlisting where supported.
- Hardened containers, non-root runtime, read-only filesystems where practical, signed images, SBOM and vulnerability scanning.
- Secrets manager; no secrets in GitHub, APK, AAB, environment dumps or build logs.
- Encrypted backups, tested restores, key separation and disaster-recovery exercises.

## Trading safety controls
- Per-customer and global kill switches; maximum leverage, notional, margin and open-position caps.
- Risk-based sizing from customer-selected risk, stop distance, available margin, fees/funding, liquidation distance and instrument rules.
- Never auto-use all available balance or maximum exchange leverage.
- Stale-feed rejection, price collars, duplicate-order idempotency, order-state machine and reconciliation.
- Explicit opt-in per exchange, product type and strategy; show risks and obtain confirmation before first live activation.
- Safe expiry policy for subscriptions: no new entries after expiry, while preserving protective controls and notifying the customer about open positions.

## Secure development and assurance
- Threat model and abuse-case review before implementation.
- SAST, dependency/SCA, secret scanning, container scanning, DAST and mobile security testing in CI.
- Unit/integration/property-based/fuzz tests for auth, tenancy, credential vault, exchange signatures and OMS state transitions.
- Independent penetration test and remediation retest before production.
- Incident response playbooks, on-call escalation, breach notification workflow and key-compromise drills.
- Immutable/tamper-evident audit trail for security-sensitive actions.

## India launch compliance gate
- Obtain a written Indian legal opinion classifying the exact service model: non-custodial API software, automated order transmission, exchange connectivity, customer onboarding, fees, support and any future custody/transfer features.
- Do not assume that non-custodial SaaS is automatically outside PMLA/FIU-IND. FIU-IND materials describe activity-based VDA service-provider obligations; applicability to this precise software-only model requires legal analysis.
- If the business falls within a reporting-entity/VDA-SP category, complete FIU-IND registration and applicable AML/CFT, KYC, recordkeeping, reporting and designated-officer requirements before offering the regulated service.
- Assess CERT-In directions, including incident reporting, log retention, point-of-contact and time synchronisation obligations for the actual entity/service-provider role.
- Implement DPDP Act/Rules obligations according to their applicable commencement timeline: clear notice, lawful purpose, data minimisation, security safeguards, processor contracts, rights/grievance workflow, retention/deletion and breach response.
- Review GST, subscription invoicing, consumer terms, advertising/performance claims, exchange terms, cross-border data processing and target-country rules.
- Reassess legal scope before adding custody, transfers, fiat ramps, copy trading, pooled funds, profit sharing or discretionary account control.

## No certification claims
Do not market the product as "world's most secure", "unhackable", SOC 2/ISO certified or regulator-approved unless independently certified/approved and current evidence exists. Describe implemented controls precisely.
