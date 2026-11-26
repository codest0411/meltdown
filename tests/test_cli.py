"""Tests for CLI entry points, module execution, error handling, and mocked curses."""

import curses
import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

import meltdown
from meltdown import cli, game


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert meltdown.__version__ in captured.out


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "MELTDOWN" in captured.out
    assert "troubleshooting:" in captured.out
    assert "--version" in captured.out


def test_python_m_meltdown_runs_from_outside_repo(tmp_path):
    env = os.environ.copy()
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    env["PYTHONPATH"] = src_dir + os.pathsep + env.get("PYTHONPATH", "")

    res = subprocess.run(
        [sys.executable, "-m", "meltdown", "--version"],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert meltdown.__version__ in res.stdout


def test_run_handles_keyboard_interrupt_and_curses_error(capsys):
    with patch("meltdown.game.curses.wrapper", side_effect=KeyboardInterrupt):
        assert game.run() == 0
    assert "Station abandoned" in capsys.readouterr().out

    with patch("meltdown.game.curses.wrapper", side_effect=curses.error("too small")):
        assert game.run() == 1
    assert "Terminal error" in capsys.readouterr().err


def test_cli_handles_missing_curses_import(capsys):
    with patch.dict(sys.modules, {"meltdown.game": None}):
        code = cli.main([])
    assert code == 1
    assert "windows-curses" in capsys.readouterr().err


def test_game_main_menu_exits_cleanly_with_mocked_stdscr(tmp_path):
    stdscr = MagicMock()
    stdscr.getmaxyx.return_value = (30, 100)
    # Press Escape (27) on main menu to quit cleanly
    stdscr.getch.return_value = 27

    with patch("meltdown.game.curses.curs_set"), patch(
        "meltdown.game.curses.color_pair", return_value=0
    ):
        sm = game.SaveManager(data_dir=str(tmp_path))
        g = game.Game(stdscr, sm)
        assert g.main_menu() == "quit"
