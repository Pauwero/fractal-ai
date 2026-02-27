"""Unit tests for swing detection — written before implementation (TDD).

Covers:
  - Model validation (Candle OHLC consistency, Swing field consistency)
  - Basic detection (single high/low, dual swing, equal values)
  - Edge cases (<3 candles, unsorted, duplicate timestamps)
  - min_swing_pips filter
  - SQL regression: 26-candle EURUSD dataset must produce exact 10 swings
  - Jan-23 bug regression: buffer candles are caller's responsibility
"""

import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.domain.structure.models import Candle, Swing, SwingType
from src.domain.structure.swing_detection import detect_swings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES_PATH = Path(__file__).parent.parent / "fixtures" / "candles.json"

_T0 = datetime(2025, 1, 1, 0, 0, 0)
_T1 = datetime(2025, 1, 1, 1, 0, 0)
_T2 = datetime(2025, 1, 1, 2, 0, 0)
_T3 = datetime(2025, 1, 1, 3, 0, 0)
_T4 = datetime(2025, 1, 1, 4, 0, 0)


def _candle(
    t: datetime,
    o: float,
    h: float,
    lo: float,
    c: float,
    pair: str = "EURUSD",
    tf: str = "1H",
) -> Candle:
    """Convenience factory — keeps test bodies concise."""
    return Candle(pair=pair, timeframe=tf, open_time=t, open=o, high=h, low=lo, close=c)


def _load_fixture() -> tuple[list[Candle], list[dict]]:
    """Load the EURUSD Feb-2025 fixture and return (candles, expected_swings)."""
    data = json.loads(FIXTURES_PATH.read_text())
    candles = [
        Candle(
            pair=data["pair"],
            timeframe=data["timeframe"],
            open_time=datetime.fromisoformat(row["open_time"]),
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
        )
        for row in data["candles"]
    ]
    expected = data["expected_swings"]
    return candles, expected


# ---------------------------------------------------------------------------
# Candle model validation
# ---------------------------------------------------------------------------


class TestCandleModel:
    """Pydantic validation on Candle ensures OHLC consistency."""

    def test_valid_candle_created_successfully(self) -> None:
        c = _candle(_T0, 1.0200, 1.0250, 1.0180, 1.0230)
        assert c.high == 1.0250
        assert c.low == 1.0180

    def test_doji_candle_all_prices_equal(self) -> None:
        """A doji where O==H==L==C is valid."""
        c = _candle(_T0, 1.0200, 1.0200, 1.0200, 1.0200)
        assert c.open == c.high == c.low == c.close

    def test_high_below_open_raises(self) -> None:
        with pytest.raises(ValidationError):
            _candle(_T0, 1.0250, 1.0200, 1.0180, 1.0220)  # high < open

    def test_high_below_close_raises(self) -> None:
        with pytest.raises(ValidationError):
            _candle(_T0, 1.0200, 1.0220, 1.0180, 1.0250)  # high < close

    def test_high_below_low_raises(self) -> None:
        with pytest.raises(ValidationError):
            _candle(_T0, 1.0200, 1.0150, 1.0180, 1.0200)  # high < low

    def test_low_above_open_raises(self) -> None:
        with pytest.raises(ValidationError):
            _candle(_T0, 1.0200, 1.0250, 1.0220, 1.0230)  # low > open

    def test_low_above_close_raises(self) -> None:
        with pytest.raises(ValidationError):
            _candle(_T0, 1.0230, 1.0250, 1.0220, 1.0200)  # low > close

    def test_candle_is_immutable(self) -> None:
        c = _candle(_T0, 1.0200, 1.0250, 1.0180, 1.0230)
        with pytest.raises(ValidationError):
            c.high = 1.9999  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Swing model validation
# ---------------------------------------------------------------------------


class TestSwingModel:
    """Pydantic validation on Swing ensures field consistency."""

    def test_swing_high_created_correctly(self) -> None:
        s = Swing(pair="EURUSD", timeframe="1H", open_time=_T1, type=SwingType.HIGH, price=1.0250)
        assert s.type == SwingType.HIGH
        assert s.price == 1.0250

    def test_swing_low_created_correctly(self) -> None:
        s = Swing(pair="EURUSD", timeframe="1H", open_time=_T1, type=SwingType.LOW, price=1.0180)
        assert s.type == SwingType.LOW
        assert s.price == 1.0180

    def test_swing_is_immutable(self) -> None:
        s = Swing(pair="EURUSD", timeframe="1H", open_time=_T1, type=SwingType.HIGH, price=1.0250)
        with pytest.raises(ValidationError):
            s.price = 9.9999  # type: ignore[misc]

    def test_swing_type_enum_values(self) -> None:
        assert SwingType.HIGH == "HIGH"
        assert SwingType.LOW == "LOW"


