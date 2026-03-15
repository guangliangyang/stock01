from typing import List, Optional
from datetime import datetime

from src.models.stock import AlertItem
from src.models.portfolio import Portfolio
from src.models.config import AppConfig
from src.core.dividend_calculator import DividendCalculator
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AlertEngine:
    """Engine for checking portfolio stocks and generating sell alerts."""

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

    def check_portfolio(
        self,
        portfolio: Portfolio,
        config: AppConfig
    ) -> List[AlertItem]:
        """Check all portfolio stocks against sell criteria.

        Args:
            portfolio: User's portfolio.
            config: Application configuration with sell threshold.

        Returns:
            List of AlertItem for stocks that should trigger sell alerts.
        """
        alerts = []
        codes = portfolio.get_all_codes()

        if not codes:
            logger.info("Portfolio is empty, no alerts to check")
            return alerts

        logger.info(f"Checking {len(codes)} portfolio stocks for sell alerts")

        # Get current prices in batch for efficiency
        current_prices = self.repository.get_batch_current_prices(codes)

        for item in portfolio.items:
            code = item.stock_code
            name = item.stock_name

            try:
                # Get dividend history
                dividend_records = self.repository.get_dividend_history(code)
                if not dividend_records:
                    logger.warning(f"No dividend history for {code}, skipping alert check")
                    continue

                # Get current price
                current_price = current_prices.get(code)
                if not current_price:
                    current_price = self.repository.get_current_price(code)

                if not current_price:
                    logger.warning(f"Could not get current price for {code}, skipping")
                    continue

                # Calculate current yield
                current_yield = self.calculator.calculate_current_dynamic_yield(
                    dividend_records, current_price
                )

                if current_yield is None:
                    logger.warning(f"Could not calculate yield for {code}, skipping")
                    continue

                # Check against threshold
                if current_yield < config.sell_yield_threshold:
                    alert = AlertItem(
                        stock_code=code,
                        stock_name=name,
                        current_yield=current_yield,
                        threshold=config.sell_yield_threshold,
                        message=f"Sell Alert: {name} ({code}) yield {current_yield:.2f}% is below threshold {config.sell_yield_threshold:.2f}%",
                        timestamp=datetime.now()
                    )
                    alerts.append(alert)
                    logger.warning(f"ALERT: {alert.message}")
                else:
                    logger.debug(f"{code} yield {current_yield:.2f}% is OK (threshold: {config.sell_yield_threshold}%)")

            except Exception as e:
                logger.error(f"Error checking {code} for alerts: {e}")
                continue

        logger.info(f"Alert check complete. Found {len(alerts)} alerts.")
        return alerts

    def check_single_stock(
        self,
        code: str,
        name: str,
        config: AppConfig
    ) -> Optional[AlertItem]:
        """Check a single stock against sell criteria.

        Args:
            code: Stock code.
            name: Stock name.
            config: Application configuration.

        Returns:
            AlertItem if stock triggers alert, None otherwise.
        """
        try:
            dividend_records = self.repository.get_dividend_history(code)
            if not dividend_records:
                return None

            current_price = self.repository.get_current_price(code)
            if not current_price:
                return None

            current_yield = self.calculator.calculate_current_dynamic_yield(
                dividend_records, current_price
            )

            if current_yield is None:
                return None

            if current_yield < config.sell_yield_threshold:
                return AlertItem(
                    stock_code=code,
                    stock_name=name,
                    current_yield=current_yield,
                    threshold=config.sell_yield_threshold,
                    message=f"Sell Alert: {name} ({code}) yield {current_yield:.2f}% is below threshold {config.sell_yield_threshold:.2f}%",
                    timestamp=datetime.now()
                )

            return None
        except Exception as e:
            logger.error(f"Error checking {code}: {e}")
            return None
