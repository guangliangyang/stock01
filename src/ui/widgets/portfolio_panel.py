from typing import List, Dict, Optional
from datetime import date
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QSpinBox, QDateEdit, QDialogButtonBox,
    QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QColor

from src.models.portfolio import Portfolio, PortfolioItem
from src.i18n import tr


def get_portfolio_columns():
    """Get translated column headers."""
    return [
        tr("columns.stock_code"),
        tr("columns.stock_name"),
        tr("columns.buy_price"),
        tr("columns.buy_date"),
        tr("columns.quantity"),
        tr("columns.current_price"),
        tr("columns.current_yield"),
        tr("columns.status"),
    ]


class AddStockDialog(QDialog):
    """Dialog for adding a stock to portfolio."""

    def __init__(self, code: str = "", name: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dialogs.add_stock"))
        self.setMinimumWidth(350)

        layout = QFormLayout(self)

        # Stock code
        self.code_edit = QLineEdit(code)
        self.code_edit.setMaxLength(6)
        self.code_label = QLabel(tr("add_stock_dialog.stock_code"))
        layout.addRow(self.code_label, self.code_edit)

        # Stock name
        self.name_edit = QLineEdit(name)
        self.name_label = QLabel(tr("add_stock_dialog.stock_name"))
        layout.addRow(self.name_label, self.name_edit)

        # Buy price
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0.01, 99999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setSuffix(tr("add_stock_dialog.price_suffix"))
        self.price_label = QLabel(tr("add_stock_dialog.buy_price"))
        layout.addRow(self.price_label, self.price_spin)

        # Buy date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_label = QLabel(tr("add_stock_dialog.buy_date"))
        layout.addRow(self.date_label, self.date_edit)

        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 9999999)
        self.quantity_spin.setValue(100)
        self.quantity_spin.setSuffix(tr("add_stock_dialog.quantity_suffix"))
        self.quantity_label = QLabel(tr("add_stock_dialog.quantity"))
        layout.addRow(self.quantity_label, self.quantity_spin)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> Optional[PortfolioItem]:
        """Get the portfolio item data."""
        code = self.code_edit.text().strip()
        name = self.name_edit.text().strip()

        if not code or not name:
            return None

        return PortfolioItem(
            stock_code=code,
            stock_name=name,
            buy_price=self.price_spin.value(),
            buy_date=self.date_edit.date().toPyDate(),
            quantity=self.quantity_spin.value(),
        )


