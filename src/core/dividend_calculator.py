from datetime import datetime
from typing import List, Dict, Optional

from src.models.stock import DividendRecord
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DividendCalculator:
    """Calculator for dividend-related metrics."""

    def calculate_consecutive_dividend_years(self, records: List[DividendRecord]) -> int:
        """Calculate the number of consecutive years with dividend payments.

        Counts backwards from the most recent completed fiscal year.

        Args:
            records: List of dividend records.

        Returns:
            Number of consecutive years with dividends.
        """
        if not records:
            return 0

        current_year = datetime.now().year
        years_with_dividend = sorted(set(r.year for r in records), reverse=True)

        if not years_with_dividend:
            return 0

        consecutive = 0
        # Start from last completed fiscal year (current year - 1)
        expected_year = current_year - 1

        for year in years_with_dividend:
            if year == expected_year:
                consecutive += 1
                expected_year -= 1
            elif year < expected_year:
                # Gap in dividend history
                break

        return consecutive

    def calculate_avg_yield(
        self,
        records: List[DividendRecord],
        avg_prices: Dict[int, float],
        years: int = 5
    ) -> float:
        """Calculate average dividend yield over specified years.

        Args:
            records: List of dividend records.
            avg_prices: Dictionary mapping year to average stock price.
            years: Number of years to calculate average over.

        Returns:
            Average yield as percentage (e.g., 5.0 for 5%).
        """
        if not records or not avg_prices:
            return 0.0

        current_year = datetime.now().year
        target_years = range(current_year - years, current_year)

        yields = []
        for year in target_years:
            # Sum all dividends for this year
            year_records = [r for r in records if r.year == year]
            if not year_records:
                continue

            total_dividend = sum(r.dividend_per_share for r in year_records)

            if year in avg_prices and avg_prices[year] > 0:
                year_yield = (total_dividend / avg_prices[year]) * 100
                yields.append(year_yield)
                logger.debug(f"Year {year}: dividend={total_dividend:.4f}, price={avg_prices[year]:.2f}, yield={year_yield:.2f}%")

        if not yields:
            return 0.0

        avg_yield = sum(yields) / len(yields)
        return round(avg_yield, 2)

    def calculate_current_dynamic_yield(
        self,
        records: List[DividendRecord],
        current_price: float
    ) -> Optional[float]:
        """Calculate current dynamic dividend yield based on most recent dividend.

        Uses the most recent full year's dividend divided by current price.

        Args:
            records: List of dividend records.
            current_price: Current stock price.

        Returns:
            Current yield as percentage, or None if cannot calculate.
        """
        if not records or not current_price or current_price <= 0:
            return None

        current_year = datetime.now().year
        # Use last completed year's dividend
        last_year = current_year - 1

        last_year_records = [r for r in records if r.year == last_year]
        if not last_year_records:
            # Try the year before
            last_year_records = [r for r in records if r.year == last_year - 1]

        if not last_year_records:
            return None

        total_dividend = sum(r.dividend_per_share for r in last_year_records)
        current_yield = (total_dividend / current_price) * 100

        return round(current_yield, 2)

    def get_total_dividends_by_year(self, records: List[DividendRecord]) -> Dict[int, float]:
        """Aggregate total dividends per year.

        Args:
            records: List of dividend records.

        Returns:
            Dictionary mapping year to total dividend per share.
        """
        result: Dict[int, float] = {}
        for record in records:
            if record.year not in result:
                result[record.year] = 0.0
            result[record.year] += record.dividend_per_share
        return result
