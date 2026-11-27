"""Command-line interface for MELTDOWN."""

import argparse
import os
import subprocess
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

commands:
  meltdown            Launch the game
  meltdown --record   Launch and export an animated SVG replay on exit
  meltdown setup-shell  Configure PowerShell/shell alias for `meltdown`

save data:
  Stored in ~/.meltdown/data.json (override with MELTDOWN_DATA_DIR).

troubleshooting:
  - Terminal too small: resize your terminal to at least 80x24.
  - Windows: if `meltdown.exe` is blocked by Application Control, run
    `meltdown setup-shell` or `python -m meltdown`.
  - Colors look wrong: ensure TERM supports 256 colors or toggle
    Colorblind Mode in Settings.
"""


def setup_shell(profile_path: Optional[str] = None) -> int:
    """Configure a shell function/alias so `meltdown` invokes `python -m meltdown`."""
    if sys.platform == "win32":
        if not profile_path:
            try:
                out = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command", "$PROFILE"],
                    stdin=subprocess.DEVNULL,
                    text=True,
                    timeout=5,
                ).strip()
                profile_path = out
            except Exception:
                profile_path = os.path.join(
                    os.path.expanduser("~"),
                    "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1",
                )
        line = "function meltdown { python -m meltdown @args }"
        os.makedirs(os.path.dirname(os.path.abspath(profile_path)), exist_ok=True)
        existing = ""
        if os.path.exists(profile_path):
            with open(profile_path, encoding="utf-8") as f:
                existing = f.read()
        if "python -m meltdown" not in existing:
            with open(profile_path, "a", encoding="utf-8") as f:
                f.write(f"\n{line}\n")
            print(f"Added `meltdown` function to PowerShell profile:\n  {profile_path}")
        else:
            print(f"`meltdown` is already configured in:\n  {profile_path}")
        print("Restart PowerShell (or run `. $PROFILE`) and then run `meltdown`.")
        return 0

    print("Add this line to your ~/.bashrc or ~/.zshrc:")
    print("  alias meltdown='python3 -m meltdown'")
    return 0


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
    parser.add_argument(
        "--record",
        nargs="?",
        const="AUTO",
        default=None,
        metavar="PATH",
        help="Export an animated SVG replay of your run (default: ~/.meltdown/last_run.svg)",
    )
    parser.add_argument(
        "subcommand",
        nargs="?",
        choices=["setup-shell"],
        help="Optional utility command (e.g. `setup-shell`)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for the `meltdown` command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "setup-shell":
        return setup_shell()

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

    return run(record_path=args.record)
