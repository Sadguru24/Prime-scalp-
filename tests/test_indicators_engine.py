"""Focused regression tests for Prime Scalp indicator calculations."""
import math
import pytest

from indicators_engine import (
    ProductionDataError,
    atr_series,
    bollinger,
    dmi_adx,
    ema_series,
    indicators,
    kama,
    macd,
    rsi_series,
    smc_fvg_and_blocks,
    validate_snapshot,
)


def make_snapshot(count=150):
    closes = [100.0 + i * 0.2 + math.sin(i / 4) for i in range(count)]
    highs = [value + 1.0 for value in closes]
    lows = [value - 1.0 for value in closes]
    return {
        "tenant_id": "tenant-a",
        "strategy_id": "strategy-a",
        "signal_id": "signal-a",
        "symbol": "NSE:TEST",
        "closes": closes,
        "highs": highs,
        "lows": lows,
        "volumes": [1000.0] * count,
        "timestamps": [1_800_000_000 + i * 60 for i in range(count)],
        "bid": closes[-1] - 0.05,
        "ask": closes[-1] + 0.05,
        "timeframe_s": 60,
    }


def test_valid_snapshot_does_not_mutate_timestamps():
    snapshot = make_snapshot()
    original = list(snapshot["timestamps"])
    assert validate_snapshot(snapshot) == (True, "passed")
    assert snapshot["timestamps"] == original


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), "not-a-number"])
def test_snapshot_rejects_non_finite_or_non_numeric_close(bad):
    snapshot = make_snapshot()
    snapshot["closes"][10] = bad
    valid, reason = validate_snapshot(snapshot)
    assert not valid
    assert "close" in reason or "non_finite" in reason or "invalid_numeric" in reason


def test_snapshot_rejects_duplicate_timestamps():
    snapshot = make_snapshot()
    snapshot["timestamps"][20] = snapshot["timestamps"][19]
    assert validate_snapshot(snapshot)[0] is False


def test_snapshot_rejects_bad_ohlc_and_quote():
    snapshot = make_snapshot()
    snapshot["highs"][30] = snapshot["lows"][30] - 1
    assert validate_snapshot(snapshot)[0] is False
    snapshot = make_snapshot()
    snapshot["ask"] = snapshot["bid"] - 1
    assert validate_snapshot(snapshot) == (False, "invalid_bid_ask")


def test_snapshot_rejects_short_history():
    assert "insufficient_history" in validate_snapshot(make_snapshot(149))[1]


def test_ema_validates_period_and_history():
    assert len(ema_series([1.0, 2.0, 3.0], 2)) == 3
    with pytest.raises(ProductionDataError):
        ema_series([1.0], 2)
    with pytest.raises(ProductionDataError):
        ema_series([1.0, 2.0], 0)


def test_kama_tracks_flat_series_and_rejects_bad_parameters():
    assert kama([10.0] * 20, period=10) == pytest.approx(10.0)
    with pytest.raises(ProductionDataError):
        kama([10.0] * 10, period=10)
    with pytest.raises(ProductionDataError):
        kama([10.0] * 20, fast=30, slow=2)


def test_rsi_handles_flat_up_and_down_series():
    assert rsi_series([5.0] * 20)[-1] == pytest.approx(50.0)
    assert rsi_series([float(i + 1) for i in range(20)])[-1] == pytest.approx(100.0)
    assert rsi_series([float(20 - i) for i in range(20)])[-1] == pytest.approx(0.0)


def test_atr_wilder_series_and_length_validation():
    highs = [11.0, 12.0, 13.0, 14.0]
    lows = [9.0, 10.0, 11.0, 12.0]
    closes = [10.0, 11.0, 12.0, 13.0]
    result = atr_series(highs, lows, closes, period=2)
    assert len(result) == 4
    assert result[-1] == pytest.approx(2.0)
    with pytest.raises(ProductionDataError):
        atr_series(highs, lows[:-1], closes, period=2)


def test_adx_requires_history_and_never_returns_fabricated_fallback():
    with pytest.raises(ProductionDataError):
        dmi_adx([11.0] * 9, [9.0] * 9, [10.0] * 9, period=5)
    flat = dmi_adx([11.0] * 10, [9.0] * 10, [10.0] * 10, period=5)
    assert flat == pytest.approx((0.0, 0.0, 0.0))


def test_bollinger_uses_sample_standard_deviation():
    upper, lower, middle = bollinger([1.0, 2.0, 3.0], period=3, deviations=1.0)
    assert middle == pytest.approx(2.0)
    assert upper == pytest.approx(3.0)
    assert lower == pytest.approx(1.0)
    with pytest.raises(ProductionDataError):
        bollinger([1.0], period=20)


def test_macd_returns_current_and_previous_histogram():
    result = macd([float(i + 1) for i in range(60)])
    assert len(result) == 4
    assert all(math.isfinite(value) for value in result)
    with pytest.raises(ProductionDataError):
        macd([1.0] * 20)


def test_smc_detects_fvg_and_returns_rolling_extrema():
    highs = [10.0] * 20
    lows = [9.0] * 20
    closes = [9.5] * 20
    highs[-3] = 10.0
    lows[-1] = 11.0
    highs[-1] = 12.0
    closes[-1] = 11.5
    result = smc_fvg_and_blocks(highs, lows, closes, lookback=20)
    assert result[0] is True
    assert result[2] == pytest.approx(9.0)
    assert result[3] == pytest.approx(12.0)


def test_indicators_validates_snapshot_and_returns_finite_bundle():
    snapshot = make_snapshot()
    result = indicators(snapshot)
    assert {"rsi", "atr", "adx", "kama", "macd", "ema9", "ema20"} <= result.keys()
    assert all(math.isfinite(value) for value in result.values())
    snapshot["closes"][0] = float("nan")
    with pytest.raises(ProductionDataError):
        indicators(snapshot)


def test_indicator_tags_are_distinct():
    from indicators_engine import generate_indicator_tag
    assert generate_indicator_tag("NSE:TEST") != generate_indicator_tag("NSE:TEST")
