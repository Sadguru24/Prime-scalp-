"""Prime Scalp unified strategy suite.

Combines market-regime classification, swing-trend evaluation and protective
options-hedge selection in one module. Pure analysis only: no broker orders,
no synthetic market data and no execution side effects.
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


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class OptionRight(str, Enum):
    CALL = "CALL"
    PUT = "PUT"


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
            raise ValueError("Candle values must be finite")
        if min(values) < 0 or self.close <= 0:
            raise ValueError("Candle prices must be non-negative and close positive")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("Candle high is inconsistent")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("Candle low is inconsistent")


@dataclass(frozen=True)
class RegimeAssessment:
    regime: Regime
    confidence: float
    atr_pct: float
    directional_strength: float
    reason: str


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


@dataclass(frozen=True)
class OptionQuote:
    symbol: str
    right: OptionRight
    strike: float
    expiry_days: int
    bid: float
    ask: float
    delta: float
    open_interest: int
    volume: int
    lot_size: int

    def validate(self) -> None:
        if not self.symbol.strip():
            raise ValueError("Option symbol is required")
        if not all(isfinite(float(v)) for v in (self.strike, self.bid, self.ask, self.delta)):
            raise ValueError("Option quote values must be finite")
        if self.strike <= 0 or self.bid < 0 or self.ask < self.bid:
            raise ValueError("Invalid option strike or bid/ask")
        if self.expiry_days < 0 or not -1 <= self.delta <= 1:
            raise ValueError("Invalid expiry or delta")
        if min(self.open_interest, self.volume) < 0 or self.lot_size <= 0:
            raise ValueError("Invalid liquidity or lot size")


@dataclass(frozen=True)
class HedgeSelection:
    selected: bool
    symbol: str
    right: OptionRight | None
    strike: float
    premium_per_unit: float
    lot_size: int
    estimated_lot_cost: float
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
    rs = gains / losses
    return 100.0 - 100.0 / (1.0 + rs)


def classify_regime(
    candles: Sequence[Candle], *, fast_period: int = 10,
    slow_period: int = 30, atr_period: int = 14,
    high_volatility_pct: float = 2.5, trend_threshold_pct: float = 0.35,
) -> RegimeAssessment:
    """Classify chronological OHLCV candles using EMA separation and ATR."""
    if fast_period < 2 or slow_period <= fast_period or atr_period < 2:
        raise ValueError("Require 2 <= fast_period < slow_period and atr_period >= 2")
    if not all(isfinite(x) and x > 0 for x in (high_volatility_pct, trend_threshold_pct)):
        raise ValueError("Thresholds must be positive and finite")
    data = tuple(candles)
    for candle in data:
        candle.validate()
    required = max(slow_period, atr_period + 1)
    if len(data) < required:
        return RegimeAssessment(Regime.INSUFFICIENT_DATA, 0.0, 0.0, 0.0,
                                f"Need at least {required} candles")
    closes = [c.close for c in data]
    ranges = [
        max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close))
        for p, c in zip(data, data[1:])
    ]
    atr = sum(ranges[-atr_period:]) / atr_period
    atr_pct = atr / closes[-1] * 100
    fast = _ema(closes[-fast_period:], fast_period)
    slow = _ema(closes[-slow_period:], slow_period)
    separation = abs(fast - slow) / slow * 100
    positive_dm = sum(
        max(c.high - p.high, 0.0)
        if c.high - p.high > p.low - c.low else 0.0
        for p, c in zip(data, data[1:])
    )
    strength = min(100.0, positive_dm / max(atr * atr_period, 1e-12) * 100)
    if atr_pct >= high_volatility_pct:
        regime = Regime.HIGH_VOLATILITY
        confidence = min(1.0, atr_pct / (2 * high_volatility_pct))
        reason = "ATR percentage exceeds volatility threshold"
    elif separation >= trend_threshold_pct:
        regime = Regime.TRENDING_UP if fast > slow else Regime.TRENDING_DOWN
        confidence = min(1.0, separation / (2 * trend_threshold_pct))
        reason = "Fast/slow EMA separation indicates direction"
    else:
        regime = Regime.RANGE_BOUND
        confidence = max(0.0, 1 - separation / trend_threshold_pct)
        reason = "EMA separation is below trend threshold"
    return RegimeAssessment(regime, round(confidence, 4), round(atr_pct, 4),
                            round(strength, 4), reason)


def evaluate_swing(
    closes: Sequence[float], *, fast_period: int = 9, slow_period: int = 21,
    rsi_period: int = 14, minimum_score: float = 70.0,
    reward_risk: float = 2.0,
) -> SwingDecision:
    """Return BUY/SELL/HOLD based on EMA trend, RSI and price confirmation."""
    values = tuple(float(v) for v in closes)
    if not all(isfinite(v) and v > 0 for v in values):
        raise ValueError("Closes must be finite positive prices")
    if fast_period < 2 or slow_period <= fast_period or rsi_period < 2:
        raise ValueError("Invalid indicator periods")
    if not isfinite(minimum_score) or not 0 < minimum_score <= 100:
        raise ValueError("minimum_score must be in (0, 100]")
    if not isfinite(reward_risk) or reward_risk < 1:
        raise ValueError("reward_risk must be at least 1")
    required = max(slow_period, rsi_period + 1)
    if len(values) < required:
        return SwingDecision(Signal.HOLD, 0.0, 0.0, 0.0, 50.0, 0.0, 0.0,
                             f"Need at least {required} closing prices")
    fast, slow = _ema(values[-fast_period:], fast_period), _ema(values[-slow_period:], slow_period)
    rsi, latest = _rsi(values, rsi_period), values[-1]
    separation = abs(fast - slow) / slow * 100
    trend_score = min(45.0, separation * 25.0)
    momentum = 25.0 if ((fast > slow and 50 <= rsi <= 70) or
                        (fast < slow and 30 <= rsi <= 50)) else 0.0
    confirmation = 30.0 if ((fast > slow and latest > fast) or
                            (fast < slow and latest < fast)) else 0.0
    score = min(100.0, trend_score + momentum + confirmation)
    signal = Signal.BUY if fast > slow else Signal.SELL if fast < slow else Signal.HOLD
    if ((signal is Signal.BUY and not 50 <= rsi <= 70) or
        (signal is Signal.SELL and not 30 <= rsi <= 50) or score < minimum_score):
        signal = Signal.HOLD
    recent = values[-min(5, len(values)):]
    stop = max(max(recent) - min(recent), latest * 0.005)
    target = stop * reward_risk
    reason = "Trend, momentum and price confirmation aligned" if signal is not Signal.HOLD else "Entry filters not aligned"
    return SwingDecision(signal, round(score, 2), round(fast, 6), round(slow, 6),
                         round(rsi, 2), round(stop, 6), round(target, 6), reason)


def select_protective_hedge(
    position_side: PositionSide, option_chain: Sequence[OptionQuote], *,
    max_expiry_days: int = 45, min_open_interest: int = 100,
    min_volume: int = 10, max_spread_pct: float = 10.0,
    target_abs_delta: float = 0.30, max_lot_cost: float | None = None,
) -> HedgeSelection:
    """Select a liquid protective put for a long or call for a short position."""
    if min(max_expiry_days, min_open_interest, min_volume) < 0:
        raise ValueError("Expiry and liquidity limits cannot be negative")
    if not isfinite(max_spread_pct) or not 0 < max_spread_pct <= 100:
        raise ValueError("max_spread_pct must be in (0, 100]")
    if not isfinite(target_abs_delta) or not 0 < target_abs_delta <= 1:
        raise ValueError("target_abs_delta must be in (0, 1]")
    if max_lot_cost is not None and (not isfinite(max_lot_cost) or max_lot_cost <= 0):
        raise ValueError("max_lot_cost must be positive and finite")
    right = OptionRight.PUT if position_side is PositionSide.LONG else OptionRight.CALL
    candidates = []
    for quote in option_chain:
        quote.validate()
        if quote.right is not right or quote.expiry_days > max_expiry_days:
            continue
        if quote.open_interest < min_open_interest or quote.volume < min_volume:
            continue
        midpoint = (quote.bid + quote.ask) / 2
        if midpoint <= 0:
            continue
        spread = (quote.ask - quote.bid) / midpoint * 100
        cost = quote.ask * quote.lot_size
        if spread > max_spread_pct or (max_lot_cost is not None and cost > max_lot_cost):
            continue
        score = abs(abs(quote.delta) - target_abs_delta) + spread / 100 + quote.expiry_days / 10000
        candidates.append((score, quote, cost))
    if not candidates:
        return HedgeSelection(False, "", None, 0.0, 0.0, 0, 0.0,
                              "No option meets the configured eligibility filters")
    _, quote, cost = min(candidates, key=lambda item: (item[0], item[1].symbol))
    return HedgeSelection(True, quote.symbol, quote.right, quote.strike, quote.ask,
                          quote.lot_size, round(cost, 2),
                          "Best eligible protective hedge; validate contract and risk before execution")