class PortfolioPanel(QWidget):
    """Panel for managing user portfolio."""

    portfolioChanged = pyqtSignal()
    checkAlertsRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._portfolio: Optional[Portfolio] = None
        self._current_prices: Dict[str, float] = {}
        self._current_yields: Dict[str, float] = {}
        self._alert_codes: List[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget()
        columns = get_portfolio_columns()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton(tr("buttons.add_stock"))
        self.add_btn.clicked.connect(self._on_add)
        button_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton(tr("buttons.remove_stock"))
        self.remove_btn.clicked.connect(self._on_remove)
        button_layout.addWidget(self.remove_btn)

        self.check_alerts_btn = QPushButton(tr("buttons.check_alerts"))
        self.check_alerts_btn.clicked.connect(self._on_check_alerts)
        button_layout.addWidget(self.check_alerts_btn)

        button_layout.addStretch()

        self.count_label = QPushButton(tr("table.stocks_count", count=0))
        self.count_label.setEnabled(False)
        self.count_label.setFlat(True)
        button_layout.addWidget(self.count_label)

        layout.addLayout(button_layout)

    def set_portfolio(self, portfolio: Portfolio):
        """Set the portfolio to display."""
        self._portfolio = portfolio
        self._refresh_table()

    def update_market_data(
        self,
        prices: Dict[str, float],
        yields: Dict[str, float],
        alert_codes: List[str]
    ):
        """Update market data for display."""
        self._current_prices = prices
        self._current_yields = yields
        self._alert_codes = alert_codes
        self._refresh_table()

    def _refresh_table(self):
        """Refresh the table display."""
        if not self._portfolio:
            self.table.setRowCount(0)
            self.count_label.setText(tr("table.stocks_count", count=0))
            return

        items = self._portfolio.items
        self.table.setRowCount(len(items))

        for row, item in enumerate(items):
            # Stock Code
            self.table.setItem(row, 0, QTableWidgetItem(item.stock_code))

            # Stock Name
            self.table.setItem(row, 1, QTableWidgetItem(item.stock_name))

            # Buy Price
            self.table.setItem(row, 2, QTableWidgetItem(f"{item.buy_price:.2f}"))

            # Buy Date
            self.table.setItem(row, 3, QTableWidgetItem(item.buy_date.isoformat()))

            # Quantity
            qty_item = QTableWidgetItem()
            qty_item.setData(Qt.DisplayRole, item.quantity)
            self.table.setItem(row, 4, qty_item)

            # Current Price
            current_price = self._current_prices.get(item.stock_code)
            if current_price:
                self.table.setItem(row, 5, QTableWidgetItem(f"{current_price:.2f}"))
            else:
                self.table.setItem(row, 5, QTableWidgetItem(tr("table.no_data")))

            # Current Yield
            current_yield = self._current_yields.get(item.stock_code)
            if current_yield:
                self.table.setItem(row, 6, QTableWidgetItem(f"{current_yield:.2f}"))
            else:
                self.table.setItem(row, 6, QTableWidgetItem(tr("table.no_data")))

            # Status
            is_alert = item.stock_code in self._alert_codes
            status_item = QTableWidgetItem(tr("table.alert") if is_alert else tr("table.ok"))
            if is_alert:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
                status_item.setForeground(QColor(200, 0, 0))  # Dark red
            else:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            self.table.setItem(row, 7, status_item)

        self.count_label.setText(tr("table.stocks_count", count=len(items)))

    def _on_add(self):
        """Handle add stock button."""
        dialog = AddStockDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            item = dialog.get_data()
            if item:
                if self._portfolio:
                    self._portfolio.add_item(item)
                else:
                    self._portfolio = Portfolio(items=[item])
                self._refresh_table()
                self.portfolioChanged.emit()

    def add_stock_with_info(self, code: str, name: str):
        """Open add dialog with pre-filled code and name."""
        dialog = AddStockDialog(code=code, name=name, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            item = dialog.get_data()
            if item:
                if self._portfolio:
                    self._portfolio.add_item(item)
                else:
                    self._portfolio = Portfolio(items=[item])
                self._refresh_table()
                self.portfolioChanged.emit()

    def _on_remove(self):
        """Handle remove stock button."""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(self, tr("dialogs.remove_stock"), tr("dialogs.select_stock"))
            return

        row = selected[0].row()
        code = self.table.item(row, 0).text()
        name = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self,
            tr("dialogs.remove_stock"),
            tr("dialogs.remove_confirm", name=name, code=code),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes and self._portfolio:
            self._portfolio.remove_item(code)
            self._refresh_table()
            self.portfolioChanged.emit()

    def _on_check_alerts(self):
        """Handle check alerts button."""
        self.checkAlertsRequested.emit()

    def get_portfolio(self) -> Optional[Portfolio]:
        """Get the current portfolio."""
        return self._portfolio

    def clear_alerts(self):
        """Clear alert highlighting."""
        self._alert_codes = []
        self._refresh_table()

    def refresh_texts(self):
        """Refresh all text for language change."""
        # Update column headers
        columns = get_portfolio_columns()
        self.table.setHorizontalHeaderLabels(columns)

        # Update buttons
        self.add_btn.setText(tr("buttons.add_stock"))
        self.remove_btn.setText(tr("buttons.remove_stock"))
        self.check_alerts_btn.setText(tr("buttons.check_alerts"))

        # Update count label
        count = len(self._portfolio.items) if self._portfolio else 0
        self.count_label.setText(tr("table.stocks_count", count=count))

        # Refresh table to update status text
        self._refresh_table()
