from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


class DividendRecord(BaseModel):
    """Single dividend payment record."""
    year: int = Field(..., description="Fiscal year of the dividend")
    dividend_per_share: float = Field(..., ge=0, description="Dividend amount per share (CNY)")
    ex_dividend_date: Optional[date] = Field(None, description="Ex-dividend date")

    class Config:
        frozen = True


class Stock(BaseModel):
    """Stock basic information."""
    code: str = Field(..., min_length=6, max_length=6, description="Stock code (6 digits)")
    name: str = Field(..., min_length=1, description="Stock name")
    listing_date: Optional[date] = Field(None, description="Date when stock was listed")
    industry: str = Field(default="Unknown", description="Industry classification")
    current_price: Optional[float] = Field(None, ge=0, description="Current stock price (CNY)")

    @property
    def listing_years(self) -> int:
        """Calculate years since listing."""
        if not self.listing_date:
            return 0
        today = date.today()
        return today.year - self.listing_date.year - (
            (today.month, today.day) < (self.listing_date.month, self.listing_date.day)
        )


class ScreeningResult(BaseModel):
    """Result of stock screening analysis."""
    stock: Stock
    listing_years: int = Field(..., ge=0)
    consecutive_dividend_years: int = Field(..., ge=0)
    avg_5y_yield: float = Field(..., ge=0, description="5-year average dividend yield (%)")
    current_yield: Optional[float] = Field(None, ge=0, description="Current dynamic dividend yield (%)")
    meets_all_criteria: bool = Field(default=False)

    @property
    def status(self) -> str:
        """Return status string for display."""
        return "OK" if self.meets_all_criteria else "Not Qualified"


class AlertItem(BaseModel):
    """Alert item for sell notification."""
    stock_code: str
    stock_name: str
    current_yield: float
    threshold: float
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
