import io
import sys
import time
from contextlib import contextmanager
from datetime import datetime, date
from typing import Optional, List, Dict
import akshare as ak
import pandas as pd

from src.models.stock import Stock, DividendRecord
from src.utils.logger import get_logger
from src.utils.constants import API_RETRY_COUNT, API_RETRY_DELAY_SECONDS

logger = get_logger(__name__)


@contextmanager
def _safe_stdout():
    """Context manager to ensure stdout/stderr are valid streams.

    In windowed PyQt5 apps, sys.stdout and sys.stderr are None.
    AkShare internally uses print/write which causes errors.
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
REQUEST_DELAY_SECONDS = 0.5


class AkShareClient:
    """Client for fetching stock data from AkShare API."""

    def __init__(self):
        self._stock_list_cache: Optional[pd.DataFrame] = None
        self._stock_list_cache_time: Optional[datetime] = None
        self._last_request_time: float = 0

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
                # Use safe stdout context to handle windowed exe mode
                with _safe_stdout():
                    result = func(*args, **kwargs)
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"API request failed (attempt {attempt + 1}/{API_RETRY_COUNT}): {e}")
                if attempt < API_RETRY_COUNT - 1:
                    # Exponential backoff: 2s, 4s, 8s
                    time.sleep(API_RETRY_DELAY_SECONDS * (2 ** attempt))
        logger.error(f"API request failed after {API_RETRY_COUNT} attempts: {last_error}")
        raise last_error

    def get_all_stock_codes(self) -> List[Dict[str, str]]:
        """Get all A-share stock codes and names.

        Returns:
            List of dicts with 'code' and 'name' keys.
        """
        try:
            df = self._retry_request(ak.stock_info_a_code_name)
            result = []
            for _, row in df.iterrows():
                result.append({
                    "code": str(row["code"]),
                    "name": str(row["name"]),
                })
            logger.info(f"Fetched {len(result)} stock codes")
            return result
        except Exception as e:
            logger.error(f"Failed to get stock codes: {e}")
            return []

    def get_stock_info(self, code: str) -> Optional[Stock]:
        """Get basic stock information including listing date.

        Args:
            code: 6-digit stock code.

        Returns:
            Stock object or None if failed.
        """
        try:
            df = self._retry_request(ak.stock_individual_info_em, symbol=code)
            info_dict = dict(zip(df["item"], df["value"]))

            listing_date = None
            listing_str = str(info_dict.get("上市时间", ""))
            if listing_str and listing_str != "nan":
                try:
                    listing_date = datetime.strptime(listing_str, "%Y%m%d").date()
                except ValueError:
                    logger.warning(f"Invalid listing date format for {code}: {listing_str}")

            return Stock(
                code=code,
                name=str(info_dict.get("股票简称", "")),
                listing_date=listing_date,
                industry=str(info_dict.get("行业", "Unknown")),
            )
        except Exception as e:
            logger.error(f"Failed to get stock info for {code}: {e}")
            return None

    def get_dividend_history(self, code: str) -> List[DividendRecord]:
        """Get historical dividend records for a stock.

        Args:
            code: 6-digit stock code.

        Returns:
            List of DividendRecord objects, sorted by year descending.
        """
        try:
            # Use stock_history_dividend_detail with indicator="分红" for dividend data
            # Parameters: symbol, indicator, date
            df = self._retry_request(
                ak.stock_history_dividend_detail,
                symbol=code,
                indicator="分红",
                date=""
            )
            records = []

            if df is None or df.empty:
                return records

            for _, row in df.iterrows():
                # Column name is "派息(税前)(元)" for dividend per share
                dividend_per_share = row.get("派息(税前)(元)")
                if pd.isna(dividend_per_share) or float(dividend_per_share) <= 0:
                    continue

                # Get year from ex-dividend date or announcement date
                ex_date = None
                ex_date_str = row.get("除权除息日")
                if pd.notna(ex_date_str) and str(ex_date_str) != "-":
                    try:
                        if isinstance(ex_date_str, str):
                            ex_date = datetime.strptime(ex_date_str, "%Y-%m-%d").date()
                        elif isinstance(ex_date_str, (datetime, date)):
                            ex_date = ex_date_str if isinstance(ex_date_str, date) else ex_date_str.date()
                    except (ValueError, AttributeError):
                        pass

                # Determine year from ex-dividend date or announcement date
                year = None
                if ex_date:
                    year = ex_date.year
                else:
                    announce_date_str = row.get("公告日期")
                    if pd.notna(announce_date_str):
                        try:
                            if isinstance(announce_date_str, str):
                                year = datetime.strptime(announce_date_str, "%Y-%m-%d").year
                            elif isinstance(announce_date_str, (datetime, date)):
                                year = announce_date_str.year
                        except (ValueError, AttributeError):
                            pass

                if year is None:
                    continue

                records.append(DividendRecord(
                    year=year,
                    dividend_per_share=float(dividend_per_share),
                    ex_dividend_date=ex_date,
                ))

            records.sort(key=lambda r: r.year, reverse=True)
            logger.debug(f"Fetched {len(records)} dividend records for {code}")
            return records
        except Exception as e:
            logger.error(f"Failed to get dividend history for {code}: {e}")
            return []

    def get_current_price(self, code: str) -> Optional[float]:
        """Get current stock price.

        Args:
            code: 6-digit stock code.

        Returns:
            Current price or None if failed.
        """
        try:
            df = self._retry_request(ak.stock_zh_a_spot_em)
            stock_row = df[df["代码"] == code]
            if stock_row.empty:
                logger.warning(f"Stock {code} not found in real-time data")
                return None
            return float(stock_row.iloc[0]["最新价"])
        except Exception as e:
            logger.error(f"Failed to get current price for {code}: {e}")
            return None

    def get_batch_current_prices(self, codes: List[str]) -> Dict[str, float]:
        """Get current prices for multiple stocks efficiently.

        Args:
            codes: List of stock codes.

        Returns:
            Dictionary mapping code to current price.
        """
        try:
            df = self._retry_request(ak.stock_zh_a_spot_em)
            result = {}
            for code in codes:
                stock_row = df[df["代码"] == code]
                if not stock_row.empty:
                    price = stock_row.iloc[0]["最新价"]
                    if pd.notna(price):
                        result[code] = float(price)
            logger.debug(f"Fetched prices for {len(result)}/{len(codes)} stocks")
            return result
        except Exception as e:
            logger.error(f"Failed to get batch prices: {e}")
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
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now().replace(year=datetime.now().year - years)).strftime("%Y%m%d")

            df = self._retry_request(
                ak.stock_zh_a_hist,
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # Forward adjusted
            )

            if df.empty:
                return {}

            df["日期"] = pd.to_datetime(df["日期"])
            df["year"] = df["日期"].dt.year

            yearly_avg = df.groupby("year")["收盘"].mean().to_dict()
            return {int(k): float(v) for k, v in yearly_avg.items()}
        except Exception as e:
            logger.error(f"Failed to get historical prices for {code}: {e}")
            return {}
