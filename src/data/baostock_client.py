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

# Lazy import baostock to avoid import errors if not installed
_bs = None


@contextmanager
def _safe_stdout():
    """Context manager to ensure stdout/stderr are valid streams."""
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


def _get_baostock():
    """Lazy load baostock module."""
    global _bs
    if _bs is None:
        try:
            with _safe_stdout():
                import baostock as bs
            _bs = bs
        except ImportError:
            logger.error("baostock not installed. Run: pip install baostock")
            raise
    return _bs


class BaostockClient:
    """Client for fetching stock data from Baostock API."""

    def __init__(self):
        self._logged_in = False
        self._last_request_time: float = 0

    def _ensure_login(self):
        """Ensure we are logged into Baostock."""
        if not self._logged_in:
            bs = _get_baostock()
            with _safe_stdout():
                result = bs.login()
            if result.error_code != '0':
                logger.error(f"Baostock login failed: {result.error_msg}")
                raise ConnectionError(f"Baostock login failed: {result.error_msg}")
            self._logged_in = True
            logger.info("Baostock login successful")

    def _throttle(self):
        """Add delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < 0.3:
            time.sleep(0.3 - elapsed)
        self._last_request_time = time.time()

    def _format_code(self, code: str) -> str:
        """Format stock code for Baostock (add exchange prefix)."""
        if code.startswith(('sh.', 'sz.')):
            return code
        # Shanghai stocks start with 6, Shenzhen with 0 or 3
        if code.startswith('6'):
            return f"sh.{code}"
        else:
            return f"sz.{code}"

    def _strip_code(self, code: str) -> str:
        """Remove exchange prefix from code."""
        if '.' in code:
            return code.split('.')[1]
        return code

    def logout(self):
        """Logout from Baostock."""
        if self._logged_in:
            bs = _get_baostock()
            with _safe_stdout():
                bs.logout()
            self._logged_in = False
            logger.info("Baostock logout")

    def get_all_stock_codes(self) -> List[Dict[str, str]]:
        """Get all A-share stock codes and names."""
        try:
            self._ensure_login()
            self._throttle()

            bs = _get_baostock()
            today = datetime.now().strftime("%Y-%m-%d")

            with _safe_stdout():
                rs = bs.query_all_stock(day=today)
            if rs.error_code != '0':
                logger.error(f"Failed to get stock list: {rs.error_msg}")
                return []

            result = []
            while rs.next():
                row = rs.get_row_data()
                code = self._strip_code(row[0])
                name = row[1]
                # Filter out indices and other non-stock items
                if len(code) == 6 and code[0] in ('0', '3', '6'):
                    result.append({"code": code, "name": name})

            logger.info(f"Baostock: Fetched {len(result)} stock codes")
            return result
        except Exception as e:
            logger.error(f"Baostock: Failed to get stock codes: {e}")
            return []

    def get_stock_info(self, code: str) -> Optional[Stock]:
        """Get basic stock information."""
        try:
            self._ensure_login()
            self._throttle()

            bs = _get_baostock()
            bs_code = self._format_code(code)

            with _safe_stdout():
                rs = bs.query_stock_basic(code=bs_code)
            if rs.error_code != '0':
                logger.error(f"Baostock: Failed to get stock info: {rs.error_msg}")
                return None

            if rs.next():
                row = rs.get_row_data()
                # Columns: code, code_name, ipoDate, outDate, type, status
                listing_date = None
                if row[2]:
                    try:
                        listing_date = datetime.strptime(row[2], "%Y-%m-%d").date()
                    except ValueError:
                        pass

                return Stock(
                    code=code,
                    name=row[1],
                    listing_date=listing_date,
                    industry="Unknown",  # Baostock basic query doesn't include industry
                )
            return None
        except Exception as e:
            logger.error(f"Baostock: Failed to get stock info for {code}: {e}")
            return None

    def get_dividend_history(self, code: str) -> List[DividendRecord]:
        """Get historical dividend records."""
        try:
            self._ensure_login()
            self._throttle()

            bs = _get_baostock()
            bs_code = self._format_code(code)

            # Query dividend data
            with _safe_stdout():
                rs = bs.query_dividend_data(code=bs_code, year="", yearType="report")
            if rs.error_code != '0':
                logger.error(f"Baostock: Failed to get dividend: {rs.error_msg}")
                return []

            records = []
            while rs.next():
                row = rs.get_row_data()
                # Columns: code, dividPreNoticeDate, dividAgmPum498Date, dividPlanAnnounceDate,
                #          dividPlanDate, dividRegistDate, dividOperateDate, dividPayDate,
                #          dividStockMarketDate, dividCashPsBeforeTax, dividCashPsAfterTax,
                #          dividStocksPs, dividCashStock, dividReserveToStockPs

                cash_dividend = row[9]  # dividCashPsBeforeTax
                if not cash_dividend or float(cash_dividend) <= 0:
                    continue

                # Get year from dividPlanDate or dividOperateDate
                year = None
                for date_field in [row[4], row[6], row[7]]:  # dividPlanDate, dividOperateDate, dividPayDate
                    if date_field:
                        try:
                            year = datetime.strptime(date_field, "%Y-%m-%d").year
                            break
                        except ValueError:
                            continue

                if not year:
                    continue

                ex_date = None
                if row[6]:  # dividOperateDate (ex-dividend date)
                    try:
                        ex_date = datetime.strptime(row[6], "%Y-%m-%d").date()
                    except ValueError:
                        pass

                records.append(DividendRecord(
                    year=year,
                    dividend_per_share=float(cash_dividend),
                    ex_dividend_date=ex_date,
                ))

            records.sort(key=lambda r: r.year, reverse=True)
            logger.debug(f"Baostock: Fetched {len(records)} dividend records for {code}")
            return records
        except Exception as e:
            logger.error(f"Baostock: Failed to get dividend for {code}: {e}")
            return []

    def get_current_price(self, code: str) -> Optional[float]:
        """Get current stock price (using latest daily data)."""
        try:
            self._ensure_login()
            self._throttle()

            bs = _get_baostock()
            bs_code = self._format_code(code)

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now().replace(day=1)).strftime("%Y-%m-%d")

            with _safe_stdout():
                rs = bs.query_history_k_data_plus(
                    code=bs_code,
                    fields="close",
                    start_date=start_date,
                    end_date=end_date,
                    frequency="d",
                    adjustflag="2"  # Forward adjusted
                )

            if rs.error_code != '0':
                return None

            last_close = None
            while rs.next():
                row = rs.get_row_data()
                if row[0]:
                    last_close = float(row[0])

            return last_close
        except Exception as e:
            logger.error(f"Baostock: Failed to get price for {code}: {e}")
            return None

    def get_batch_current_prices(self, codes: List[str]) -> Dict[str, float]:
        """Get current prices for multiple stocks."""
        result = {}
        for code in codes:
            price = self.get_current_price(code)
            if price:
                result[code] = price
        return result

    def get_historical_prices(self, code: str, years: int = 5) -> Dict[int, float]:
        """Get average yearly prices."""
        try:
            self._ensure_login()
            self._throttle()

            bs = _get_baostock()
            bs_code = self._format_code(code)

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = datetime.now().replace(year=datetime.now().year - years).strftime("%Y-%m-%d")

            with _safe_stdout():
                rs = bs.query_history_k_data_plus(
                    code=bs_code,
                    fields="date,close",
                    start_date=start_date,
                    end_date=end_date,
                    frequency="d",
                    adjustflag="2"
                )

            if rs.error_code != '0':
                return {}

            data = []
            while rs.next():
                row = rs.get_row_data()
                if row[0] and row[1]:
                    data.append({
                        "date": row[0],
                        "close": float(row[1])
                    })

            if not data:
                return {}

            df = pd.DataFrame(data)
            df["year"] = pd.to_datetime(df["date"]).dt.year
            yearly_avg = df.groupby("year")["close"].mean().to_dict()

            return {int(k): float(v) for k, v in yearly_avg.items()}
        except Exception as e:
            logger.error(f"Baostock: Failed to get historical prices for {code}: {e}")
            return {}

    def __del__(self):
        """Cleanup on deletion."""
        self.logout()
