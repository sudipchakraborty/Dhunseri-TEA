# cd '.\EdgeNode'
# .\.venv\Scripts\Activate.ps1

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    """Load the application stylesheet."""

    qss_path = (
        Path(__file__).parent
        / "ui"
        / "dark_theme.qss"
    )

    if qss_path.exists():
        with qss_path.open("r", encoding="utf-8") as file:
            app.setStyleSheet(file.read())
    else:
        print(f"Warning: Stylesheet not found: {qss_path}")


def main() -> None:
    """Application entry point."""

    app = QApplication(sys.argv)

    app.setApplicationName("Visual AI")
    app.setApplicationDisplayName("Visual AI Camera")
    app.setOrganizationName("Graphite India Limited")

    load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
