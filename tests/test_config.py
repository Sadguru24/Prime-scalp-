"""Unit tests for validated Prime Scalp global configuration."""

import pytest
from pydantic import ValidationError

from config import SaaSGlobalSystemSettings


@pytest.fixture
def configured_environment(monkeypatch):
    values = {
        "DATABASE_URL": "postgresql://prime:strong-password@db.example.com/prime",
        "REDIS_URL": "rediss://redis.example.com:6379/0",
        "ADMIN_JWT_SECRET": "a" * 40,
        "WEBHOOK_HMAC_SECRET": "b" * 40,
        "TELEGRAM_BOT_TOKEN": "telegram-token-value",
        "TELEGRAM_CHAT_ID": "123456789",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return values


def test_default_capacity_is_500000(configured_environment):
    settings = SaaSGlobalSystemSettings()
    assert settings.max_tenants_capacity == 500_000


def test_compliance_claims_default_to_false(configured_environment):
    settings = SaaSGlobalSystemSettings()
    assert settings.fiu_ind_registered is False
    assert settings.kyc_aml_enforced is False
    assert settings.tds_194s_tracking_enabled is False
    assert settings.travel_rule_logging is False
    assert settings.dpdp_consent_verified is False


def test_secrets_are_masked_in_model_representation(configured_environment):
    settings = SaaSGlobalSystemSettings()
    assert "a" * 40 not in repr(settings)
    assert "b" * 40 not in repr(settings)


@pytest.mark.parametrize("field", [
    "DATABASE_URL", "REDIS_URL", "ADMIN_JWT_SECRET", "WEBHOOK_HMAC_SECRET",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
])
def test_missing_required_secret_is_rejected(configured_environment, monkeypatch, field):
    monkeypatch.setenv(field, "")
    with pytest.raises(ValidationError):
        SaaSGlobalSystemSettings()


@pytest.mark.parametrize("field", ["ADMIN_JWT_SECRET", "WEBHOOK_HMAC_SECRET"])
def test_short_cryptographic_secret_is_rejected(configured_environment, monkeypatch, field):
    monkeypatch.setenv(field, "too-short")
    with pytest.raises(ValidationError):
        SaaSGlobalSystemSettings()


@pytest.mark.parametrize("value", ["not-a-url", "postgresql://"])
def test_invalid_database_url_is_rejected(configured_environment, monkeypatch, value):
    monkeypatch.setenv("DATABASE_URL", value)
    with pytest.raises(ValidationError):
        SaaSGlobalSystemSettings()


@pytest.mark.parametrize("value", ["http://redis.example.com", "redis://"])
def test_invalid_redis_url_is_rejected(configured_environment, monkeypatch, value):
    monkeypatch.setenv("REDIS_URL", value)
    with pytest.raises(ValidationError):
        SaaSGlobalSystemSettings()


@pytest.mark.parametrize("value", [0, -1])
def test_non_positive_capacity_is_rejected(configured_environment, value):
    with pytest.raises(ValidationError):
        SaaSGlobalSystemSettings(max_tenants_capacity=value)


@pytest.mark.parametrize("value", [0, -0.1, float("nan"), float("inf"), float("-inf")])
def test_invalid_rate_limit_is_rejected(configured_environment, value):
    with pytest.raises(ValidationError):
        SaaSGlobalSystemSettings(global_rate_limit_rate=value)


@pytest.mark.parametrize("value", [0, -1, 65536])
def test_invalid_port_is_rejected(configured_environment, value):
    with pytest.raises(ValidationError):
        SaaSGlobalSystemSettings(http_port=value)


@pytest.mark.parametrize("value", [1, 8080, 65535])
def test_valid_port_boundaries_are_accepted(configured_environment, value):
    settings = SaaSGlobalSystemSettings(http_port=value)
    assert settings.http_port == value


def test_explicit_capacity_override_is_supported(configured_environment):
    settings = SaaSGlobalSystemSettings(max_tenants_capacity=750_000)
    assert settings.max_tenants_capacity == 750_000
