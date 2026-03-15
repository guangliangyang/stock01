import json
from pathlib import Path
from typing import Optional
from datetime import datetime, date

from src.models.portfolio import Portfolio, PortfolioItem
from src.utils.constants import PORTFOLIO_FILE
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PortfolioStore:
    """Store for portfolio data persistence."""

    def __init__(self, portfolio_file: Optional[Path] = None):
        self.portfolio_file = portfolio_file or PORTFOLIO_FILE
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure the portfolio directory exists."""
        self.portfolio_file.parent.mkdir(parents=True, exist_ok=True)

    def _json_serializer(self, obj):
        """Custom JSON serializer for dates and datetimes."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def _parse_portfolio_data(self, data: dict) -> Portfolio:
        """Parse portfolio data from JSON."""
        items = []
        for item_data in data.get("items", []):
            # Parse buy_date
            buy_date = item_data.get("buy_date")
            if isinstance(buy_date, str):
                buy_date = date.fromisoformat(buy_date)

            items.append(PortfolioItem(
                stock_code=item_data["stock_code"],
                stock_name=item_data["stock_name"],
                buy_price=item_data["buy_price"],
                buy_date=buy_date,
                quantity=item_data["quantity"],
                notes=item_data.get("notes", ""),
            ))

        # Parse timestamps
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.now()

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        else:
            updated_at = datetime.now()

        return Portfolio(items=items, created_at=created_at, updated_at=updated_at)

    def load(self) -> Portfolio:
        """Load portfolio from file.

        Returns:
            Portfolio, or empty portfolio if file doesn't exist.
        """
        if not self.portfolio_file.exists():
            logger.info("Portfolio file not found, returning empty portfolio")
            return Portfolio()

        try:
            with open(self.portfolio_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            portfolio = self._parse_portfolio_data(data)
            logger.info(f"Loaded portfolio with {len(portfolio.items)} items")
            return portfolio
        except Exception as e:
            logger.error(f"Failed to load portfolio: {e}")
            return Portfolio()

    def save(self, portfolio: Portfolio) -> bool:
        """Save portfolio to file.

        Args:
            portfolio: Portfolio to save.

        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            self._ensure_directory()
            portfolio.updated_at = datetime.now()

            with open(self.portfolio_file, "w", encoding="utf-8") as f:
                json.dump(
                    portfolio.model_dump(),
                    f,
                    indent=2,
                    ensure_ascii=False,
                    default=self._json_serializer
                )
            logger.info(f"Saved portfolio with {len(portfolio.items)} items")
            return True
        except Exception as e:
            logger.error(f"Failed to save portfolio: {e}")
            return False

    def add_stock(
        self,
        stock_code: str,
        stock_name: str,
        buy_price: float,
        buy_date: date,
        quantity: int,
        notes: str = ""
    ) -> bool:
        """Add a stock to portfolio.

        Args:
            stock_code: Stock code.
            stock_name: Stock name.
            buy_price: Purchase price.
            buy_date: Purchase date.
            quantity: Number of shares.
            notes: Optional notes.

        Returns:
            True if added successfully.
        """
        portfolio = self.load()
        item = PortfolioItem(
            stock_code=stock_code,
            stock_name=stock_name,
            buy_price=buy_price,
            buy_date=buy_date,
            quantity=quantity,
            notes=notes,
        )
        portfolio.add_item(item)
        return self.save(portfolio)

    def remove_stock(self, stock_code: str) -> bool:
        """Remove a stock from portfolio.

        Args:
            stock_code: Stock code to remove.

        Returns:
            True if removed successfully.
        """
        portfolio = self.load()
        if portfolio.remove_item(stock_code):
            return self.save(portfolio)
        return False

    def clear(self) -> bool:
        """Clear all portfolio items.

        Returns:
            True if cleared successfully.
        """
        return self.save(Portfolio())
