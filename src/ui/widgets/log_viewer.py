from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QComboBox, QLabel, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat
from loguru import logger

from src.i18n import tr


class LogSignal(QObject):
    """Signal emitter for log messages."""
    log_message = pyqtSignal(str, str)  # message, level


class LogHandler:
    """Custom loguru handler that emits Qt signals."""

    def __init__(self, signal: LogSignal):
        self.signal = signal

    def write(self, message):
        record = message.record
        level = record["level"].name
        formatted = f"{record['time'].strftime('%H:%M:%S')} | {level:<8} | {record['name']}:{record['function']} - {record['message']}"
        self.signal.log_message.emit(formatted, level)


class LogViewer(QWidget):
    """Widget for viewing application logs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_log_handler()
        self._log_count = 0
        self._max_logs = 1000  # Keep last 1000 log entries

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()

        # Filter by level
        self.filter_label = QLabel(tr("log_viewer.filter"))
        toolbar.addWidget(self.filter_label)
        self.level_filter = QComboBox()
        self.level_filter.addItems([tr("log_viewer.all"), "DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_filter.setCurrentIndex(0)
        self.level_filter.currentTextChanged.connect(self._apply_filter)
        toolbar.addWidget(self.level_filter)

        toolbar.addStretch()

        # Clear button
        self.clear_btn = QPushButton(tr("log_viewer.clear"))
        self.clear_btn.clicked.connect(self._clear_logs)
        toolbar.addWidget(self.clear_btn)

        # Export button
        self.export_btn = QPushButton(tr("log_viewer.export"))
        self.export_btn.clicked.connect(self._export_logs)
        toolbar.addWidget(self.export_btn)

        # Auto-scroll checkbox
        self.auto_scroll_btn = QPushButton(tr("log_viewer.auto_scroll_on"))
        self.auto_scroll_btn.setCheckable(True)
        self.auto_scroll_btn.setChecked(True)
        self.auto_scroll_btn.clicked.connect(self._toggle_auto_scroll)
        toolbar.addWidget(self.auto_scroll_btn)

        layout.addLayout(toolbar)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: Consolas, Monaco, monospace;
                font-size: 10pt;
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
        """)
        layout.addWidget(self.log_text)

        # Status bar
        self.status_label = QLabel(tr("log_viewer.entries", count=0))
        layout.addWidget(self.status_label)

    def _setup_log_handler(self):
        """Setup custom log handler to capture logs."""
        self.log_signal = LogSignal()
        self.log_signal.log_message.connect(self._append_log)

        # Add custom handler to loguru
        self.handler_id = logger.add(
            LogHandler(self.log_signal).write,
            format="{message}",
            level="DEBUG",
        )

    def _get_level_color(self, level: str) -> QColor:
        """Get color for log level."""
        colors = {
            "DEBUG": QColor("#808080"),    # Gray
            "INFO": QColor("#4fc3f7"),     # Light blue
            "WARNING": QColor("#ffb74d"),  # Orange
            "ERROR": QColor("#ef5350"),    # Red
            "CRITICAL": QColor("#ff1744"), # Bright red
        }
        return colors.get(level, QColor("#d4d4d4"))

    def _append_log(self, message: str, level: str):
        """Append a log message to the viewer."""
        # Check filter
        current_filter = self.level_filter.currentText()
        all_text = tr("log_viewer.all")
        if current_filter != all_text:
            level_order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if level in level_order and current_filter in level_order:
                if level_order.index(level) < level_order.index(current_filter):
                    return

        # Apply color formatting
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt = QTextCharFormat()
        fmt.setForeground(self._get_level_color(level))

        cursor.insertText(message + "\n", fmt)

        self._log_count += 1
        self.status_label.setText(tr("log_viewer.entries", count=self._log_count))

        # Auto-scroll if enabled
        if self.auto_scroll_btn.isChecked():
            self.log_text.moveCursor(QTextCursor.End)

        # Trim old logs if exceeding max
        if self._log_count > self._max_logs:
            self._trim_logs()

    def _trim_logs(self):
        """Remove old log entries to prevent memory issues."""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.Start)
        # Remove first 100 lines
        for _ in range(100):
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        self._log_count -= 100

    def _apply_filter(self, level: str):
        """Apply log level filter (for future logs only)."""
        self.log_text.append(tr("log_viewer.filter_changed", level=level))

    def _clear_logs(self):
        """Clear all logs."""
        self.log_text.clear()
        self._log_count = 0
        self.status_label.setText(tr("log_viewer.entries", count=0))

    def _export_logs(self):
        """Export logs to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, tr("dialogs.export_logs"), f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.log_text.toPlainText())

    def _toggle_auto_scroll(self):
        """Toggle auto-scroll."""
        if self.auto_scroll_btn.isChecked():
            self.auto_scroll_btn.setText(tr("log_viewer.auto_scroll_on"))
        else:
            self.auto_scroll_btn.setText(tr("log_viewer.auto_scroll_off"))

    def add_manual_log(self, message: str, level: str = "INFO"):
        """Add a log entry manually."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"{timestamp} | {level:<8} | UI - {message}"
        self._append_log(formatted, level)

    def refresh_texts(self):
        """Refresh all text for language change."""
        self.filter_label.setText(tr("log_viewer.filter"))
        self.clear_btn.setText(tr("log_viewer.clear"))
        self.export_btn.setText(tr("log_viewer.export"))
        self.status_label.setText(tr("log_viewer.entries", count=self._log_count))

        # Update auto-scroll button
        if self.auto_scroll_btn.isChecked():
            self.auto_scroll_btn.setText(tr("log_viewer.auto_scroll_on"))
        else:
            self.auto_scroll_btn.setText(tr("log_viewer.auto_scroll_off"))

        # Update filter combo (keep current selection)
        current_idx = self.level_filter.currentIndex()
        self.level_filter.blockSignals(True)
        self.level_filter.clear()
        self.level_filter.addItems([tr("log_viewer.all"), "DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_filter.setCurrentIndex(current_idx)
        self.level_filter.blockSignals(False)

    def closeEvent(self, event):
        """Clean up handler on close."""
        try:
            logger.remove(self.handler_id)
        except:
            pass
        event.accept()