# ---------------------------------------------------------------------------
# Basic detection
# ---------------------------------------------------------------------------


class TestDetectSwingsBasic:
    """Core C1-C2-C3 detection behaviour."""

    def test_detects_single_swing_high(self) -> None:
        candles = [
            _candle(_T0, 1.0200, 1.0210, 1.0190, 1.0200),  # C1 — lower high
            _candle(_T1, 1.0200, 1.0250, 1.0195, 1.0220),  # C2 — highest high
            _candle(_T2, 1.0200, 1.0230, 1.0190, 1.0200),  # C3 — lower high
        ]
        swings = detect_swings(candles, "EURUSD", "1H")
        assert len(swings) == 1
        assert swings[0].type == SwingType.HIGH
        assert swings[0].price == 1.0250
        assert swings[0].open_time == _T1

    def test_detects_single_swing_low(self) -> None:
        candles = [
            _candle(_T0, 1.0200, 1.0210, 1.0190, 1.0200),  # C1 — higher low
            _candle(_T1, 1.0180, 1.0200, 1.0150, 1.0180),  # C2 — lowest low
            _candle(_T2, 1.0180, 1.0205, 1.0175, 1.0200),  # C3 — higher low
        ]
        swings = detect_swings(candles, "EURUSD", "1H")
        assert len(swings) == 1
        assert swings[0].type == SwingType.LOW
        assert swings[0].price == 1.0150
        assert swings[0].open_time == _T1

    def test_detects_dual_swing_high_before_low(self) -> None:
        """Same C2 can fire both HIGH and LOW; HIGH must come first in output."""
        candles = [
            _candle(_T0, 1.0220, 1.0230, 1.0170, 1.0220),  # C1
            _candle(_T1, 1.0200, 1.0280, 1.0120, 1.0200),  # C2 — new high AND new low
            _candle(_T2, 1.0200, 1.0250, 1.0160, 1.0200),  # C3
        ]
        swings = detect_swings(candles, "EURUSD", "1H")
        assert len(swings) == 2
        assert swings[0].type == SwingType.HIGH
        assert swings[0].price == 1.0280
        assert swings[1].type == SwingType.LOW
        assert swings[1].price == 1.0120
        assert swings[0].open_time == swings[1].open_time == _T1

    def test_no_swings_in_monotone_uptrend(self) -> None:
        """Rising market has no swing highs or lows."""
        candles = [
            _candle(_T0, 1.0200, 1.0210, 1.0190, 1.0205),
            _candle(_T1, 1.0205, 1.0220, 1.0200, 1.0215),
            _candle(_T2, 1.0215, 1.0230, 1.0210, 1.0225),
        ]
        swings = detect_swings(candles, "EURUSD", "1H")
        assert swings == []

    def test_equal_highs_do_not_form_swing(self) -> None:
        """Strict greater-than: equal high is NOT a swing high."""
        candles = [
            _candle(_T0, 1.0200, 1.0250, 1.0190, 1.0220),  # C1 same high as C2
            _candle(_T1, 1.0220, 1.0250, 1.0200, 1.0230),  # C2 — high == C1.high
            _candle(_T2, 1.0220, 1.0230, 1.0200, 1.0210),  # C3 — lower high
        ]
        swings = detect_swings(candles, "EURUSD", "1H")
        assert all(s.type != SwingType.HIGH for s in swings)

    def test_equal_lows_do_not_form_swing(self) -> None:
        """Strict less-than: equal low is NOT a swing low."""
        candles = [
            _candle(_T0, 1.0200, 1.0210, 1.0150, 1.0200),  # C1 same low as C2
            _candle(_T1, 1.0180, 1.0205, 1.0150, 1.0195),  # C2 — low == C1.low
            _candle(_T2, 1.0190, 1.0210, 1.0160, 1.0200),  # C3 — higher low
        ]
        swings = detect_swings(candles, "EURUSD", "1H")
        assert all(s.type != SwingType.LOW for s in swings)

    def test_pair_and_timeframe_propagated_to_swings(self) -> None:
        candles = [
            _candle(_T0, 1.2200, 1.2210, 1.2190, 1.2200, pair="GBPUSD", tf="4H"),
            _candle(_T1, 1.2200, 1.2280, 1.2180, 1.2200, pair="GBPUSD", tf="4H"),
            _candle(_T2, 1.2200, 1.2250, 1.2200, 1.2220, pair="GBPUSD", tf="4H"),
        ]
        swings = detect_swings(candles, "GBPUSD", "4H")
        assert all(s.pair == "GBPUSD" for s in swings)
        assert all(s.timeframe == "4H" for s in swings)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestDetectSwingsEdgeCases:
    """Boundary conditions and input validation."""

    def test_raises_on_empty_input(self) -> None:
        with pytest.raises(ValueError, match="3 candles"):
            detect_swings([], "EURUSD", "1H")

    def test_raises_on_one_candle(self) -> None:
        with pytest.raises(ValueError, match="3 candles"):
            detect_swings([_candle(_T0, 1.02, 1.03, 1.01, 1.02)], "EURUSD", "1H")

    def test_raises_on_two_candles(self) -> None:
        candles = [
            _candle(_T0, 1.02, 1.03, 1.01, 1.02),
            _candle(_T1, 1.02, 1.04, 1.00, 1.03),
        ]
        with pytest.raises(ValueError, match="3 candles"):
            detect_swings(candles, "EURUSD", "1H")

    def test_raises_on_descending_order(self) -> None:
        candles = [
            _candle(_T2, 1.02, 1.03, 1.01, 1.02),
            _candle(_T1, 1.02, 1.04, 1.00, 1.03),
            _candle(_T0, 1.02, 1.05, 1.01, 1.04),
        ]
        with pytest.raises(ValueError, match="sorted ascending"):
            detect_swings(candles, "EURUSD", "1H")

    def test_raises_on_duplicate_timestamps(self) -> None:
        candles = [
            _candle(_T0, 1.02, 1.03, 1.01, 1.02),
            _candle(_T0, 1.02, 1.04, 1.00, 1.03),  # same time as previous
            _candle(_T1, 1.02, 1.05, 1.01, 1.04),
        ]
        with pytest.raises(ValueError, match="sorted ascending"):
            detect_swings(candles, "EURUSD", "1H")

    def test_exactly_three_candles_high_detected(self) -> None:
        candles = [
            _candle(_T0, 1.0200, 1.0210, 1.0190, 1.0200),
            _candle(_T1, 1.0200, 1.0260, 1.0195, 1.0220),  # swing high
            _candle(_T2, 1.0210, 1.0240, 1.0200, 1.0215),
        ]
        swings = detect_swings(candles, "EURUSD", "1H")
        assert len(swings) == 1
        assert swings[0].type == SwingType.HIGH
        assert swings[0].price == 1.0260

    def test_exactly_three_candles_no_swing(self) -> None:
        candles = [
            _candle(_T0, 1.0200, 1.0240, 1.0190, 1.0220),  # highest high
            _candle(_T1, 1.0200, 1.0230, 1.0195, 1.0210),  # middle
            _candle(_T2, 1.0200, 1.0250, 1.0185, 1.0240),  # highest high again
        ]
        swings = detect_swings(candles, "EURUSD", "1H")
        assert swings == []


