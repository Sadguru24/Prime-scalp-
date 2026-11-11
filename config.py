"""Central configuration and fail-closed validation for Prime Scalp SaaS."""

import math
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

load_dotenv()


class SaaSGlobalSystemSettings(BaseModel):
    """Validated runtime settings. Secrets must be supplied by the deployment environment."""

    model_config = ConfigDict(validate_default=True)

    firm_name: str = "Sadguru Traders"
    owner: str = "Saurabh Rameshlal Solanki"

    database_url: SecretStr = Field(
        default_factory=lambda: SecretStr(os.environ.get("DATABASE_URL", ""))
    )
    redis_url: SecretStr = Field(
        default_factory=lambda: SecretStr(os.environ.get("REDIS_URL", ""))
    )
    admin_jwt_secret: SecretStr = Field(
        default_factory=lambda: SecretStr(os.environ.get("ADMIN_JWT_SECRET", ""))
    )
    webhook_secret: SecretStr = Field(
        default_factory=lambda: SecretStr(os.environ.get("WEBHOOK_HMAC_SECRET", ""))
    )
    telegram_token: SecretStr = Field(
        default_factory=lambda: SecretStr(os.environ.get("TELEGRAM_BOT_TOKEN", ""))
    )
    chat_id: SecretStr = Field(
        default_factory=lambda: SecretStr(os.environ.get("TELEGRAM_CHAT_ID", ""))
    )

    # Capacity target is a configuration target, not proof of tested throughput.
    max_tenants_capacity: int = 500_000
    global_rate_limit_rate: float = 100.0
    http_port: int = 8080

    # Compliance must never be represented as completed by a default setting.
    fiu_ind_registered: bool = False
    kyc_aml_enforced: bool = False
    tds_194s_tracking_enabled: bool = False
    travel_rule_logging: bool = False
    dpdp_consent_verified: bool = False

    audit_filepath: str = "saas_master_audit_trail.jsonl"
    dlq_filepath: str = "saas_master_dlq.jsonl"

    @field_validator(
        "database_url",
        "redis_url",
        "admin_jwt_secret",
        "webhook_secret",
        "telegram_token",
        "chat_id",
        mode="before",
    )
    @classmethod
    def validate_required_secrets(cls, value: object, info):
        if isinstance(value, SecretStr):
            value = value.get_secret_value()
        secret = str(value).strip()
        placeholders = {"", "dummy_key", "dummy_secret", "default", "secret", "changeme", "null", "none"}
        if secret.lower() in placeholders:
            raise ValueError(f"{info.field_name} must be supplied securely; placeholder values are forbidden")
        return SecretStr(secret)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        parsed = urlparse(value.get_secret_value())
        if not parsed.scheme or not parsed.hostname:
            raise ValueError("database_url must be a valid URL with scheme and host")
        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: SecretStr) -> SecretStr:
        parsed = urlparse(value.get_secret_value())
        if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
            raise ValueError("redis_url must use redis:// or rediss:// and include a host")
        return value

    @field_validator("admin_jwt_secret", "webhook_secret")
    @classmethod
    def validate_cryptographic_secrets(cls, value: SecretStr, info) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError(f"{info.field_name} must contain at least 32 characters")
        return value

    @field_validator("max_tenants_capacity")
    @classmethod
    def validate_tenant_capacity(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_tenants_capacity must be greater than zero")
        return value

    @field_validator("global_rate_limit_rate")
    @classmethod
    def validate_rate_limit(cls, value: float) -> float:
        if not math.isfinite(value) or value <= 0:
            raise ValueError("global_rate_limit_rate must be a finite positive number")
        return value

    @field_validator("http_port")
    @classmethod
    def validate_http_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("http_port must be between 1 and 65535")
        return value
