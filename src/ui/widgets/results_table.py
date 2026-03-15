from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QAbstractItemView, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from src.models.stock import ScreeningResult
from src.i18n import tr


def get_results_columns():
    """Get translated column headers."""
    return [
        tr("columns.stock_code"),
        tr("columns.stock_name"),
        tr("columns.industry"),
        tr("columns.listing_years"),
        tr("columns.dividend_years"),
        tr("columns.avg_yield"),
        tr("columns.current_yield"),
        tr("columns.status"),
    ]


class ResultsTable(QWidget):
    """Table widget for displaying screening results."""

    addToPortfolioRequested = pyqtSignal(str, str)  # code, name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: List[ScreeningResult] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget()
        columns = get_results_columns()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Code
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Industry
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Listing Years
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Dividend Years
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 5Y Yield
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Current Yield
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Status

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        self.export_btn = QPushButton(tr("buttons.export_csv"))
        self.export_btn.clicked.connect(self._on_export)
        button_layout.addWidget(self.export_btn)

        self.add_portfolio_btn = QPushButton(tr("buttons.add_to_portfolio"))
        self.add_portfolio_btn.clicked.connect(self._on_add_to_portfolio)
        button_layout.addWidget(self.add_portfolio_btn)

        button_layout.addStretch()

        self.count_label = QPushButton(tr("table.stocks_count", count=0))
        self.count_label.setEnabled(False)
        self.count_label.setFlat(True)
        button_layout.addWidget(self.count_label)

        layout.addLayout(button_layout)

    def set_results(self, results: List[ScreeningResult]):
        """Set the screening results to display."""
        self._results = results
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(results))

        for row, result in enumerate(results):
            # Stock Code
            self.table.setItem(row, 0, QTableWidgetItem(result.stock.code))

            # Stock Name
            self.table.setItem(row, 1, QTableWidgetItem(result.stock.name))

            # Industry
            self.table.setItem(row, 2, QTableWidgetItem(result.stock.industry))

            # Listing Years
            item = QTableWidgetItem()
            item.setData(Qt.DisplayRole, result.listing_years)
            self.table.setItem(row, 3, item)

            # Dividend Years
            item = QTableWidgetItem()
            item.setData(Qt.DisplayRole, result.consecutive_dividend_years)
            self.table.setItem(row, 4, item)

            # 5Y Avg Yield
            item = QTableWidgetItem(f"{result.avg_5y_yield:.2f}")
            item.setData(Qt.UserRole, result.avg_5y_yield)
            self.table.setItem(row, 5, item)

            # Current Yield
            if result.current_yield is not None:
                item = QTableWidgetItem(f"{result.current_yield:.2f}")
                item.setData(Qt.UserRole, result.current_yield)
            else:
                item = QTableWidgetItem(tr("table.na"))
            self.table.setItem(row, 6, item)

            # Status
            status_item = QTableWidgetItem(result.status)
            if result.meets_all_criteria:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            self.table.setItem(row, 7, status_item)

        self.table.setSortingEnabled(True)
        self.count_label.setText(tr("table.stocks_count", count=len(results)))

    def clear(self):
        """Clear the table."""
        self._results = []
        self.table.setRowCount(0)
        self.count_label.setText(tr("table.stocks_count", count=0))

    def get_selected_stock(self) -> Optional[tuple]:
        """Get the selected stock code and name."""
        selected = self.table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        code = self.table.item(row, 0).text()
        name = self.table.item(row, 1).text()
        return code, name

    def _on_export(self):
        """Export results to CSV."""
        if not self._results:
            QMessageBox.information(self, tr("dialogs.export"), tr("dialogs.no_results"))
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, tr("dialogs.export_results"), "screening_results.csv", "CSV Files (*.csv)"
        )
        if not filename:
            return

        try:
            columns = get_results_columns()
            with open(filename, "w", encoding="utf-8-sig") as f:
                # Header
                f.write(",".join(columns) + "\n")

                # Data
                for result in self._results:
                    row = [
                        result.stock.code,
                        result.stock.name,
                        result.stock.industry,
                        str(result.listing_years),
                        str(result.consecutive_dividend_years),
                        f"{result.avg_5y_yield:.2f}",
                        f"{result.current_yield:.2f}" if result.current_yield else tr("table.na"),
                        result.status,
                    ]
                    f.write(",".join(row) + "\n")

            QMessageBox.information(self, tr("dialogs.export"), tr("dialogs.export_success", filename=filename))
        except Exception as e:
            QMessageBox.critical(self, tr("dialogs.export_error"), tr("dialogs.export_failed", error=str(e)))

    def _on_add_to_portfolio(self):
        """Handle add to portfolio button click."""
        selected = self.get_selected_stock()
        if not selected:
            QMessageBox.information(self, tr("buttons.add_to_portfolio"), tr("dialogs.select_stock"))
            return
        code, name = selected
        self.addToPortfolioRequested.emit(code, name)

    def refresh_texts(self):
        """Refresh all text for language change."""
        # Update column headers
        columns = get_results_columns()
        self.table.setHorizontalHeaderLabels(columns)

        # Update buttons
        self.export_btn.setText(tr("buttons.export_csv"))
        self.add_portfolio_btn.setText(tr("buttons.add_to_portfolio"))
        self.count_label.setText(tr("table.stocks_count", count=len(self._results)))
