from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application configuration with screening parameters."""

    # Buy filter criteria
    min_listing_years: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Minimum years since stock listing"
    )
    min_dividend_years: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Minimum consecutive years of dividend payments"
    )
    min_avg_yield: float = Field(
        default=5.0,
        ge=0.1,
        le=20.0,
        description="Minimum 5-year average dividend yield (%)"
    )

    # Sell alert criteria
    sell_yield_threshold: float = Field(
        default=3.0,
        ge=0.1,
        le=10.0,
        description="Alert when current yield drops below this (%)"
    )

    # Cache settings
    cache_expiration_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Hours before cached data expires"
    )

    # UI settings
    language: str = Field(
        default="en",
        description="UI language (en, zh)"
    )

    class Config:
        validate_assignment = True

    def to_display_dict(self) -> dict:
        """Convert to dictionary with display-friendly keys."""
        return {
            "Min Listing Years": self.min_listing_years,
            "Min Dividend Years": self.min_dividend_years,
            "Min Avg Yield (%)": self.min_avg_yield,
            "Sell Threshold (%)": self.sell_yield_threshold,
        }
