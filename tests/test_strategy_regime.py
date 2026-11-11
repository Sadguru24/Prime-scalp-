"""Focused safety and behavior tests for the market-regime classifier."""

import pytest

from strategy_regime import MarketRegimeDetector, MarketRegimeStrategy


def rising_closes():
    return [100.0 + index for index in range(30)]


def falling_closes():
    return [130.0 - index for index in range(30)]


def test_bull_trend_is_detected_from_aligned_price_structure():
    result = MarketRegimeStrategy().detect_regime({"closes": rising_closes(), "adx": 35.0})
    assert result["regime"] == "BULL_TREND"
    assert result["confidence"] == 35.0


def test_bear_trend_is_detected_from_aligned_price_structure():
    result = MarketRegimeStrategy().detect_regime({"closes": falling_closes(), "adx": 35.0})
    assert result["regime"] == "BEAR_TREND"


def test_low_adx_is_classified_as_sideways():
    result = MarketRegimeStrategy().detect_regime({"closes": [100.0] * 30, "adx": 10.0})
    assert result["regime"] == "SIDEWAYS"
    assert result["confidence"] == 90.0


def test_high_adx_without_directional_alignment_is_transition():
    closes = [120.0] * 20 + [100.0] * 9 + [130.0]
    result = MarketRegimeStrategy().detect_regime({"closes": closes, "adx": 35.0})
    assert result["regime"] == "TRANSITION_TREND"


def test_insufficient_history_returns_unknown_without_fabricated_regime():
    result = MarketRegimeStrategy().detect_regime({"closes": [100.0] * 29, "adx": 15.0})
    assert result["regime"] == "UNKNOWN"
    assert result["confidence"] == 0.0


def test_missing_adx_is_rejected_instead_of_defaulting_to_zero():
    with pytest.raises(ValueError, match="adx"):
        MarketRegimeStrategy().detect_regime({"closes": rising_closes()})


@pytest.mark.parametrize("adx", [float("nan"), float("inf"), -0.1, 100.1, True, "bad"])
def test_invalid_adx_is_rejected(adx):
    with pytest.raises(ValueError):
        MarketRegimeStrategy().detect_regime({"closes": rising_closes(), "adx": adx})


@pytest.mark.parametrize("price", [0.0, -1.0, float("nan"), float("inf"), True])
def test_invalid_closing_price_is_rejected(price):
    closes = rising_closes()
    closes[-1] = price
    with pytest.raises(ValueError):
        MarketRegimeStrategy().detect_regime({"closes": closes, "adx": 30.0})


@pytest.mark.parametrize("cutoff", [0.0, -1.0, 100.1, float("nan"), float("inf"), True])
def test_invalid_adx_cutoff_is_rejected(cutoff):
    with pytest.raises(ValueError):
        MarketRegimeStrategy(adx_trend_cutoff=cutoff)


def test_legacy_detector_name_remains_compatible():
    assert MarketRegimeDetector is MarketRegimeStrategy


def test_non_mapping_snapshot_is_rejected():
    with pytest.raises(TypeError):
        MarketRegimeStrategy().detect_regime([])


def test_non_sequence_closes_are_rejected():
    with pytest.raises(TypeError):
        MarketRegimeStrategy().detect_regime({"closes": 100, "adx": 30})
