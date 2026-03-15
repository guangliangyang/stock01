import sys
from pathlib import Path
from loguru import logger

# Remove default handler
logger.remove()

# Console handler - INFO level (only if stderr is available)
if sys.stderr is not None:
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        colorize=True,
    )

# File handler - DEBUG level with rotation
# Use user's AppData for packaged exe, or project dir for development
if getattr(sys, 'frozen', False):
    # Running as packaged exe
    log_dir = Path.home() / "AppData" / "Local" / "DividendStockScreener" / "logs"
else:
    # Running in development
    log_dir = Path(__file__).parent.parent.parent / "data" / "logs"

log_dir.mkdir(parents=True, exist_ok=True)

logger.add(
    log_dir / "app_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    encoding="utf-8",
)


def get_logger(name: str):
    """Get a logger instance with the given name."""
    return logger.bind(name=name)
