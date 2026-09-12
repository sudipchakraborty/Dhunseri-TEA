import os
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"


def use_project_python() -> None:
    """Restart with the bundled environment when another Python is active."""

    if not VENV_PYTHON.exists():
        return
    if Path(sys.executable).resolve() == VENV_PYTHON.resolve():
        return
    os.execv(
        str(VENV_PYTHON),
        [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
    )


use_project_python()

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    """Load the application stylesheet."""

    qss_path = (
        PROJECT_DIR
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

    app.setApplicationName("TeaVision Edge")
    app.setApplicationDisplayName("TeaVision Edge")
    app.setOrganizationName("TeaVision")

    load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