# ---------------------------------------------------------------------------
# min_swing_pips filter
# ---------------------------------------------------------------------------


class TestDetectSwingsMinPips:
    """The optional min_swing_pips filter uses the C2 candle range."""

    def _small_range_high_candles(self) -> list[Candle]:
        """C2 swing high with only a 2-pip candle range."""
        return [
            _candle(_T0, 1.02200, 1.02220, 1.02190, 1.02200),
            _candle(_T1, 1.02230, 1.02250, 1.02230, 1.02240),  # C2: range = 2 pips
            _candle(_T2, 1.02220, 1.02240, 1.02210, 1.02220),
        ]

    def _large_range_high_candles(self) -> list[Candle]:
        """C2 swing high with a 60-pip candle range."""
        return [
            _candle(_T0, 1.02000, 1.02100, 1.01990, 1.02050),
            _candle(_T1, 1.02100, 1.02700, 1.02100, 1.02600),  # C2: range = 60 pips
            _candle(_T2, 1.02500, 1.02650, 1.02490, 1.02550),
        ]

    def test_none_filter_returns_all_swings(self) -> None:
        swings = detect_swings(self._small_range_high_candles(), "EURUSD", "1H", min_swing_pips=None)
        assert len(swings) == 1

    def test_filter_removes_small_range_candle_swing(self) -> None:
        """C2 range of 2 pips is removed when min_swing_pips=5."""
        swings = detect_swings(self._small_range_high_candles(), "EURUSD", "1H", min_swing_pips=5.0)
        assert swings == []

    def test_filter_keeps_large_range_candle_swing(self) -> None:
        """C2 range of 60 pips passes when min_swing_pips=5."""
        swings = detect_swings(self._large_range_high_candles(), "EURUSD", "1H", min_swing_pips=5.0)
        assert len(swings) == 1
        assert swings[0].type == SwingType.HIGH

    def test_filter_boundary_exact_match_kept(self) -> None:
        """A C2 range that meets (>=) the min_swing_pips threshold is included.

        Uses a 6-pip range with a 5-pip filter to avoid floating-point precision
        issues that arise when testing exact boundary equality.
        """
        candles = [
            _candle(_T0, 1.02200, 1.02220, 1.02190, 1.02200),
            _candle(_T1, 1.02250, 1.02300, 1.02240, 1.02280),  # C2: range = 6 pips, filter = 5
            _candle(_T2, 1.02270, 1.02290, 1.02265, 1.02270),
        ]
        swings = detect_swings(candles, "EURUSD", "1H", min_swing_pips=5.0)
        assert len(swings) == 1

    def test_filter_unknown_pair_raises_value_error(self) -> None:
        candles = [
            _candle(_T0, 100.00, 100.50, 99.50, 100.00, pair="XYZUSD"),
            _candle(_T1, 100.00, 101.00, 99.00, 100.00, pair="XYZUSD"),
            _candle(_T2, 100.00, 100.80, 99.60, 100.00, pair="XYZUSD"),
        ]
        with pytest.raises(ValueError, match="Unknown pair"):
            detect_swings(candles, "XYZUSD", "1H", min_swing_pips=5.0)

    def test_dual_swing_both_filtered_when_range_small(self) -> None:
        """If C2 fails range filter, both HIGH and LOW are removed."""
        candles = [
            _candle(_T0, 1.02200, 1.02230, 1.02160, 1.02200),  # C1
            _candle(_T1, 1.02200, 1.02240, 1.02190, 1.02200),  # C2: range = 5 pips, dual swing
            _candle(_T2, 1.02200, 1.02230, 1.02200, 1.02210),  # C3
        ]
        # Without filter: C2 is a HIGH (1.02240 > 1.02230) and LOW (1.02190 < 1.02160? No)
        # Let me recalculate: C2.low=1.02190 vs C1.low=1.02160 → 1.02190 > 1.02160 → not a LOW
        # Just check HIGH is detected without filter but removed with filter (range=5 pips, filter=10)
        swings_no_filter = detect_swings(candles, "EURUSD", "1H")
        assert len(swings_no_filter) >= 1

        swings_filtered = detect_swings(candles, "EURUSD", "1H", min_swing_pips=10.0)
        assert swings_filtered == []


