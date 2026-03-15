import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from src.ui.main_window import MainWindow
from src.utils.logger import get_logger
from src.utils.constants import APP_NAME

logger = get_logger(__name__)


def main():
    """Application entry point."""
    logger.info(f"Starting {APP_NAME}")

    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("Application started successfully")

    # Run event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
