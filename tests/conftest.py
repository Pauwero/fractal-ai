"""Shared test fixtures for Fractal AI test suite.

Fixtures defined here are available to all tests automatically.
"""

import pytest


@pytest.fixture
def eurusd_pair() -> str:
    """Standard EURUSD pair string."""
    return "EURUSD"


@pytest.fixture
def timeframe_1h() -> str:
    """Standard 1H timeframe string."""
    return "1H"


@pytest.fixture
def timeframe_5m() -> str:
    """Standard 5M timeframe string."""
    return "5M"
