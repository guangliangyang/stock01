from pathlib import Path

# Application info
APP_NAME = "Dividend Stock Screener"
APP_VERSION = "1.0.0"

# Paths
ROOT_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# Config files
DEFAULT_SETTINGS_FILE = CONFIG_DIR / "default_settings.json"
USER_SETTINGS_FILE = DATA_DIR / "settings.json"
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"

# API settings
API_RETRY_COUNT = 3
API_RETRY_DELAY_SECONDS = 1
API_REQUEST_TIMEOUT_SECONDS = 30

# Cache settings
DEFAULT_CACHE_EXPIRATION_HOURS = 24

# UI constants
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700
TABLE_ROW_HEIGHT = 30

# Column headers for results table
RESULTS_COLUMNS = [
    "Stock Code",
    "Stock Name",
    "Industry",
    "Listing Years",
    "Dividend Years",
    "5Y Avg Yield (%)",
    "Current Yield (%)",
    "Status",
]

# Column headers for portfolio table
PORTFOLIO_COLUMNS = [
    "Stock Code",
    "Stock Name",
    "Buy Price",
    "Buy Date",
    "Quantity",
    "Current Price",
    "Current Yield (%)",
    "Status",
]

# Ensure directories exist
for directory in [CONFIG_DIR, DATA_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
