import io
import sys
import time
from contextlib import contextmanager
from datetime import datetime, date
from typing import Optional, List, Dict
import pandas as pd

from src.models.stock import Stock, DividendRecord
from src.utils.logger import get_logger
from src.utils.constants import API_RETRY_COUNT, API_RETRY_DELAY_SECONDS

logger = get_logger(__name__)


@contextmanager
def _safe_stdout():
    """Context manager to ensure stdout/stderr are valid streams.

    In windowed PyQt5 apps, sys.stdout and sys.stderr are None.
    yfinance internally uses print/write which causes errors.
    This temporarily replaces them with StringIO if they're None.
    """
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    try:
        if sys.stdout is None:
            sys.stdout = io.StringIO()
        if sys.stderr is None:
            sys.stderr = io.StringIO()
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


# Delay between API requests to avoid rate limiting
REQUEST_DELAY_SECONDS = 0.3


class YahooFinanceClient:
    """Client for fetching A-share stock data from Yahoo Finance API.

    This client is useful for users outside China who cannot access
    AkShare or Baostock due to network restrictions.

    Note: Yahoo Finance has limited A-share coverage and data may be
    incomplete or delayed compared to Chinese data sources.
    """

    def __init__(self):
        self._last_request_time: float = 0
        self._stock_list_cache: Optional[List[Dict[str, str]]] = None

    def _throttle(self):
        """Add delay between requests to avoid rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_DELAY_SECONDS:
            time.sleep(REQUEST_DELAY_SECONDS - elapsed)
        self._last_request_time = time.time()

    def _retry_request(self, func, *args, **kwargs):
        """Execute a function with retry logic."""
        self._throttle()
        last_error = None
        for attempt in range(API_RETRY_COUNT):
            try:
                with _safe_stdout():
                    result = func(*args, **kwargs)
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Yahoo Finance request failed (attempt {attempt + 1}/{API_RETRY_COUNT}): {e}")
                if attempt < API_RETRY_COUNT - 1:
                    time.sleep(API_RETRY_DELAY_SECONDS * (2 ** attempt))
        logger.error(f"Yahoo Finance request failed after {API_RETRY_COUNT} attempts: {last_error}")
        raise last_error

    def _to_yahoo_symbol(self, code: str) -> str:
        """Convert A-share code to Yahoo Finance symbol.

        Shanghai stocks (6xxxxx): append .SS
        Shenzhen stocks (0xxxxx, 3xxxxx): append .SZ

        Args:
            code: 6-digit A-share stock code

        Returns:
            Yahoo Finance symbol (e.g., "600000.SS")
        """
        code = code.strip()
        if code.startswith("6"):
            return f"{code}.SS"
        elif code.startswith("0") or code.startswith("3"):
            return f"{code}.SZ"
        else:
            # Default to Shanghai
            return f"{code}.SS"

    def _from_yahoo_symbol(self, symbol: str) -> str:
        """Convert Yahoo Finance symbol back to A-share code.

        Args:
            symbol: Yahoo Finance symbol (e.g., "600000.SS")

        Returns:
            6-digit A-share code
        """
        return symbol.replace(".SS", "").replace(".SZ", "")

    def get_all_stock_codes(self) -> List[Dict[str, str]]:
        """Get all A-share stock codes and names.

        Note: Yahoo Finance doesn't provide a complete A-share stock list API.
        This method returns a predefined list of major A-share stocks or
        relies on cached data from other sources.

        Returns:
            List of dicts with 'code' and 'name' keys.
        """
        # Yahoo Finance doesn't have an API to list all A-shares
        # Return empty list - the app should use AkShare/Baostock for full list
        # Yahoo Finance is primarily for getting data for individual stocks
        logger.warning("Yahoo Finance does not support listing all A-share stocks. Use AkShare or Baostock for stock list.")
        return []

    def get_stock_info(self, code: str) -> Optional[Stock]:
        """Get basic stock information including listing date.

        Args:
            code: 6-digit stock code.

        Returns:
            Stock object or None if failed.
        """
        try:
            import yfinance as yf

            symbol = self._to_yahoo_symbol(code)
            ticker = self._retry_request(lambda: yf.Ticker(symbol))

            with _safe_stdout():
                info = ticker.info

            if not info or info.get("regularMarketPrice") is None:
                logger.warning(f"No data found for {symbol} on Yahoo Finance")
                return None

            # Extract listing date if available
            listing_date = None
            # Yahoo Finance doesn't always have IPO date for A-shares

            # Get name - Yahoo may have English or Chinese name
            name = info.get("shortName") or info.get("longName") or code

            # Get industry
            industry = info.get("industry") or info.get("sector") or "Unknown"

            # Get current price
            current_price = info.get("regularMarketPrice")

            return Stock(
                code=code,
                name=name,
                listing_date=listing_date,
                industry=industry,
                current_price=float(current_price) if current_price else None,
            )
        except Exception as e:
            logger.error(f"Failed to get stock info for {code} from Yahoo Finance: {e}")
            return None

    def get_dividend_history(self, code: str) -> List[DividendRecord]:
        """Get historical dividend records for a stock.

        Args:
            code: 6-digit stock code.

        Returns:
            List of DividendRecord objects, sorted by year descending.
        """
        try:
            import yfinance as yf

            symbol = self._to_yahoo_symbol(code)
            ticker = self._retry_request(lambda: yf.Ticker(symbol))

            with _safe_stdout():
                dividends = ticker.dividends

            if dividends is None or dividends.empty:
                logger.debug(f"No dividend data for {code} on Yahoo Finance")
                return []

            records = []
            # Group dividends by year
            yearly_dividends: Dict[int, float] = {}
            yearly_dates: Dict[int, date] = {}

            for idx, value in dividends.items():
                if pd.notna(value) and float(value) > 0:
                    year = idx.year
                    if year not in yearly_dividends:
                        yearly_dividends[year] = 0
                        yearly_dates[year] = idx.date() if hasattr(idx, 'date') else None
                    yearly_dividends[year] += float(value)

            for year, dividend in yearly_dividends.items():
                records.append(DividendRecord(
                    year=year,
                    dividend_per_share=dividend,
                    ex_dividend_date=yearly_dates.get(year),
                ))

            records.sort(key=lambda r: r.year, reverse=True)
            logger.debug(f"Fetched {len(records)} dividend records for {code} from Yahoo Finance")
            return records
        except Exception as e:
            logger.error(f"Failed to get dividend history for {code} from Yahoo Finance: {e}")
            return []

    def get_current_price(self, code: str) -> Optional[float]:
        """Get current stock price.

        Args:
            code: 6-digit stock code.

        Returns:
            Current price or None if failed.
        """
        try:
            import yfinance as yf

            symbol = self._to_yahoo_symbol(code)
            ticker = self._retry_request(lambda: yf.Ticker(symbol))

            with _safe_stdout():
                info = ticker.info

            price = info.get("regularMarketPrice")
            if price is not None:
                return float(price)

            # Fallback to history
            with _safe_stdout():
                hist = ticker.history(period="1d")

            if not hist.empty:
                return float(hist["Close"].iloc[-1])

            return None
        except Exception as e:
            logger.error(f"Failed to get current price for {code} from Yahoo Finance: {e}")
            return None

    def get_batch_current_prices(self, codes: List[str]) -> Dict[str, float]:
        """Get current prices for multiple stocks.

        Args:
            codes: List of stock codes.

        Returns:
            Dictionary mapping code to current price.
        """
        try:
            import yfinance as yf

            if not codes:
                return {}

            # Convert to Yahoo symbols
            symbols = [self._to_yahoo_symbol(code) for code in codes]
            symbols_str = " ".join(symbols)

            with _safe_stdout():
                tickers = yf.Tickers(symbols_str)

            result = {}
            for code, symbol in zip(codes, symbols):
                try:
                    with _safe_stdout():
                        info = tickers.tickers[symbol].info
                    price = info.get("regularMarketPrice")
                    if price is not None:
                        result[code] = float(price)
                except Exception as e:
                    logger.debug(f"Failed to get price for {code}: {e}")
                    continue

            logger.debug(f"Fetched prices for {len(result)}/{len(codes)} stocks from Yahoo Finance")
            return result
        except Exception as e:
            logger.error(f"Failed to get batch prices from Yahoo Finance: {e}")
            return {}

    def get_historical_prices(self, code: str, years: int = 5) -> Dict[int, float]:
        """Get average yearly prices for dividend yield calculation.

        Args:
            code: 6-digit stock code.
            years: Number of years of history to fetch.

        Returns:
            Dictionary mapping year to average price.
        """
        try:
            import yfinance as yf

            symbol = self._to_yahoo_symbol(code)
            ticker = self._retry_request(lambda: yf.Ticker(symbol))

            with _safe_stdout():
                hist = ticker.history(period=f"{years}y")

            if hist.empty:
                return {}

            # Calculate yearly average prices
            hist["year"] = hist.index.year
            yearly_avg = hist.groupby("year")["Close"].mean().to_dict()

            return {int(k): float(v) for k, v in yearly_avg.items()}
        except Exception as e:
            logger.error(f"Failed to get historical prices for {code} from Yahoo Finance: {e}")
            return {}
