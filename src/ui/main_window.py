from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QTabWidget, QToolBar, QStatusBar, QAction, QMessageBox,
    QProgressBar, QLabel, QApplication, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from src.models.config import AppConfig
from src.models.portfolio import Portfolio
from src.core.stock_screener import StockScreener, ScreeningProgress
from src.core.alert_engine import AlertEngine
from src.data.stock_repository import StockRepository, DataSource
from src.persistence.settings_store import SettingsStore
from src.persistence.portfolio_store import PortfolioStore
from src.notification.toast_notifier import ToastNotifier
from src.ui.widgets.config_panel import ConfigPanel
from src.ui.widgets.results_table import ResultsTable
from src.ui.widgets.portfolio_panel import PortfolioPanel
from src.ui.widgets.log_viewer import LogViewer
from src.utils.constants import APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from src.utils.logger import get_logger
from src.i18n import tr, set_language, get_current_language

logger = get_logger(__name__)


class ScreeningWorker(QThread):
    """Worker thread for stock screening."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, screener: StockScreener, config: AppConfig):
        super().__init__()
        self.screener = screener
        self.config = config
        self._stop_requested = False

    def run(self):
        try:
            results = self.screener.screen_all_stocks(
                self.config,
                progress_callback=self._on_progress,
                stop_flag=lambda: self._stop_requested
            )
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"Screening error: {e}")
            self.error.emit(str(e))

    def _on_progress(self, progress: ScreeningProgress):
        self.progress.emit(progress.current, progress.total, progress.message)

    def stop(self):
        self._stop_requested = True


class AlertWorker(QThread):
    """Worker thread for checking portfolio alerts."""

    finished = pyqtSignal(list, dict, dict)  # alerts, prices, yields
    error = pyqtSignal(str)

    def __init__(self, alert_engine: AlertEngine, portfolio: Portfolio, config: AppConfig):
        super().__init__()
        self.alert_engine = alert_engine
        self.portfolio = portfolio
        self.config = config

    def run(self):
        try:
            alerts = self.alert_engine.check_portfolio(self.portfolio, self.config)

            # Get current data for display
            codes = self.portfolio.get_all_codes()
            prices = self.alert_engine.repository.get_batch_current_prices(codes)

            yields = {}
            for item in self.portfolio.items:
                dividend_records = self.alert_engine.repository.get_dividend_history(item.stock_code)
                current_price = prices.get(item.stock_code)
                if dividend_records and current_price:
                    current_yield = self.alert_engine.calculator.calculate_current_dynamic_yield(
                        dividend_records, current_price
                    )
                    if current_yield:
                        yields[item.stock_code] = current_yield

            self.finished.emit(alerts, prices, yields)
        except Exception as e:
            logger.error(f"Alert check error: {e}")
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Initialize components with unified repository
        self.repository = StockRepository(DataSource.AUTO)
        self.screener = StockScreener(repository=self.repository)
        self.alert_engine = AlertEngine(repository=self.repository)
        self.settings_store = SettingsStore()
        self.portfolio_store = PortfolioStore()
        self.notifier = ToastNotifier()

        # Load data
        self.config = self.settings_store.load()
        self.portfolio = self.portfolio_store.load()

        # Initialize language from config
        set_language(self.config.language)

        # Set window properties
        self.setWindowTitle(f"{tr('app_name')} v{APP_VERSION}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Workers
        self.screening_worker: ScreeningWorker = None
        self.alert_worker: AlertWorker = None

        # Setup UI
        self._setup_ui()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

        logger.info("Main window initialized")

    def _setup_ui(self):
        """Setup the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)

        # Splitter for config panel and main content
        splitter = QSplitter(Qt.Horizontal)

        # Left side - Config panel
        self.config_panel = ConfigPanel(self.config)
        self.config_panel.setMaximumWidth(280)
        self.config_panel.setMinimumWidth(200)
        splitter.addWidget(self.config_panel)

        # Right side - Tab widget
        self.tab_widget = QTabWidget()

        # Results tab
        self.results_table = ResultsTable()
        self.tab_widget.addTab(self.results_table, tr("tabs.results"))

        # Portfolio tab
        self.portfolio_panel = PortfolioPanel()
        self.portfolio_panel.set_portfolio(self.portfolio)
        self.tab_widget.addTab(self.portfolio_panel, tr("tabs.portfolio"))

        # Log viewer tab
        self.log_viewer = LogViewer()
        self.tab_widget.addTab(self.log_viewer, tr("tabs.logs"))

        splitter.addWidget(self.tab_widget)
        splitter.setSizes([250, 750])

        layout.addWidget(splitter)

    def _setup_toolbar(self):
        """Setup the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Scan action
        self.scan_action = QAction(tr("toolbar.scan_stocks"), self)
        self.scan_action.setToolTip(tr("toolbar.scan_stocks_tip"))
        self.scan_action.triggered.connect(self._on_scan)
        toolbar.addAction(self.scan_action)

        # Stop action
        self.stop_action = QAction(tr("toolbar.stop"), self)
        self.stop_action.setToolTip(tr("toolbar.stop_tip"))
        self.stop_action.triggered.connect(self._on_stop)
        self.stop_action.setEnabled(False)
        toolbar.addAction(self.stop_action)

        toolbar.addSeparator()

        # Check portfolio action
        self.check_action = QAction(tr("toolbar.check_portfolio"), self)
        self.check_action.setToolTip(tr("toolbar.check_portfolio_tip"))
        self.check_action.triggered.connect(self._on_check_portfolio)
        toolbar.addAction(self.check_action)

        toolbar.addSeparator()

        # Data source selector
        self.source_label = QLabel(tr("toolbar.data_source"))
        toolbar.addWidget(self.source_label)
        self.source_combo = QComboBox()
        self.source_combo.addItems([
            tr("data_sources.auto"),
            tr("data_sources.akshare"),
            tr("data_sources.baostock")
        ])
        self.source_combo.setCurrentIndex(0)
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        self.source_combo.setToolTip(tr("toolbar.data_source_tip"))
        toolbar.addWidget(self.source_combo)

        toolbar.addSeparator()

        # Language selector
        self.lang_label = QLabel(tr("toolbar.language"))
        toolbar.addWidget(self.lang_label)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "中文"])
        # Set current language
        if self.config.language == "zh":
            self.language_combo.setCurrentIndex(1)
        else:
            self.language_combo.setCurrentIndex(0)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        toolbar.addWidget(self.language_combo)

        toolbar.addSeparator()

        # Last scan label
        self.last_scan_label = QLabel(f"{tr('toolbar.last_scan')} {tr('toolbar.last_scan_never')}")
        toolbar.addWidget(self.last_scan_label)

    def _setup_statusbar(self):
        """Setup the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Data source indicator
        self.source_status_label = QLabel(f"{tr('toolbar.data_source')} Auto")
        self.statusbar.addPermanentWidget(self.source_status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)

        # Status message
        self.statusbar.showMessage(tr("status.ready"))

    def _connect_signals(self):
        """Connect widget signals."""
        # Config panel
        self.config_panel.configChanged.connect(self._on_config_changed)
        self.config_panel.configReset.connect(self._on_config_reset)

        # Results table
        self.results_table.addToPortfolioRequested.connect(self._on_add_to_portfolio)

        # Portfolio panel
        self.portfolio_panel.portfolioChanged.connect(self._on_portfolio_changed)
        self.portfolio_panel.checkAlertsRequested.connect(self._on_check_portfolio)

    def _on_source_changed(self, index: int):
        """Handle data source change."""
        source_map = {
            0: DataSource.AUTO,
            1: DataSource.AKSHARE,
            2: DataSource.BAOSTOCK,
        }
        source = source_map.get(index, DataSource.AUTO)
        self.repository.set_data_source(source)
        self.source_status_label.setText(f"{tr('toolbar.data_source')} {source.value}")
        self.statusbar.showMessage(tr("status.source_changed", source=source.value), 3000)

    def _on_language_changed(self, index: int):
        """Handle language change."""
        lang = "zh" if index == 1 else "en"
        if lang != get_current_language():
            set_language(lang)
            self.config.language = lang
            self.settings_store.save(self.config)
            self._refresh_ui_texts()
            lang_name = "中文" if lang == "zh" else "English"
            self.statusbar.showMessage(tr("status.language_changed", language=lang_name), 3000)
            logger.info(f"Language changed to: {lang}")

    def _refresh_ui_texts(self):
        """Refresh all UI text after language change."""
        # Window title
        self.setWindowTitle(f"{tr('app_name')} v{APP_VERSION}")

        # Toolbar actions
        self.scan_action.setText(tr("toolbar.scan_stocks"))
        self.scan_action.setToolTip(tr("toolbar.scan_stocks_tip"))
        self.stop_action.setText(tr("toolbar.stop"))
        self.stop_action.setToolTip(tr("toolbar.stop_tip"))
        self.check_action.setText(tr("toolbar.check_portfolio"))
        self.check_action.setToolTip(tr("toolbar.check_portfolio_tip"))

        # Toolbar labels
        self.source_label.setText(tr("toolbar.data_source"))
        self.lang_label.setText(tr("toolbar.language"))
        self.source_combo.setToolTip(tr("toolbar.data_source_tip"))

        # Update data source combo items
        self.source_combo.blockSignals(True)
        current_source_idx = self.source_combo.currentIndex()
        self.source_combo.clear()
        self.source_combo.addItems([
            tr("data_sources.auto"),
            tr("data_sources.akshare"),
            tr("data_sources.baostock")
        ])
        self.source_combo.setCurrentIndex(current_source_idx)
        self.source_combo.blockSignals(False)

        # Tab titles
        self.tab_widget.setTabText(0, tr("tabs.results"))
        self.tab_widget.setTabText(1, tr("tabs.portfolio"))
        self.tab_widget.setTabText(2, tr("tabs.logs"))

        # Status bar
        current_source = self.repository.get_current_source()
        self.source_status_label.setText(f"{tr('toolbar.data_source')} {current_source.value}")
        self.statusbar.showMessage(tr("status.ready"))

        # Refresh child widgets
        self.config_panel.refresh_texts()
        self.results_table.refresh_texts()
        self.portfolio_panel.refresh_texts()
        self.log_viewer.refresh_texts()

    def _on_config_changed(self, config: AppConfig):
        """Handle config change."""
        self.config = config
        self.settings_store.save(config)
        self.statusbar.showMessage(tr("status.saved"), 3000)
        logger.info("Config updated and saved")

    def _on_config_reset(self):
        """Handle config reset."""
        self.config = self.settings_store.reset_to_defaults()
        self.statusbar.showMessage(tr("status.reset_defaults"), 3000)
        logger.info("Config reset to defaults")

    def _on_scan(self):
        """Start stock screening."""
        if self.screening_worker and self.screening_worker.isRunning():
            return

        self.config = self.config_panel.get_config()
        self.settings_store.save(self.config)

        self.screening_worker = ScreeningWorker(self.screener, self.config)
        self.screening_worker.progress.connect(self._on_screening_progress)
        self.screening_worker.finished.connect(self._on_screening_finished)
        self.screening_worker.error.connect(self._on_screening_error)

        # Update UI
        self.scan_action.setEnabled(False)
        self.stop_action.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_table.clear()
        self.tab_widget.setCurrentIndex(0)

        self.statusbar.showMessage(tr("status.screening"))
        self.screening_worker.start()
        logger.info("Screening started")

    def _on_stop(self):
        """Stop current screening."""
        if self.screening_worker:
            self.screening_worker.stop()
            self.statusbar.showMessage(tr("status.stopping"))

    def _on_screening_progress(self, current: int, total: int, message: str):
        """Handle screening progress update."""
        percent = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.statusbar.showMessage(tr("status.progress", current=current, total=total, message=message))
        # Update source label with current active source
        current_source = self.repository.get_current_source()
        self.source_status_label.setText(f"{tr('toolbar.data_source')} {current_source.value}")

    def _on_screening_finished(self, results):
        """Handle screening completion."""
        self.scan_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.results_table.set_results(results)
        self.last_scan_label.setText(f"{tr('toolbar.last_scan')} {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        self.statusbar.showMessage(tr("status.complete", count=len(results)), 5000)

        # Show notification
        self.notifier.show_screening_complete(len(results))
        logger.info(f"Screening finished with {len(results)} results")

    def _on_screening_error(self, error_msg: str):
        """Handle screening error."""
        self.scan_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, tr("dialogs.screening_error"), tr("dialogs.error_occurred", error=error_msg))
        self.statusbar.showMessage(tr("dialogs.screening_error"), 5000)
        logger.error(f"Screening failed: {error_msg}")

    def _on_check_portfolio(self):
        """Check portfolio for alerts."""
        if not self.portfolio or not self.portfolio.items:
            QMessageBox.information(self, tr("dialogs.check_portfolio"), tr("dialogs.portfolio_empty"))
            return

        if self.alert_worker and self.alert_worker.isRunning():
            return

        self.alert_worker = AlertWorker(self.alert_engine, self.portfolio, self.config)
        self.alert_worker.finished.connect(self._on_alert_check_finished)
        self.alert_worker.error.connect(self._on_alert_check_error)

        self.check_action.setEnabled(False)
        self.statusbar.showMessage(tr("status.checking"))
        self.alert_worker.start()
        logger.info("Alert check started")

    def _on_alert_check_finished(self, alerts, prices, yields):
        """Handle alert check completion."""
        self.check_action.setEnabled(True)

        alert_codes = [a.stock_code for a in alerts]
        self.portfolio_panel.update_market_data(prices, yields, alert_codes)
        self.tab_widget.setCurrentIndex(1)

        if alerts:
            self.notifier.show_multiple_alerts(alerts)
            self.statusbar.showMessage(tr("status.alerts_found", count=len(alerts)), 5000)
        else:
            self.statusbar.showMessage(tr("status.no_alerts"), 5000)

        logger.info(f"Alert check finished with {len(alerts)} alerts")

    def _on_alert_check_error(self, error_msg: str):
        """Handle alert check error."""
        self.check_action.setEnabled(True)
        QMessageBox.critical(self, tr("dialogs.alert_error"), tr("dialogs.error_occurred", error=error_msg))
        self.statusbar.showMessage(tr("dialogs.alert_error"), 5000)
        logger.error(f"Alert check failed: {error_msg}")

    def _on_add_to_portfolio(self, code: str, name: str):
        """Handle request to add stock to portfolio."""
        self.portfolio_panel.add_stock_with_info(code, name)
        self.tab_widget.setCurrentIndex(1)

    def _on_portfolio_changed(self):
        """Handle portfolio change."""
        self.portfolio = self.portfolio_panel.get_portfolio()
        if self.portfolio:
            self.portfolio_store.save(self.portfolio)
            self.statusbar.showMessage(tr("status.portfolio_saved"), 3000)
        logger.info("Portfolio updated and saved")

    def closeEvent(self, event):
        """Handle window close."""
        # Stop any running workers
        if self.screening_worker and self.screening_worker.isRunning():
            self.screening_worker.stop()
            self.screening_worker.wait()

        if self.alert_worker and self.alert_worker.isRunning():
            self.alert_worker.wait()

        # Save state
        self.settings_store.save(self.config)
        if self.portfolio:
            self.portfolio_store.save(self.portfolio)

        logger.info("Application closing")
        event.accept()
