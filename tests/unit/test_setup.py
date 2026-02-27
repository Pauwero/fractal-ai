"""Smoke tests to verify project setup.

These tests confirm that the basic project structure, imports,
and configuration are working correctly.
"""


class TestProjectSetup:
    """Verify the project skeleton is correctly configured."""

    def test_python_version(self):
        """Python 3.11+ is required for modern type hints."""
        import sys

        assert sys.version_info >= (3, 11), "Python 3.11+ required"

    def test_src_package_importable(self):
        """The src package should be importable."""
        import src  # noqa: F401

    def test_domain_packages_importable(self):
        """All domain packages should be importable."""
        import src.domain.execution
        import src.domain.market_data
        import src.domain.observability
        import src.domain.research
        import src.domain.strategy
        import src.domain.structure  # noqa: F401

    def test_api_importable(self):
        """The FastAPI app should be importable."""
        from src.api.main import app

        assert app.title == "Fractal AI"

    def test_health_endpoint_exists(self):
        """The /health endpoint should be registered."""
        from src.api.main import app

        routes = [route.path for route in app.routes]
        assert "/health" in routes

    def test_conventions_pair_format(self, eurusd_pair):
        """Pairs must be uppercase, no slash."""
        assert eurusd_pair == "EURUSD"
        assert "/" not in eurusd_pair
        assert eurusd_pair == eurusd_pair.upper()

    def test_conventions_timeframe_format(self, timeframe_1h, timeframe_5m):
        """Timeframes must be uppercase with unit."""
        assert timeframe_1h == "1H"
        assert timeframe_5m == "5M"
