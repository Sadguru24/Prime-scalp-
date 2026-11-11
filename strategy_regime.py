"""Prime Scalp market-regime classifier.

Consumes validated OHLCV candles and returns a deterministic regime assessment.
This module never places orders and never fabricates market data.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Sequence


class Regime(str, Enum):
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGE_BOUND = "RANGE_BOUND"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: float

    def validate(self) -> None:
        values = (self.open, self.high, self.low, self.close, self.volume)
        if not all(isfinite(float(v)) for v in values):
            raise ValueError("Candle values must be finite numbers")
        if min(self.open, self.high, self.low, self.close, self.volume) < 0:
            raise ValueError("Candle values cannot be negative")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("Candle high is inconsistent")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("Candle low is inconsistent")
        if self.close <= 0:
            raise ValueError("Candle close must be positive")


@dataclass(frozen=True)
class RegimeAssessment:
    regime: Regime
    confidence: float
    atr_pct: float
    directional_strength: float
    reason: str


def _ema(values: Sequence[float], period: int) -> float:
    alpha = 2.0 / (period + 1.0)
    result = float(values[0])
    for value in values[1:]:
        result = alpha * float(value) + (1.0 - alpha) * result
    return result


def classify_regime(
    candles: Sequence[Candle],
    *,
    fast_period: int = 10,
    slow_period: int = 30,
    atr_period: int = 14,
    high_volatility_pct: float = 2.5,
    trend_threshold_pct: float = 0.35,
) -> RegimeAssessment:
    """Classify recent market conditions from chronological candles."""
    if fast_period < 2 or slow_period <= fast_period or atr_period < 2:
        raise ValueError("Periods must satisfy 2 <= fast_period < slow_period")
    if high_volatility_pct <= 0 or trend_threshold_pct <= 0:
        raise ValueError("Thresholds must be positive")
    data = tuple(candles)
    for candle in data:
        candle.validate()
    required = max(slow_period, atr_period + 1)
    if len(data) < required:
        return RegimeAssessment(
            Regime.INSUFFICIENT_DATA, 0.0, 0.0, 0.0,
            f"Need at least {required} valid candles",
        )

    closes = [c.close for c in data]
    true_ranges = []
    directional_moves = []
    for previous, current in zip(data, data[1:]):
        true_ranges.append(max(
            current.high - current.low,
            abs(current.high - previous.close),
            abs(current.low - previous.close),
        ))
        up = current.high - previous.high
        down = previous.low - current.low
        directional_moves.append(max(up, 0.0) if up > down else 0.0)

    atr = sum(true_ranges[-atr_period:]) / atr_period
    atr_pct = atr / closes[-1] * 100.0
    fast = _ema(closes[-fast_period:], fast_period)
    slow = _ema(closes[-slow_period:], slow_period)
    displacement_pct = abs(fast - slow) / slow * 100.0
    plus_dm = sum(directional_moves[-atr_period:])
    directional_strength = min(100.0, plus_dm / max(atr * atr_period, 1e-12) * 100.0)

    if atr_pct >= high_volatility_pct:
        regime = Regime.HIGH_VOLATILITY
        confidence = min(1.0, atr_pct / (high_volatility_pct * 2.0))
        reason = "ATR as a percentage of price exceeds the volatility threshold"
    elif displacement_pct >= trend_threshold_pct:
        regime = Regime.TRENDING_UP if fast > slow else Regime.TRENDING_DOWN
        confidence = min(1.0, displacement_pct / (trend_threshold_pct * 2.0))
        reason = "Fast and slow EMA separation indicates directional movement"
    else:
        regime = Regime.RANGE_BOUND
        confidence = max(0.0, 1.0 - displacement_pct / trend_threshold_pct)
        reason = "EMA separation remains below the trend threshold"

    return RegimeAssessment(
        regime, round(confidence, 4), round(atr_pct, 4),
        round(directional_strength, 4), reason,
    )
