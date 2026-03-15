from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QPushButton, QGroupBox, QFormLayout
)
from PyQt5.QtCore import pyqtSignal

from src.models.config import AppConfig
from src.i18n import tr


class ConfigPanel(QWidget):
    """Configuration panel for screening parameters."""

    configChanged = pyqtSignal(AppConfig)
    configReset = pyqtSignal()

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Buy criteria group
        self.buy_group = QGroupBox(tr("config.buy_criteria"))
        buy_layout = QFormLayout()

        # Min listing years
        self.listing_years_spin = QSpinBox()
        self.listing_years_spin.setRange(1, 50)
        self.listing_years_spin.setSuffix(tr("config.years_suffix"))
        self.listing_years_label = QLabel(tr("config.min_listing_years"))
        buy_layout.addRow(self.listing_years_label, self.listing_years_spin)

        # Min dividend years
        self.dividend_years_spin = QSpinBox()
        self.dividend_years_spin.setRange(1, 20)
        self.dividend_years_spin.setSuffix(tr("config.years_suffix"))
        self.dividend_years_label = QLabel(tr("config.min_dividend_years"))
        buy_layout.addRow(self.dividend_years_label, self.dividend_years_spin)

        # Min avg yield
        self.avg_yield_spin = QDoubleSpinBox()
        self.avg_yield_spin.setRange(0.1, 20.0)
        self.avg_yield_spin.setDecimals(1)
        self.avg_yield_spin.setSingleStep(0.5)
        self.avg_yield_spin.setSuffix(tr("config.percent_suffix"))
        self.avg_yield_label = QLabel(tr("config.min_avg_yield"))
        buy_layout.addRow(self.avg_yield_label, self.avg_yield_spin)

        self.buy_group.setLayout(buy_layout)
        layout.addWidget(self.buy_group)

        # Sell criteria group
        self.sell_group = QGroupBox(tr("config.sell_criteria"))
        sell_layout = QFormLayout()

        # Sell threshold
        self.sell_threshold_spin = QDoubleSpinBox()
        self.sell_threshold_spin.setRange(0.1, 10.0)
        self.sell_threshold_spin.setDecimals(1)
        self.sell_threshold_spin.setSingleStep(0.5)
        self.sell_threshold_spin.setSuffix(tr("config.percent_suffix"))
        self.sell_threshold_label = QLabel(tr("config.sell_threshold"))
        sell_layout.addRow(self.sell_threshold_label, self.sell_threshold_spin)

        self.sell_group.setLayout(sell_layout)
        layout.addWidget(self.sell_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.apply_btn = QPushButton(tr("config.apply"))
        self.apply_btn.clicked.connect(self._on_apply)
        button_layout.addWidget(self.apply_btn)

        self.reset_btn = QPushButton(tr("config.reset"))
        self.reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(self.reset_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

    def _load_config(self):
        """Load config values into widgets."""
        self.listing_years_spin.setValue(self._config.min_listing_years)
        self.dividend_years_spin.setValue(self._config.min_dividend_years)
        self.avg_yield_spin.setValue(self._config.min_avg_yield)
        self.sell_threshold_spin.setValue(self._config.sell_yield_threshold)

    def _on_apply(self):
        """Handle apply button click."""
        self._config = AppConfig(
            min_listing_years=self.listing_years_spin.value(),
            min_dividend_years=self.dividend_years_spin.value(),
            min_avg_yield=self.avg_yield_spin.value(),
            sell_yield_threshold=self.sell_threshold_spin.value(),
            language=self._config.language,
        )
        self.configChanged.emit(self._config)

    def _on_reset(self):
        """Handle reset button click."""
        lang = self._config.language
        self._config = AppConfig(language=lang)
        self._load_config()
        self.configReset.emit()

    def get_config(self) -> AppConfig:
        """Get current config from widget values."""
        return AppConfig(
            min_listing_years=self.listing_years_spin.value(),
            min_dividend_years=self.dividend_years_spin.value(),
            min_avg_yield=self.avg_yield_spin.value(),
            sell_yield_threshold=self.sell_threshold_spin.value(),
            language=self._config.language,
        )

    def set_config(self, config: AppConfig):
        """Set config and update widgets."""
        self._config = config
        self._load_config()

    def refresh_texts(self):
        """Refresh all text for language change."""
        self.buy_group.setTitle(tr("config.buy_criteria"))
        self.sell_group.setTitle(tr("config.sell_criteria"))

        self.listing_years_label.setText(tr("config.min_listing_years"))
        self.dividend_years_label.setText(tr("config.min_dividend_years"))
        self.avg_yield_label.setText(tr("config.min_avg_yield"))
        self.sell_threshold_label.setText(tr("config.sell_threshold"))

        self.listing_years_spin.setSuffix(tr("config.years_suffix"))
        self.dividend_years_spin.setSuffix(tr("config.years_suffix"))
        self.avg_yield_spin.setSuffix(tr("config.percent_suffix"))
        self.sell_threshold_spin.setSuffix(tr("config.percent_suffix"))

        self.apply_btn.setText(tr("config.apply"))
        self.reset_btn.setText(tr("config.reset"))
