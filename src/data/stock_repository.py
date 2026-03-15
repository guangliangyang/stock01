from enum import Enum
from typing import Optional, List, Dict, Protocol
from datetime import date

from src.models.stock import Stock, DividendRecord
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataSource(Enum):
    """Available data sources."""
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    YAHOO_FINANCE = "yahoo_finance"
    AUTO = "auto"  # Automatically switch on failure


class StockDataClient(Protocol):
    """Protocol for stock data clients."""

    def get_all_stock_codes(self) -> List[Dict[str, str]]: ...
    def get_stock_info(self, code: str) -> Optional[Stock]: ...
    def get_dividend_history(self, code: str) -> List[DividendRecord]: ...
    def get_current_price(self, code: str) -> Optional[float]: ...
    def get_batch_current_prices(self, codes: List[str]) -> Dict[str, float]: ...
    def get_historical_prices(self, code: str, years: int = 5) -> Dict[int, float]: ...


class StockRepository:
    """Unified repository for stock data with automatic fallback."""

    def __init__(self, primary_source: DataSource = DataSource.AUTO):
        self._primary_source = primary_source
        self._current_source = primary_source
        self._akshare_client = None
        self._baostock_client = None
        self._yahoo_finance_client = None
        self._failure_counts = {
            DataSource.AKSHARE: 0,
            DataSource.BAOSTOCK: 0,
            DataSource.YAHOO_FINANCE: 0,
        }
        self._max_failures = 3  # Switch source after this many consecutive failures

    def _get_akshare_client(self):
        """Lazy load AkShare client."""
        if self._akshare_client is None:
            from src.data.akshare_client import AkShareClient
            self._akshare_client = AkShareClient()
        return self._akshare_client

    def _get_baostock_client(self):
        """Lazy load Baostock client."""
        if self._baostock_client is None:
            from src.data.baostock_client import BaostockClient
            self._baostock_client = BaostockClient()
        return self._baostock_client

    def _get_yahoo_finance_client(self):
        """Lazy load Yahoo Finance client."""
        if self._yahoo_finance_client is None:
            from src.data.yahoo_finance_client import YahooFinanceClient
            self._yahoo_finance_client = YahooFinanceClient()
        return self._yahoo_finance_client

    def _get_client(self, source: DataSource) -> StockDataClient:
        """Get client for specified source."""
        if source == DataSource.AKSHARE:
            return self._get_akshare_client()
        elif source == DataSource.BAOSTOCK:
            return self._get_baostock_client()
        elif source == DataSource.YAHOO_FINANCE:
            return self._get_yahoo_finance_client()
        else:
            # AUTO mode - prefer AkShare
            return self._get_akshare_client()

    def _get_fallback_sources(self, current: DataSource) -> List[DataSource]:
        """Get fallback sources in order of preference.

        Fallback chain: AkShare -> Baostock -> Yahoo Finance
        """
        all_sources = [DataSource.AKSHARE, DataSource.BAOSTOCK, DataSource.YAHOO_FINANCE]
        # Return sources excluding current, in order
        return [s for s in all_sources if s != current]

    def _get_fallback_source(self, current: DataSource) -> DataSource:
        """Get primary fallback source (for backward compatibility)."""
        fallbacks = self._get_fallback_sources(current)
        return fallbacks[0] if fallbacks else DataSource.AKSHARE

    def _handle_success(self, source: DataSource):
        """Reset failure count on success."""
        self._failure_counts[source] = 0

    def _handle_failure(self, source: DataSource) -> bool:
        """Handle failure and decide whether to switch source.

        Returns True if should try fallback.
        """
        self._failure_counts[source] += 1
        if self._failure_counts[source] >= self._max_failures:
            logger.warning(f"Data source {source.value} failed {self._max_failures} times, switching...")
            return True
        return False

    def set_data_source(self, source: DataSource):
        """Set the primary data source."""
        self._primary_source = source
        self._current_source = source
        logger.info(f"Data source set to: {source.value}")

    def get_current_source(self) -> DataSource:
        """Get current active data source."""
        return self._current_source

    def get_all_stock_codes(self) -> List[Dict[str, str]]:
        """Get all stock codes with automatic fallback."""
        sources = [self._current_source]
        if self._primary_source == DataSource.AUTO:
            sources.extend(self._get_fallback_sources(self._current_source))

        for source in sources:
            try:
                client = self._get_client(source)
                result = client.get_all_stock_codes()
                if result:
                    self._handle_success(source)
                    self._current_source = source
                    return result
            except Exception as e:
                logger.error(f"Error with {source.value}: {e}")
                self._handle_failure(source)
                continue
        return []

    def get_stock_info(self, code: str) -> Optional[Stock]:
        """Get stock info with automatic fallback."""
        sources = [self._current_source]
        if self._primary_source == DataSource.AUTO:
            sources.extend(self._get_fallback_sources(self._current_source))

        for source in sources:
            try:
                client = self._get_client(source)
                result = client.get_stock_info(code)
                if result:
                    self._handle_success(source)
                    return result
            except Exception as e:
                logger.error(f"Error with {source.value} for {code}: {e}")
                self._handle_failure(source)
                continue
        return None

    def get_dividend_history(self, code: str) -> List[DividendRecord]:
        """Get dividend history with automatic fallback."""
        sources = [self._current_source]
        if self._primary_source == DataSource.AUTO:
            sources.extend(self._get_fallback_sources(self._current_source))

        for source in sources:
            try:
                client = self._get_client(source)
                result = client.get_dividend_history(code)
                if result:
                    self._handle_success(source)
                    return result
            except Exception as e:
                logger.error(f"Error with {source.value} for {code}: {e}")
                self._handle_failure(source)
                continue
        return []

    def get_current_price(self, code: str) -> Optional[float]:
        """Get current price with automatic fallback."""
        sources = [self._current_source]
        if self._primary_source == DataSource.AUTO:
            sources.extend(self._get_fallback_sources(self._current_source))

        for source in sources:
            try:
                client = self._get_client(source)
                result = client.get_current_price(code)
                if result is not None:
                    self._handle_success(source)
                    return result
            except Exception as e:
                logger.error(f"Error with {source.value} for {code}: {e}")
                self._handle_failure(source)
                continue
        return None

    def get_batch_current_prices(self, codes: List[str]) -> Dict[str, float]:
        """Get batch prices with automatic fallback."""
        sources = [self._current_source]
        if self._primary_source == DataSource.AUTO:
            sources.extend(self._get_fallback_sources(self._current_source))

        for source in sources:
            try:
                client = self._get_client(source)
                result = client.get_batch_current_prices(codes)
                if result:
                    self._handle_success(source)
                    return result
            except Exception as e:
                logger.error(f"Error with {source.value}: {e}")
                self._handle_failure(source)
                continue
        return {}

    def get_historical_prices(self, code: str, years: int = 5) -> Dict[int, float]:
        """Get historical prices with automatic fallback."""
        sources = [self._current_source]
        if self._primary_source == DataSource.AUTO:
            sources.extend(self._get_fallback_sources(self._current_source))

        for source in sources:
            try:
                client = self._get_client(source)
                result = client.get_historical_prices(code, years)
                if result:
                    self._handle_success(source)
                    return result
            except Exception as e:
                logger.error(f"Error with {source.value} for {code}: {e}")
                self._handle_failure(source)
                continue
        return {}
