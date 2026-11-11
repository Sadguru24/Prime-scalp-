"""Rate of Change momentum strategy for Prime Scalp.

The strategy calculates percentage price momentum and emits signals only when
ROC crosses its zero line. It does not submit, route, or manage broker orders.
"""

from __future__ import annotations

from numbers import Integral

import numpy as np
import pandas as pd


class RateOfChangeStrategy:
    """Calculate ROC and zero-line crossover signals.

    Args:
        period: Number of observations used as the ROC lookback. Must be a
            positive integer (booleans are not accepted).

    Notes:
        The input DataFrame is never mutated. Missing close observations remain
        missing and naturally suppress signals until valid comparisons exist.
    """

    def __init__(self, period: int = 12) -> None:
        if isinstance(period, bool) or not isinstance(period, Integral) or period <= 0:
            raise ValueError("period must be a positive integer")
        self.period = int(period)

    @staticmethod
    def _validated_close(data: pd.DataFrame) -> pd.Series:
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")
        if "close" not in data.columns:
            raise ValueError("Missing required column: close")

        close = data["close"]
        if not pd.api.types.is_numeric_dtype(close.dtype) or pd.api.types.is_bool_dtype(close.dtype):
            raise TypeError("close column must contain numeric prices")

        values = close.to_numpy(dtype="float64", na_value=np.nan)
        present = ~np.isnan(values)
        if np.any(~np.isfinite(values[present])):
            raise ValueError("close values must be finite when present")
        if np.any(values[present] <= 0.0):
            raise ValueError("close prices must be greater than zero")
        return close.astype("float64")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of the input with the ROC percentage column added."""
        close = self._validated_close(df)
        previous_close = close.shift(self.period)
        roc = ((close - previous_close) / previous_close) * 100.0
        result = df.copy(deep=True)
        result["roc"] = roc
        return result

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy with ROC and int8 signal (-1, 0, or 1)."""
        result = self.calculate_indicators(df)
        current = result["roc"]
        previous = current.shift(1)

        signal = pd.Series(0, index=result.index, dtype="int8")
        signal.loc[(current > 0.0) & (previous <= 0.0)] = 1
        signal.loc[(current < 0.0) & (previous >= 0.0)] = -1
        result["signal"] = signal
        return result
