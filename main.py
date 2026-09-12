"""Convenient repository-root launcher for TeaVision Edge."""

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
EDGE_ENTRYPOINT = PROJECT_ROOT / "EdgeNode" / "main.py"
VENV_PYTHON = PROJECT_ROOT / "EdgeNode" / ".venv" / "Scripts" / "python.exe"


def main() -> None:
    if not VENV_PYTHON.exists():
        raise SystemExit(
            "TeaVision's Python environment is missing from EdgeNode\\.venv."
        )
    os.execv(
        str(VENV_PYTHON),
        [str(VENV_PYTHON), str(EDGE_ENTRYPOINT), *sys.argv[1:]],
    )


if __name__ == "__main__":
    main()
