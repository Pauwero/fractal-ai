"""Domain models for the structure bounded context.

Defines the core value objects used by swing detection, level tracking,
and CISD pattern logic.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, model_validator


class SwingType(StrEnum):
    """Valid swing direction types.

    A swing HIGH is a candle whose high is strictly greater than both its
    left and right neighbours. A swing LOW is the mirror — lowest low.
    """

    HIGH = "HIGH"
    LOW = "LOW"


class Candle(BaseModel, frozen=True):
    """An immutable OHLC candle for a given pair and timeframe.

    All price fields are in the quote currency (e.g. USD for EURUSD).
    Times are UTC.

    Attributes:
        pair: Currency pair in uppercase format with no slash (e.g. "EURUSD").
        timeframe: Timeframe in uppercase with unit (e.g. "1H", "5M").
        open_time: UTC open time of the candle.
        open: Opening price.
        high: Highest traded price — must be >= open, close, and low.
        low: Lowest traded price — must be <= open, close, and high.
        close: Closing price.
    """

    pair: str
    timeframe: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float

    @model_validator(mode="after")
    def validate_ohlc_consistency(self) -> "Candle":
        """Ensure high is the maximum and low is the minimum of the OHLC bar."""
        if self.high < self.open:
            raise ValueError(f"high ({self.high}) must be >= open ({self.open})")
        if self.high < self.close:
            raise ValueError(f"high ({self.high}) must be >= close ({self.close})")
        if self.high < self.low:
            raise ValueError(f"high ({self.high}) must be >= low ({self.low})")
        if self.low > self.open:
            raise ValueError(f"low ({self.low}) must be <= open ({self.open})")
        if self.low > self.close:
            raise ValueError(f"low ({self.low}) must be <= close ({self.close})")
        return self


class Swing(BaseModel, frozen=True):
    """An immutable swing point detected in market structure.

    A swing is the C2 candle in a C1-C2-C3 triplet where C2's high (or low)
    is strictly greater than (or less than) both neighbours.

    Attributes:
        pair: Currency pair in uppercase format with no slash (e.g. "EURUSD").
        timeframe: Timeframe in uppercase with unit (e.g. "1H").
        open_time: UTC open time of the C2 candle that formed the swing.
        type: Swing direction — HIGH or LOW.
        price: The swing price — C2.high for HIGHs, C2.low for LOWs.
    """

    pair: str
    timeframe: str
    open_time: datetime
    type: SwingType
    price: float
