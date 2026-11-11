#!/usr/bin/env python3
# File Path: indicators_engine.py

# ==========================================
# ||       श्री स्वामी समर्थ Start          ||
# ||       Sadguru Traders                 ||
# ||       Owner: Saurabh Rameshlal Solanki||
# ||       Project: Prime Scalp India      ||
# ==========================================

"""Validated technical-indicator engine for Prime Scalp India.

Provides deterministic OHLCV validation, Wilder indicators, KAMA, MACD,
Bollinger Bands, basic three-candle FVG detection and rolling support/resistance.
This module performs analysis only; it does not place or modify broker orders.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any
import logging
import math
import time
import uuid

logger = logging.getLogger("PrimeScalpIndicatorsEngine")
logger.addHandler(logging.NullHandler())

REQUIRED_FIELDS = (
    "tenant_id", "strategy_id", "signal_id", "symbol",
    "closes", "highs", "lows", "volumes", "timestamps",
    "bid", "ask", "timeframe_s",
)
MIN_HISTORY = 150


class ProductionDataError(ValueError):
    """Raised when input market data violates engine invariants."""


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ProductionDataError(f"invalid_numeric_value: {field}")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ProductionDataError(f"invalid_numeric_value: {field}") from exc
    if not math.isfinite(result):
        raise ProductionDataError(f"non_finite_value: {field}")
    return result


def _positive_period(period: int, name: str, minimum: int = 1) -> None:
    if isinstance(period, bool) or not isinstance(period, int) or period < minimum:
        raise ProductionDataError(f"{name}_must_be_integer_gte_{minimum}")


def validate_snapshot(
    snapshot: Mapping[str, Any], now_ms: int | None = None
) -> tuple[bool, str]:
    """Validate a market snapshot without mutating the caller's dictionary.

    Timestamps may be Unix seconds or milliseconds. They are normalized only
    for validation; the original snapshot is left unchanged.
    """
    if not isinstance(snapshot, Mapping):
        return False, "snapshot_must_be_mapping"
    for key in REQUIRED_FIELDS:
        if key not in snapshot:
            return False, f"missing_field: {key}"

    for key in ("tenant_id", "strategy_id", "signal_id", "symbol"):
        value = snapshot[key]
        if not isinstance(value, str) or not value.strip():
            return False, f"invalid_identifier: {key}"

    arrays: dict[str, Sequence[Any]] = {}
    for key in ("closes", "highs", "lows", "volumes", "timestamps"):
        value = snapshot[key]
        if not isinstance(value, (list, tuple)):
            return False, f"array_must_be_list_or_tuple: {key}"
        arrays[key] = value

    lengths = {len(values) for values in arrays.values()}
    if len(lengths) != 1:
        return False, "array_length_mismatch"
    count = len(snapshot["closes"])
    if count < MIN_HISTORY:
        return False, f"insufficient_history: <{MIN_HISTORY}"

    try:
        timeframe = _finite_number(snapshot["timeframe_s"], "timeframe_s")
        bid = _finite_number(snapshot["bid"], "bid")
        ask = _finite_number(snapshot["ask"], "ask")
        if timeframe <= 0:
            return False, "invalid_timeframe"
        if bid <= 0 or ask < bid:
            return False, "invalid_bid_ask"

        previous_ts: int | None = None
        normalized: list[int] = []
        for index, (close, high, low, volume, timestamp) in enumerate(zip(
            arrays["closes"], arrays["highs"], arrays["lows"],
            arrays["volumes"], arrays["timestamps"]
        )):
            c = _finite_number(close, f"closes[{index}]")
            h = _finite_number(high, f"highs[{index}]")
            low_value = _finite_number(low, f"lows[{index}]")
            vol = _finite_number(volume, f"volumes[{index}]")
            ts = _finite_number(timestamp, f"timestamps[{index}]")
            if c <= 0 or h <= 0 or low_value <= 0 or vol < 0:
                return False, f"invalid_ohlcv: {index}"
            if h < low_value or c < low_value or c > h:
                return False, f"ohlc_relationship_error: {index}"
            ts_ms = int(ts if ts >= 1e12 else ts * 1000)
            if ts_ms <= 0:
                return False, f"invalid_timestamp: {index}"
            if previous_ts is not None and ts_ms <= previous_ts:
                return False, f"timestamps_not_strictly_increasing: {index}"
            if now_ms is not None and ts_ms > now_ms:
                return False, f"future_timestamp: {index}"
            normalized.append(ts_ms)
            previous_ts = ts_ms
    except ProductionDataError as exc:
        return False, str(exc)

    return True, "passed"


def _validate_series(values: Sequence[float], name: str, minimum: int = 1) -> list[float]:
    if not isinstance(values, (list, tuple)) or len(values) < minimum:
        raise ProductionDataError(f"{name}_history_insufficient")
    result = [_finite_number(value, f"{name}[{i}]") for i, value in enumerate(values)]
    return result


def ema_series(values: Sequence[float], period: int) -> list[float]:
    """Compute an EMA seeded with the first observation."""
    _positive_period(period, "ema_period")
    data = _validate_series(values, "ema", period)
    alpha = 2.0 / (period + 1.0)
    output = [data[0]]
    for value in data[1:]:
        output.append(alpha * value + (1.0 - alpha) * output[-1])
    return output


def kama(
    closes: Sequence[float], period: int = 10, fast: int = 2, slow: int = 30
) -> float:
    """Compute Kaufman's Adaptive Moving Average using the latest window."""
    _positive_period(period, "kama_period")
    _positive_period(fast, "kama_fast")
    _positive_period(slow, "kama_slow")
    if fast >= slow:
        raise ProductionDataError("kama_fast_must_be_less_than_slow")
    data = _validate_series(closes, "kama", period + 1)
    fast_sc = 2.0 / (fast + 1.0)
    slow_sc = 2.0 / (slow + 1.0)

    # Seed with the first-period simple average, then update the efficiency
    # ratio and smoothing constant independently for every subsequent bar.
    value = sum(data[:period]) / period
    for index in range(period, len(data)):
        change = abs(data[index] - data[index - period])
        volatility = sum(
            abs(data[j] - data[j - 1])
            for j in range(index - period + 1, index + 1)
        )
        efficiency_ratio = change / volatility if volatility > 0 else 0.0
        smoothing = (efficiency_ratio * (fast_sc - slow_sc) + slow_sc) ** 2
        value += smoothing * (data[index] - value)
    return value


