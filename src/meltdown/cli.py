"""Command-line interface for MELTDOWN."""

import argparse
import sys
from typing import List, Optional

from meltdown import __version__

EPILOG = """\
controls:
  Letters / numbers   Type your answer
  Enter               Submit answer
  Backspace           Delete character
  Esc                 Pause menu
  Tab                 Switch active player (Co-op mode)
  Ctrl+C              Quit

save data:
  Stored in ~/.meltdown/data.json (override with MELTDOWN_DATA_DIR).

troubleshooting:
  - Terminal too small: resize your terminal to at least 80x24.
  - Windows: if curses fails to import, install `windows-curses`.
  - Colors look wrong: ensure TERM supports 256 colors or toggle
    Colorblind Mode in Settings.
"""


def build_parser() -> argparse.ArgumentParser:
    """Create and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="meltdown",
        description=(
            "MELTDOWN — A fast-typing terminal survival game. "
            "Clear incoming alarms, manage stress and hull integrity, "
            "and survive bosses and endless dread."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for the `meltdown` command."""
    parser = build_parser()
    parser.parse_args(argv)

    try:
        from meltdown.game import run
    except ImportError as exc:
        print(
            f"Error: Failed to load terminal UI ({exc}).\n"
            "If you are on Windows, ensure `windows-curses` is installed:\n"
            "  pip install windows-curses",
            file=sys.stderr,
        )
        return 1

    return run()