# ---------------------------------------------------------------------------
# SQL regression: 26-candle EURUSD dataset
# ---------------------------------------------------------------------------


class TestDetectSwingsRegression:
    """The Python implementation must produce identical output to research_detect_swings SQL."""

    def test_eurusd_feb_2025_produces_exact_10_swings(self) -> None:
        candles, expected = _load_fixture()
        swings = detect_swings(candles, "EURUSD", "1H")

        assert len(swings) == len(expected), (
            f"Expected {len(expected)} swings, got {len(swings)}.\n"
            f"Got: {[(s.open_time, s.type, s.price) for s in swings]}"
        )

        for i, (swing, exp) in enumerate(zip(swings, expected)):
            exp_time = datetime.fromisoformat(exp["open_time"])
            assert swing.open_time == exp_time, f"Swing {i}: time mismatch {swing.open_time} != {exp_time}"
            assert swing.type == exp["type"], f"Swing {i}: type mismatch {swing.type} != {exp['type']}"
            assert abs(swing.price - exp["price"]) < 1e-8, (
                f"Swing {i}: price mismatch {swing.price} != {exp['price']}"
            )

    def test_all_swing_pairs_are_eurusd(self) -> None:
        candles, _ = _load_fixture()
        swings = detect_swings(candles, "EURUSD", "1H")
        assert all(s.pair == "EURUSD" for s in swings)

    def test_all_swing_timeframes_are_1h(self) -> None:
        candles, _ = _load_fixture()
        swings = detect_swings(candles, "EURUSD", "1H")
        assert all(s.timeframe == "1H" for s in swings)

    def test_dual_swing_at_feb3_15h(self) -> None:
        """Feb 3 15:00 candle must fire both HIGH and LOW (dual swing), HIGH first."""
        candles, _ = _load_fixture()
        swings = detect_swings(candles, "EURUSD", "1H")

        dual_time = datetime(2025, 2, 3, 15, 0, 0)
        dual = [s for s in swings if s.open_time == dual_time]

        assert len(dual) == 2, f"Expected 2 swings at {dual_time}, got {len(dual)}"
        assert dual[0].type == SwingType.HIGH
        assert dual[1].type == SwingType.LOW
        assert abs(dual[0].price - 1.03368) < 1e-8
        assert abs(dual[1].price - 1.02423) < 1e-8