def rsi_series(closes: Sequence[float], period: int = 14) -> list[float]:
    """Compute Wilder RSI; flat markets return 50, not a false 100."""
    _positive_period(period, "rsi_period")
    data = _validate_series(closes, "rsi", period + 1)
    gains = [max(data[i] - data[i - 1], 0.0) for i in range(1, len(data))]
    losses = [max(data[i - 1] - data[i], 0.0) for i in range(1, len(data))]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    def value(gain: float, loss: float) -> float:
        if loss == 0:
            return 50.0 if gain == 0 else 100.0
        if gain == 0:
            return 0.0
        return 100.0 - 100.0 / (1.0 + gain / loss)

    output = [50.0] * period
    output.append(value(avg_gain, avg_loss))
    for index in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[index]) / period
        avg_loss = (avg_loss * (period - 1) + losses[index]) / period
        output.append(value(avg_gain, avg_loss))
    return output


def _validate_ohlc(
    highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], minimum: int
) -> tuple[list[float], list[float], list[float]]:
    h = _validate_series(highs, "highs", minimum)
    low = _validate_series(lows, "lows", minimum)
    c = _validate_series(closes, "closes", minimum)
    if not (len(h) == len(low) == len(c)):
        raise ProductionDataError("ohlc_array_length_mismatch")
    for i, (high, low_value, close) in enumerate(zip(h, low, c)):
        if low_value <= 0 or close <= 0 or high < low_value or not low_value <= close <= high:
            raise ProductionDataError(f"invalid_ohlc_relationship: {i}")
    return h, low, c


def _true_ranges(h: list[float], low: list[float], c: list[float]) -> list[float]:
    ranges = [h[0] - low[0]]
    for i in range(1, len(c)):
        ranges.append(max(h[i] - low[i], abs(h[i] - c[i - 1]), abs(low[i] - c[i - 1])))
    return ranges


def atr_series(
    highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int = 14
) -> list[float]:
    """Compute Wilder ATR with a simple-average seed."""
    _positive_period(period, "atr_period")
    h, low, c = _validate_ohlc(highs, lows, closes, period)
    tr = _true_ranges(h, low, c)
    current = sum(tr[:period]) / period
    output = [current] * period
    for value in tr[period:]:
        current = ((period - 1) * current + value) / period
        output.append(current)
    return output


def dmi_adx(
    highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int = 14
) -> tuple[float, float, float]:
    """Return latest (ADX, +DI, -DI) using Wilder smoothing.

    Returns neutral zero values when there is not enough history instead of
    fabricating an ADX/DI reading.
    """
    _positive_period(period, "adx_period")
    h, low, c = _validate_ohlc(highs, lows, closes, 2 * period)
    tr = _true_ranges(h, low, c)
    plus_dm = [0.0]
    minus_dm = [0.0]
    for i in range(1, len(c)):
        up = h[i] - h[i - 1]
        down = low[i - 1] - low[i]
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)

    sm_tr = sum(tr[1:period + 1])
    sm_plus = sum(plus_dm[1:period + 1])
    sm_minus = sum(minus_dm[1:period + 1])
    dx_values: list[float] = []

    def di_values() -> tuple[float, float]:
        if sm_tr <= 0:
            return 0.0, 0.0
        return sm_plus / sm_tr * 100.0, sm_minus / sm_tr * 100.0

    for i in range(period, len(c)):
        if i > period:
            sm_tr = sm_tr - sm_tr / period + tr[i]
            sm_plus = sm_plus - sm_plus / period + plus_dm[i]
            sm_minus = sm_minus - sm_minus / period + minus_dm[i]
        plus_di, minus_di = di_values()
        denominator = plus_di + minus_di
        dx_values.append(abs(plus_di - minus_di) / denominator * 100.0 if denominator else 0.0)

    if len(dx_values) < period:
        return 0.0, 0.0, 0.0
    adx = sum(dx_values[:period]) / period
    for dx in dx_values[period:]:
        adx = ((period - 1) * adx + dx) / period
    plus_di, minus_di = di_values()
    return adx, plus_di, minus_di


