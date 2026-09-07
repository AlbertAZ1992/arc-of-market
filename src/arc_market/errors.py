"""Errors raised by the compact market-data pipeline."""


class MarketDataError(RuntimeError):
    """Base error for market-data collection, calculation, and publication."""


class MarketConfigError(MarketDataError):
    """The fail-closed market-data configuration is invalid."""


class MarketSourceError(MarketDataError):
    """A named upstream source could not provide valid data."""


class MarketQualityError(MarketDataError):
    """Collected data does not satisfy the publication quality gate."""
