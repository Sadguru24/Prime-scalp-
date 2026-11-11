#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prime Scalp adaptive market-regime classifier.

Classifies a validated close-price series and externally calculated ADX into
BULL_TREND, BEAR_TREND, SIDEWAYS, TRANSITION_TREND, or UNKNOWN. This module
only analyses supplied market data; it never creates data or places orders.
"""
from __future__ import annotations

import logging
import math
from collections.abc import Mapping, Sequence
from typing import Any

logger = logging.getLogger("prime_scalp.strategy.regime")
logger.addHandler(logging.NullHandler())


class MarketRegimeStrategy:
    """Classify market regime from the last 10/30 closes and a validated ADX."""

    def __init__(self, adx_trend_cutoff: float = 25.0) -> None:
        cutoff = self._finite_number(adx_trend_cutoff, "adx_trend_cutoff")
        if not 0.0 < cutoff <= 100.0:
            raise ValueError("adx_trend_cutoff must be in the interval (0, 100]")
        self.adx_trend_cutoff = cutoff

    @staticmethod
    def _finite_number(value: Any, field: str) -> float:
        """Convert a real numeric value while rejecting booleans and non-finite values."""
        if isinstance(value, bool):
            raise ValueError(f"{field} must be a finite real number")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{field} must be a finite real number") from exc
        if not math.isfinite(number):
            raise ValueError(f"{field} must be finite")
        return number

    def detect_regime(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        """Return regime metadata; malformed market inputs fail closed.

        The confidence value is a bounded ADX-derived heuristic score, not a
        statistically calibrated probability. Missing ADX is never treated
        as zero and cannot silently create a SIDEWAYS classification.
        """
        if not isinstance(snapshot, Mapping):
            raise TypeError("snapshot must be a mapping")
        if "closes" not in snapshot:
            raise ValueError("snapshot must include closes")
        if "adx" not in snapshot:
            raise ValueError("snapshot must include a validated adx value")

        raw_closes = snapshot["closes"]
        if isinstance(raw_closes, (str, bytes)) or not isinstance(raw_closes, Sequence):
            raise TypeError("closes must be a sequence of finite positive prices")

        if len(raw_closes) < 30:
            return {
                "regime": "UNKNOWN",
                "confidence": 0.0,
                "reason": "At least 30 closing prices are required",
            }

        closes = [
            self._finite_number(value, f"closes[{index}]")
            for index, value in enumerate(raw_closes)
        ]
        if any(value <= 0.0 for value in closes):
            raise ValueError("closing prices must be greater than zero")

        adx_val = self._finite_number(snapshot["adx"], "adx")
        if not 0.0 <= adx_val <= 100.0:
            raise ValueError("adx must be in the interval [0, 100]")

        current_close = closes[-1]
        ma_short = math.fsum(closes[-10:]) / 10.0
        ma_long = math.fsum(closes[-30:]) / 30.0

        if adx_val >= self.adx_trend_cutoff:
            if current_close > ma_long and ma_short > ma_long:
                regime = "BULL_TREND"
                confidence = adx_val
            elif current_close < ma_long and ma_short < ma_long:
                regime = "BEAR_TREND"
                confidence = adx_val
            else:
                regime = "TRANSITION_TREND"
                confidence = min(adx_val, 100.0 - adx_val)
        else:
            regime = "SIDEWAYS"
            confidence = 100.0 - adx_val

        payload = {
            "regime": regime,
            "adx": round(adx_val, 2),
            "confidence": round(max(0.0, min(100.0, confidence)), 2),
            "reason": (
                f"{regime}: ADX={adx_val:.2f}, "
                f"MA10={ma_short:.6f}, MA30={ma_long:.6f}"
            ),
        }
        logger.info("Market regime classified: %s", regime)
        return payload


# Backwards-compatible name used by earlier callers.
MarketRegimeDetector = MarketRegimeStrategy
