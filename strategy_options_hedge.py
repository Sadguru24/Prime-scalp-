"""Prime Scalp protective-options hedge selector.

Requires a real, validated option-chain snapshot from the market-data adapter.
It returns a hedge candidate and never submits orders.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Sequence


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class OptionRight(str, Enum):
    CALL = "CALL"
    PUT = "PUT"


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
        numeric = (self.strike, self.bid, self.ask, self.delta)
        if not all(isfinite(float(value)) for value in numeric):
            raise ValueError("Option quote contains non-finite values")
        if not self.symbol.strip() or self.strike <= 0:
            raise ValueError("Option symbol and positive strike are required")
        if self.expiry_days < 0 or self.bid < 0 or self.ask < self.bid:
            raise ValueError("Invalid expiry or bid/ask market")
        if not -1.0 <= self.delta <= 1.0:
            raise ValueError("Option delta must be between -1 and 1")
        if self.open_interest < 0 or self.volume < 0 or self.lot_size <= 0:
            raise ValueError("Invalid option liquidity or lot size")


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


def select_protective_hedge(
    position_side: PositionSide,
    option_chain: Sequence[OptionQuote],
    *,
    max_expiry_days: int = 45,
    min_open_interest: int = 100,
    min_volume: int = 10,
    max_spread_pct: float = 10.0,
    target_abs_delta: float = 0.30,
    max_lot_cost: float | None = None,
) -> HedgeSelection:
    """Choose a liquid protective put for longs or call for shorts."""
    if max_expiry_days < 0 or min_open_interest < 0 or min_volume < 0:
        raise ValueError("Invalid expiry/liquidity constraints")
    if not 0 < max_spread_pct <= 100 or not 0 < target_abs_delta <= 1:
        raise ValueError("Invalid spread or delta constraint")
    if max_lot_cost is not None and (
        not isfinite(max_lot_cost) or max_lot_cost <= 0
    ):
        raise ValueError("max_lot_cost must be positive and finite")

    required_right = OptionRight.PUT if position_side is PositionSide.LONG else OptionRight.CALL
    candidates: list[tuple[float, OptionQuote, float]] = []
    for quote in option_chain:
        quote.validate()
        if quote.right is not required_right:
            continue
        if quote.expiry_days > max_expiry_days:
            continue
        if quote.open_interest < min_open_interest or quote.volume < min_volume:
            continue
        midpoint = (quote.bid + quote.ask) / 2.0
        if midpoint <= 0:
            continue
        spread_pct = (quote.ask - quote.bid) / midpoint * 100.0
        if spread_pct > max_spread_pct:
            continue
        lot_cost = quote.ask * quote.lot_size
        if max_lot_cost is not None and lot_cost > max_lot_cost:
            continue
        delta_distance = abs(abs(quote.delta) - target_abs_delta)
        score = delta_distance + spread_pct / 100.0 + quote.expiry_days / 10000.0
        candidates.append((score, quote, lot_cost))

    if not candidates:
        return HedgeSelection(
            False, "", None, 0.0, 0.0, 0, 0.0,
            "No option satisfies the supplied liquidity, spread, expiry and cost filters",
        )
    _, selected, lot_cost = min(candidates, key=lambda item: (item[0], item[1].symbol))
    return HedgeSelection(
        True, selected.symbol, selected.right, selected.strike,
        selected.ask, selected.lot_size, round(lot_cost, 2),
        "Lowest-scoring eligible protective option; verify contract and risk before execution",
    )
