"""Translation manager for internationalization support."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Supported languages
LANGUAGES = {
    "en": "English",
    "zh": "中文",
}


class Translator:
    """Singleton translation manager."""

    _instance: Optional["Translator"] = None

    def __init__(self):
        self.current_language = "en"
        self.translations: Dict[str, Any] = {}
        self.locales_dir = Path(__file__).parent / "locales"
        self._load_language("en")

    @classmethod
    def instance(cls) -> "Translator":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = Translator()
        return cls._instance

    def _load_language(self, lang: str) -> bool:
        """Load translation file for specified language.

        Args:
            lang: Language code (e.g., 'en', 'zh').

        Returns:
            True if loaded successfully.
        """
        locale_file = self.locales_dir / f"{lang}.json"
        try:
            with open(locale_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            self.current_language = lang
            logger.info(f"Loaded language: {lang}")
            return True
        except FileNotFoundError:
            logger.error(f"Translation file not found: {locale_file}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in translation file: {e}")
            return False

    def set_language(self, lang: str) -> bool:
        """Set current language.

        Args:
            lang: Language code.

        Returns:
            True if language was changed successfully.
        """
        if lang == self.current_language:
            return True
        return self._load_language(lang)

    def get_current_language(self) -> str:
        """Get current language code."""
        return self.current_language

    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages.

        Returns:
            Dictionary of language codes to display names.
        """
        return LANGUAGES.copy()

    def tr(self, key: str, **kwargs) -> str:
        """Translate a key with optional format arguments.

        Args:
            key: Dot-separated key (e.g., 'toolbar.scan_stocks').
            **kwargs: Format arguments for string interpolation.

        Returns:
            Translated string or key if not found.
        """
        # Navigate nested keys
        parts = key.split(".")
        value = self.translations

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                logger.warning(f"Translation key not found: {key}")
                return key

        if not isinstance(value, str):
            logger.warning(f"Translation value is not a string: {key}")
            return key

        # Apply format arguments
        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing format argument for {key}: {e}")
                return value

        return value


# Global convenience functions
def tr(key: str, **kwargs) -> str:
    """Translate a key.

    Args:
        key: Dot-separated key (e.g., 'toolbar.scan_stocks').
        **kwargs: Format arguments.

    Returns:
        Translated string.
    """
    return Translator.instance().tr(key, **kwargs)


def set_language(lang: str) -> bool:
    """Set current language.

    Args:
        lang: Language code.

    Returns:
        True if successful.
    """
    return Translator.instance().set_language(lang)


def get_current_language() -> str:
    """Get current language code."""
    return Translator.instance().get_current_language()
