import json
from pathlib import Path
from typing import Optional

from src.models.config import AppConfig
from src.utils.constants import DEFAULT_SETTINGS_FILE, USER_SETTINGS_FILE
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SettingsStore:
    """Store for application settings persistence."""

    def __init__(self, settings_file: Optional[Path] = None):
        self.settings_file = settings_file or USER_SETTINGS_FILE
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure the settings directory exists."""
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppConfig:
        """Load settings from file.

        Returns:
            AppConfig with user settings, or defaults if file doesn't exist.
        """
        # Try to load user settings first
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                config = AppConfig(**data)
                logger.info(f"Loaded settings from {self.settings_file}")
                return config
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")

        # Fall back to default settings
        if DEFAULT_SETTINGS_FILE.exists():
            try:
                with open(DEFAULT_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                config = AppConfig(**data)
                logger.info(f"Loaded default settings from {DEFAULT_SETTINGS_FILE}")
                return config
            except Exception as e:
                logger.error(f"Failed to load default settings: {e}")

        # Return default config
        logger.info("Using built-in default settings")
        return AppConfig()

    def save(self, config: AppConfig) -> bool:
        """Save settings to file.

        Args:
            config: AppConfig to save.

        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            self._ensure_directory()
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved settings to {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def reset_to_defaults(self) -> AppConfig:
        """Reset settings to defaults.

        Returns:
            Default AppConfig.
        """
        default_config = AppConfig()
        self.save(default_config)
        logger.info("Settings reset to defaults")
        return default_config
