from math import isclose

import pytest

from prime_scalp_strategy_suite import (
    Candle, OptionQuote, OptionRight, PositionSide, Regime, Signal,
    classify_regime, evaluate_swing, select_protective_hedge,
)


def test_regime_requires_enough_history():
    result = classify_regime([Candle(100, 101, 99, 100, 1000)])
    assert result.regime is Regime.INSUFFICIENT_DATA


def test_regime_rejects_invalid_candle():
    with pytest.raises(ValueError):
        classify_regime([Candle(100, 98, 99, 100, 10)])


def test_regime_classifies_flat_market_as_range():
    candles = [Candle(100, 100.5, 99.5, 100, 1000) for _ in range(40)]
    assert classify_regime(candles).regime is Regime.RANGE_BOUND


def test_swing_holds_when_history_is_short():
    assert evaluate_swing([100, 101]).signal is Signal.HOLD


def test_swing_rejects_nan():
    with pytest.raises(ValueError):
        evaluate_swing([100.0, float("nan")])


def test_hedge_selects_put_for_long():
    chain = [
        OptionQuote("PUT1", OptionRight.PUT, 100, 20, 2.0, 2.1, -0.30, 1000, 100, 50),
        OptionQuote("CALL1", OptionRight.CALL, 100, 20, 2.0, 2.1, 0.30, 1000, 100, 50),
    ]
    result = select_protective_hedge(PositionSide.LONG, chain)
    assert result.selected
    assert result.symbol == "PUT1"
    assert isclose(result.estimated_lot_cost, 105.0)


def test_hedge_returns_no_selection_when_filters_fail():
    chain = [OptionQuote("PUT1", OptionRight.PUT, 100, 20, 2.0, 2.1, -0.3, 1, 1, 50)]
    assert not select_protective_hedge(PositionSide.LONG, chain).selected


def test_hedge_rejects_invalid_quote():
    chain = [OptionQuote("PUT1", OptionRight.PUT, 100, 20, 3.0, 2.0, -0.3, 1000, 100, 50)]
    with pytest.raises(ValueError):
        select_protective_hedge(PositionSide.LONG, chain)
