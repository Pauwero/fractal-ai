"""Swing detection for the structure bounded context.

Ports the research_detect_swings SQL function to a pure Python function.
The SQL used LAG/LEAD window functions to examine each candle (C2) against
its left neighbour (C1) and right neighbour (C3). This module replicates
that logic exactly, including the dual-swing behaviour.
"""

from src.domain.structure.models import Candle, Swing, SwingType

# Pip value per pair — the smallest price increment that counts as one pip.
# Extend this dict as new pairs are added to the platform.
PIP_VALUES: dict[str, float] = {
    "EURUSD": 0.0001,
    "GBPUSD": 0.0001,
    "USDJPY": 0.01,
}


def detect_swings(
    candles: list[Candle],
    pair: str,
    timeframe: str,
    min_swing_pips: float | None = None,
) -> list[Swing]:
    """Detect swing highs and lows from a sequence of candles.

    Uses the C1-C2-C3 pattern mirroring the research_detect_swings SQL function:

    - Swing HIGH: c2.high > c1.high AND c2.high > c3.high (strict greater-than)
    - Swing LOW:  c2.low  < c1.low  AND c2.low  < c3.low  (strict less-than)

    Both checks are INDEPENDENT — a single candle can be both a swing HIGH and
    a swing LOW (dual swing). When both fire, HIGH is appended before LOW.

    The caller is responsible for providing buffer candles around their target
    date range (±3 days is recommended for daily/weekly boundaries). This
    function processes ALL candles it receives without any internal trimming.

    Args:
        candles: Sequence of candles sorted ascending by open_time.
            Must contain at least 3 candles.
        pair: Currency pair in uppercase format with no slash (e.g. "EURUSD").
        timeframe: Timeframe in uppercase with unit (e.g. "1H").
        min_swing_pips: Optional minimum candle range filter. When set, a swing
            is only included if the C2 candle range (high - low) converted to
            pips is >= this value. Requires the pair to be present in PIP_VALUES.
            Applies to both HIGH and LOW from the same C2. None = no filter.

    Returns:
        List of Swing objects in open_time ascending order. Dual swings
        (same open_time) appear with HIGH before LOW.

    Raises:
        ValueError: If fewer than 3 candles are provided.
        ValueError: If candles are not sorted strictly ascending by open_time
            (duplicate timestamps are also rejected).
        ValueError: If min_swing_pips is set for a pair not in PIP_VALUES.
    """
    if len(candles) < 3:
        raise ValueError(f"At least 3 candles required, got {len(candles)}")

    for i in range(1, len(candles)):
        if candles[i].open_time <= candles[i - 1].open_time:
            raise ValueError(
                "Candles must be sorted ascending by open_time with no duplicates. "
                f"Violation at index {i}: {candles[i].open_time} <= {candles[i - 1].open_time}"
            )

    pip_value: float | None = None
    if min_swing_pips is not None:
        if pair not in PIP_VALUES:
            raise ValueError(
                f"Unknown pair '{pair}' — pip value required for min_swing_pips filter. "
                f"Known pairs: {sorted(PIP_VALUES)}"
            )
        pip_value = PIP_VALUES[pair]

    swings: list[Swing] = []

    for i in range(1, len(candles) - 1):
        c1 = candles[i - 1]
        c2 = candles[i]
        c3 = candles[i + 1]

        # Apply optional min_swing_pips filter on the C2 candle range.
        # If C2 doesn't meet the threshold, skip both HIGH and LOW checks.
        if pip_value is not None:
            c2_range_pips = (c2.high - c2.low) / pip_value
            if c2_range_pips < min_swing_pips:  # type: ignore[operator]
                continue

        # HIGH check — independent of LOW check, strict greater-than on both sides.
        if c2.high > c1.high and c2.high > c3.high:
            swings.append(
                Swing(
                    pair=pair,
                    timeframe=timeframe,
                    open_time=c2.open_time,
                    type=SwingType.HIGH,
                    price=c2.high,
                )
            )

        # LOW check — independent of HIGH check, strict less-than on both sides.
        if c2.low < c1.low and c2.low < c3.low:
            swings.append(
                Swing(
                    pair=pair,
                    timeframe=timeframe,
                    open_time=c2.open_time,
                    type=SwingType.LOW,
                    price=c2.low,
                )
            )

    return swings
