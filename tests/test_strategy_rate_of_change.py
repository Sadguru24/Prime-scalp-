import numpy as np
import pandas as pd
import pytest

from strategy_rate_of_change import RateOfChangeStrategy


def test_roc_values_and_zero_crossing_signals():
    frame = pd.DataFrame({"close": [100.0, 90.0, 95.0, 110.0, 100.0, 80.0]})
    result = RateOfChangeStrategy(period=1).generate_signals(frame)
    assert result["roc"].iloc[1] == pytest.approx(-10.0)
    assert result["signal"].tolist() == [0, 0, 1, 0, -1, 0]


def test_does_not_mutate_input_or_drop_other_columns():
    frame = pd.DataFrame({"close": [10.0, 11.0, 12.0], "volume": [1, 2, 3]})
    original = frame.copy(deep=True)
    result = RateOfChangeStrategy(1).calculate_indicators(frame)
    pd.testing.assert_frame_equal(frame, original)
    assert "volume" in result.columns and "roc" in result.columns


@pytest.mark.parametrize("period", [0, -1, 1.5, True, "2", None])
def test_rejects_invalid_period(period):
    with pytest.raises(ValueError):
        RateOfChangeStrategy(period)


def test_missing_close_column_rejected():
    with pytest.raises(ValueError, match="close"):
        RateOfChangeStrategy().calculate_indicators(pd.DataFrame({"price": [1.0]}))


@pytest.mark.parametrize("bad", [0.0, -1.0, np.inf, -np.inf])
def test_rejects_nonpositive_or_nonfinite_prices(bad):
    with pytest.raises(ValueError):
        RateOfChangeStrategy(1).calculate_indicators(pd.DataFrame({"close": [100.0, bad]}))


def test_rejects_non_numeric_and_boolean_close():
    for values in (["100", "101"], [True, False]):
        with pytest.raises(TypeError):
            RateOfChangeStrategy(1).calculate_indicators(pd.DataFrame({"close": values}))


def test_missing_values_do_not_create_signals():
    result = RateOfChangeStrategy(1).generate_signals(
        pd.DataFrame({"close": [100.0, np.nan, 110.0, 90.0]})
    )
    assert result["signal"].tolist() == [0, 0, 0, 0]


def test_empty_and_short_inputs_are_supported():
    strategy = RateOfChangeStrategy(3)
    assert strategy.generate_signals(pd.DataFrame({"close": []}))["signal"].empty
    assert strategy.generate_signals(pd.DataFrame({"close": [10.0, 11.0]}))["signal"].tolist() == [0, 0]
