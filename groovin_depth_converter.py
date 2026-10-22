"""Backward-compatible launcher for the refactored local application."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PROJECT_ROOT / "src"


def main() -> None:
    if str(SOURCE_ROOT) not in sys.path:
        sys.path.insert(0, str(SOURCE_ROOT))
    from depth_video_converter.ui import main as run_ui

    run_ui()


if __name__ == "__main__":
    main()
