from typing import List, Optional, Callable, Union
from dataclasses import dataclass

from src.models.stock import Stock, ScreeningResult
from src.models.config import AppConfig
from src.core.dividend_calculator import DividendCalculator
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScreeningProgress:
    """Progress information for screening operation."""
    current: int
    total: int
    current_stock: str
    message: str


class StockScreener:
    """Screener for filtering stocks based on dividend criteria."""

    def __init__(
        self,
        client=None,
        repository=None,
        calculator: Optional[DividendCalculator] = None
    ):
        # Support both old client interface and new repository
        if repository is not None:
            self.repository = repository
        elif client is not None:
            self.repository = client
        else:
            from src.data.stock_repository import StockRepository
            self.repository = StockRepository()
        self.calculator = calculator or DividendCalculator()

    def screen_stock(self, code: str, name: str, config: AppConfig) -> Optional[ScreeningResult]:
        """Screen a single stock against criteria.

        Args:
            code: Stock code.
            name: Stock name.
            config: Screening configuration.

        Returns:
            ScreeningResult or None if stock doesn't pass initial checks.
        """
        # Get stock info
        stock = self.repository.get_stock_info(code)
        if not stock:
            logger.debug(f"Skipping {code}: failed to get stock info")
            return None

        # Check listing years
        listing_years = stock.listing_years
        if listing_years < config.min_listing_years:
            logger.debug(f"Skipping {code}: listing years {listing_years} < {config.min_listing_years}")
            return ScreeningResult(
                stock=stock,
                listing_years=listing_years,
                consecutive_dividend_years=0,
                avg_5y_yield=0.0,
                current_yield=None,
                meets_all_criteria=False,
            )

        # Get dividend history
        dividend_records = self.repository.get_dividend_history(code)
        if not dividend_records:
            logger.debug(f"Skipping {code}: no dividend history")
            return ScreeningResult(
                stock=stock,
                listing_years=listing_years,
                consecutive_dividend_years=0,
                avg_5y_yield=0.0,
                current_yield=None,
                meets_all_criteria=False,
            )

        # Calculate consecutive dividend years
        consecutive_years = self.calculator.calculate_consecutive_dividend_years(dividend_records)
        if consecutive_years < config.min_dividend_years:
            logger.debug(f"Skipping {code}: dividend years {consecutive_years} < {config.min_dividend_years}")
            return ScreeningResult(
                stock=stock,
                listing_years=listing_years,
                consecutive_dividend_years=consecutive_years,
                avg_5y_yield=0.0,
                current_yield=None,
                meets_all_criteria=False,
            )

        # Get historical prices for yield calculation
        historical_prices = self.repository.get_historical_prices(code, years=5)
        avg_5y_yield = self.calculator.calculate_5y_avg_yield(dividend_records, historical_prices)

        # Get current price and yield
        current_price = self.repository.get_current_price(code)
        stock.current_price = current_price
        current_yield = self.calculator.calculate_current_dynamic_yield(dividend_records, current_price)

        # Check if meets all criteria
        meets_criteria = (
            listing_years >= config.min_listing_years
            and consecutive_years >= config.min_dividend_years
            and avg_5y_yield >= config.min_avg_yield
        )

        return ScreeningResult(
            stock=stock,
            listing_years=listing_years,
            consecutive_dividend_years=consecutive_years,
            avg_5y_yield=avg_5y_yield,
            current_yield=current_yield,
            meets_all_criteria=meets_criteria,
        )

    def screen_all_stocks(
        self,
        config: AppConfig,
        progress_callback: Optional[Callable[[ScreeningProgress], None]] = None,
        stop_flag: Optional[Callable[[], bool]] = None
    ) -> List[ScreeningResult]:
        """Screen all A-share stocks against criteria.

        Args:
            config: Screening configuration.
            progress_callback: Optional callback for progress updates.
            stop_flag: Optional callable that returns True to stop screening.

        Returns:
            List of ScreeningResult for stocks that meet all criteria.
        """
        # Get all stock codes
        stocks = self.repository.get_all_stock_codes()
        total = len(stocks)
        logger.info(f"Starting screening of {total} stocks")

        results = []
        for i, stock_info in enumerate(stocks):
            # Check stop flag
            if stop_flag and stop_flag():
                logger.info("Screening stopped by user")
                break

            code = stock_info["code"]
            name = stock_info["name"]

            # Update progress
            if progress_callback:
                progress_callback(ScreeningProgress(
                    current=i + 1,
                    total=total,
                    current_stock=f"{code} {name}",
                    message=f"Screening {code} {name}..."
                ))

            try:
                result = self.screen_stock(code, name, config)
                if result and result.meets_all_criteria:
                    results.append(result)
                    logger.info(f"Found qualifying stock: {code} {name} - Yield: {result.avg_5y_yield}%")
            except Exception as e:
                logger.error(f"Error screening {code}: {e}")
                continue

        # Sort by 5-year average yield descending
        results.sort(key=lambda r: r.avg_5y_yield, reverse=True)
        logger.info(f"Screening complete. Found {len(results)} qualifying stocks.")

        return results

    def screen_specific_stocks(
        self,
        codes: List[str],
        config: AppConfig,
        progress_callback: Optional[Callable[[ScreeningProgress], None]] = None
    ) -> List[ScreeningResult]:
        """Screen specific stocks by code.

        Args:
            codes: List of stock codes to screen.
            config: Screening configuration.
            progress_callback: Optional callback for progress updates.

        Returns:
            List of ScreeningResult for all screened stocks.
        """
        total = len(codes)
        results = []

        for i, code in enumerate(codes):
            if progress_callback:
                progress_callback(ScreeningProgress(
                    current=i + 1,
                    total=total,
                    current_stock=code,
                    message=f"Screening {code}..."
                ))

            try:
                result = self.screen_stock(code, "", config)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error screening {code}: {e}")
                continue

        return results
