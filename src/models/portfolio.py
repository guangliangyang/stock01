from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field


class PortfolioItem(BaseModel):
    """Single stock holding in portfolio."""
    stock_code: str = Field(..., min_length=6, max_length=6)
    stock_name: str = Field(..., min_length=1)
    buy_price: float = Field(..., gt=0, description="Purchase price per share (CNY)")
    buy_date: date = Field(..., description="Purchase date")
    quantity: int = Field(..., gt=0, description="Number of shares")
    notes: str = Field(default="", description="User notes")

    @property
    def total_cost(self) -> float:
        """Total investment cost."""
        return self.buy_price * self.quantity


class Portfolio(BaseModel):
    """User's stock portfolio."""
    items: List[PortfolioItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def add_item(self, item: PortfolioItem) -> None:
        """Add a stock to portfolio."""
        self.items.append(item)
        self.updated_at = datetime.now()

    def remove_item(self, stock_code: str) -> bool:
        """Remove a stock from portfolio by code. Returns True if removed."""
        original_len = len(self.items)
        self.items = [item for item in self.items if item.stock_code != stock_code]
        if len(self.items) < original_len:
            self.updated_at = datetime.now()
            return True
        return False

    def get_item(self, stock_code: str) -> Optional[PortfolioItem]:
        """Get portfolio item by stock code."""
        for item in self.items:
            if item.stock_code == stock_code:
                return item
        return None

    def get_all_codes(self) -> List[str]:
        """Get all stock codes in portfolio."""
        return [item.stock_code for item in self.items]

    @property
    def total_investment(self) -> float:
        """Total investment across all holdings."""
        return sum(item.total_cost for item in self.items)