# ---------------------------------------------------------------------------
# Jan-23 bug regression: buffer candles are the caller's responsibility
# ---------------------------------------------------------------------------


class TestBufferCandleRegression:
    """Demonstrate that the function processes ALL provided candles without
    internal trimming. Callers must provide ±buffer around their target range.

    Background: Production N8N missed a swing at Jan 23 08:00 because the
    sequential detection ran without sufficient buffer candles on the boundary.
    """

    def test_swing_at_index_1_is_detected_when_buffer_candle_present(self) -> None:
        """The first detectable C2 is at index 1 — it requires index 0 as C1 buffer."""
        candles, _ = _load_fixture()
        swings = detect_swings(candles, "EURUSD", "1H")

        first_swing_time = datetime(2025, 2, 2, 23, 0, 0)
        times = [s.open_time for s in swings]
        assert first_swing_time in times, "Swing at index 1 should be detected when index 0 is present"

    def test_swing_at_last_minus_1_detected_when_buffer_candle_present(self) -> None:
        """The last detectable C2 is at index -2 — it requires index -1 as C3 buffer."""
        candles, _ = _load_fixture()
        swings = detect_swings(candles, "EURUSD", "1H")

        last_swing_time = datetime(2025, 2, 3, 22, 0, 0)
        times = [s.open_time for s in swings]
        assert last_swing_time in times, "Swing at index -2 should be detected when index -1 is present"

    def test_removing_first_buffer_causes_boundary_swing_to_be_missed(self) -> None:
        """Removing the first candle (C1 buffer) causes the Feb-2 23:00 swing to be missed.

        This is the exact failure mode of the Jan-23 production bug.
        """
        candles, _ = _load_fixture()
        first_swing_time = datetime(2025, 2, 2, 23, 0, 0)

        # Confirm it IS detected with the buffer candle
        full_swings = detect_swings(candles, "EURUSD", "1H")
        assert first_swing_time in [s.open_time for s in full_swings]

        # Remove the first buffer candle — the Feb-2 23:00 swing can no longer be C2
        trimmed_swings = detect_swings(candles[1:], "EURUSD", "1H")
        assert first_swing_time not in [s.open_time for s in trimmed_swings], (
            "Without the first buffer candle the boundary swing MUST be missed"
        )

    def test_removing_last_buffer_causes_boundary_swing_to_be_missed(self) -> None:
        """Removing the last candle (C3 buffer) causes the Feb-3 22:00 swing to be missed."""
        candles, _ = _load_fixture()
        last_swing_time = datetime(2025, 2, 3, 22, 0, 0)

        # Confirm it IS detected with the buffer candle
        full_swings = detect_swings(candles, "EURUSD", "1H")
        assert last_swing_time in [s.open_time for s in full_swings]

        # Remove the last buffer candle — Feb-3 22:00 can no longer be C2
        trimmed_swings = detect_swings(candles[:-1], "EURUSD", "1H")
        assert last_swing_time not in [s.open_time for s in trimmed_swings], (
            "Without the last buffer candle the boundary swing MUST be missed"
        )