def bollinger(
    closes: Sequence[float], period: int = 20, deviations: float = 2.0
) -> tuple[float, float, float]:
    """Return (upper, lower, middle) Bollinger Bands using sample deviation."""
    _positive_period(period, "bollinger_period", 2)
    if not math.isfinite(float(deviations)) or deviations < 0:
        raise ProductionDataError("invalid_bollinger_deviations")
    data = _validate_series(closes, "bollinger", period)[-period:]
    mean = sum(data) / period
    variance = sum((value - mean) ** 2 for value in data) / (period - 1)
    standard_deviation = math.sqrt(variance)
    return mean + deviations * standard_deviation, mean - deviations * standard_deviation, mean


def macd(
    closes: Sequence[float], fast_period: int = 12, slow_period: int = 26,
    signal_period: int = 9
) -> tuple[float, float, float, float]:
    """Return MACD, signal, current histogram and previous histogram."""
    _positive_period(fast_period, "macd_fast")
    _positive_period(slow_period, "macd_slow")
    _positive_period(signal_period, "macd_signal")
    if fast_period >= slow_period:
        raise ProductionDataError("macd_fast_must_be_less_than_slow")
    data = _validate_series(closes, "macd", slow_period + signal_period)
    fast = ema_series(data, fast_period)
    slow = ema_series(data, slow_period)
    line = [a - b for a, b in zip(fast, slow)]
    signal = ema_series(line, signal_period)
    histogram = [a - b for a, b in zip(line, signal)]
    return line[-1], signal[-1], histogram[-1], histogram[-2]


def smc_fvg_and_blocks(
    highs: Sequence[float], lows: Sequence[float], closes: Sequence[float],
    lookback: int = 20
) -> tuple[bool, bool, float, float]:
    """Detect latest three-candle FVG and rolling horizontal extrema.

    The returned levels are simple lookback extrema, not institutionally
    confirmed order blocks or liquidity zones.
    """
    _positive_period(lookback, "smc_lookback", 3)
    h, low, c = _validate_ohlc(highs, lows, closes, lookback)
    bullish_fvg = low[-1] > h[-3]
    bearish_fvg = h[-1] < low[-3]
    return bullish_fvg, bearish_fvg, min(low[-lookback:]), max(h[-lookback:])


def generate_indicator_tag(symbol: str) -> str:
    """Generate a collision-resistant calculation correlation tag."""
    if not isinstance(symbol, str) or not symbol.strip():
        raise ProductionDataError("invalid_symbol")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"ST-IND-{stamp}-{uuid.uuid4().hex[:12]}-{symbol.strip()}"


def indicators(snapshot: Mapping[str, Any]) -> dict[str, float]:
    """Validate a snapshot and compute the complete indicator output bundle."""
    valid, reason = validate_snapshot(snapshot)
    if not valid:
        raise ProductionDataError(reason)

    closes = [_finite_number(x, "close") for x in snapshot["closes"]]
    highs = [_finite_number(x, "high") for x in snapshot["highs"]]
    lows = [_finite_number(x, "low") for x in snapshot["lows"]]
    volumes = [_finite_number(x, "volume") for x in snapshot["volumes"]]
    # Volume is validated even though no volume-derived indicator is exposed yet.
    if any(volume < 0 for volume in volumes):
        raise ProductionDataError("negative_volume")

    rsi_values = rsi_series(closes, 14)
    atr_values = atr_series(highs, lows, closes, 14)
    adx, plus_di, minus_di = dmi_adx(highs, lows, closes, 14)
    upper, lower, middle = bollinger(closes, 20, 2.0)
    macd_value, macd_signal, macd_hist, macd_hist_prev = macd(closes)
    bullish_fvg, bearish_fvg, support, resistance = smc_fvg_and_blocks(
        highs, lows, closes, 20
    )
    tag = generate_indicator_tag(str(snapshot["symbol"]))
    logger.info("Indicators computed for %s", tag)

    return {
        "rsi": rsi_values[-1],
        "rsi_prev": rsi_values[-2],
        "atr": atr_values[-1],
        "adx": adx,
        "plus_di": plus_di,
        "minus_di": minus_di,
        "kama": kama(closes, 10),
        "bb_upper": upper,
        "bb_lower": lower,
        "bb_mid": middle,
        "macd": macd_value,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "macd_hist_prev": macd_hist_prev,
        "bullish_fvg": float(bullish_fvg),
        "bearish_fvg": float(bearish_fvg),
        "horizontal_support": support,
        "horizontal_resistance": resistance,
        "ema9": ema_series(closes, 9)[-1],
        "ema20": ema_series(closes, 20)[-1],
    }


# ==========================================
# ||       श्री स्वामी समर्थ End            ||
# ||       Sadguru Traders                 ||
# ||       Owner: Saurabh Rameshlal Solanki||
# ||       Project: Prime Scalp India      ||
# ==========================================
