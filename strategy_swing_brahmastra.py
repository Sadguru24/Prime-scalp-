"""Prime Scalp swing-trend strategy.

Signals are analytical outputs only; broker execution belongs to the execution layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Sequence


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class SwingDecision:
    signal: Signal
    score: float
    fast_ema: float
    slow_ema: float
    rsi: float
    stop_distance: float
    target_distance: float
    reason: str


def _ema(values: Sequence[float], period: int) -> float:
    alpha = 2.0 / (period + 1.0)
    result = float(values[0])
    for value in values[1:]:
        result = alpha * float(value) + (1.0 - alpha) * result
    return result


def _rsi(values: Sequence[float], period: int) -> float:
    changes = [b - a for a, b in zip(values[-period - 1:], values[-period:])]
    gains = sum(max(change, 0.0) for change in changes) / period
    losses = sum(max(-change, 0.0) for change in changes) / period
    if losses == 0:
        return 100.0 if gains > 0 else 50.0
    relative_strength = gains / losses
    return 100.0 - 100.0 / (1.0 + relative_strength)


def evaluate_swing(
    closes: Sequence[float],
    *,
    fast_period: int = 9,
    slow_period: int = 21,
    rsi_period: int = 14,
    minimum_score: float = 70.0,
    reward_risk: float = 2.0,
) -> SwingDecision:
    """Evaluate a swing setup using chronological closing prices."""
    values = tuple(float(value) for value in closes)
    if not all(isfinite(value) and value > 0 for value in values):
        raise ValueError("Closing prices must be finite and positive")
    if fast_period < 2 or slow_period <= fast_period or rsi_period < 2:
        raise ValueError("Invalid indicator periods")
    if not 0 < minimum_score <= 100 or reward_risk < 1:
        raise ValueError("Invalid score or reward/risk configuration")
    required = max(slow_period, rsi_period + 1)
    if len(values) < required:
        return SwingDecision(
            Signal.HOLD, 0.0, 0.0, 0.0, 50.0, 0.0, 0.0,
            f"Insufficient history: need {required} closes",
        )

    fast = _ema(values[-fast_period:], fast_period)
    slow = _ema(values[-slow_period:], slow_period)
    rsi = _rsi(values, rsi_period)
    latest = values[-1]
    spread_pct = abs(fast - slow) / slow * 100.0
    trend_score = min(45.0, spread_pct * 25.0)
    momentum_score = 25.0 if (
        (fast > slow and 50.0 <= rsi <= 70.0)
        or (fast < slow and 30.0 <= rsi <= 50.0)
    ) else 0.0
    confirmation_score = 30.0 if (
        (fast > slow and latest > fast)
        or (fast < slow and latest < fast)
    ) else 0.0
    score = min(100.0, trend_score + momentum_score + confirmation_score)

    direction = Signal.BUY if fast > slow else Signal.SELL if fast < slow else Signal.HOLD
    if direction is Signal.BUY and not 50.0 <= rsi <= 70.0:
        direction = Signal.HOLD
    if direction is Signal.SELL and not 30.0 <= rsi <= 50.0:
        direction = Signal.HOLD
    if score < minimum_score:
        direction = Signal.HOLD

    # Volatility must be supplied by the risk layer; this price-based proxy is
    # deliberately conservative and is not a substitute for ATR sizing.
    recent_range = max(values[-min(5, len(values)):]) - min(values[-min(5, len(values)):])
    stop_distance = max(recent_range, latest * 0.005)
    target_distance = stop_distance * reward_risk
    reason = (
        "Trend, momentum and price confirmation aligned"
        if direction is not Signal.HOLD
        else "Swing entry filters are not fully aligned"
    )
    return SwingDecision(
        direction, round(score, 2), round(fast, 6), round(slow, 6),
        round(rsi, 2), round(stop_distance, 6), round(target_distance, 6), reason,
    )
