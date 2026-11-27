"""Color themes and unlockable console skins for MELTDOWN."""

import curses

THEMES = {
    "cyber_cyan": {
        "name": "Cyber Cyan",
        "pairs": {
            1: curses.COLOR_GREEN,
            2: curses.COLOR_YELLOW,
            3: curses.COLOR_RED,
            4: curses.COLOR_CYAN,
            5: curses.COLOR_MAGENTA,
            6: curses.COLOR_WHITE,
        },
    },
    "classic_amber": {
        "name": "Classic Amber",
        "pairs": {
            1: curses.COLOR_YELLOW,
            2: curses.COLOR_YELLOW,
            3: curses.COLOR_RED,
            4: curses.COLOR_YELLOW,
            5: curses.COLOR_WHITE,
            6: curses.COLOR_YELLOW,
        },
    },
    "red_alert": {
        "name": "Red Alert",
        "pairs": {
            1: curses.COLOR_YELLOW,
            2: curses.COLOR_RED,
            3: curses.COLOR_RED,
            4: curses.COLOR_RED,
            5: curses.COLOR_MAGENTA,
            6: curses.COLOR_WHITE,
        },
    },
    "mono_hc": {
        "name": "Monochrome High-Contrast",
        "pairs": {
            1: curses.COLOR_WHITE,
            2: curses.COLOR_WHITE,
            3: curses.COLOR_WHITE,
            4: curses.COLOR_WHITE,
            5: curses.COLOR_WHITE,
            6: curses.COLOR_WHITE,
        },
    },
}

SKINS = {
    "default": {
        "name": "Orbital Standard",
        "req": None,
        "core": ("   .-===-.   ", "  / ( {s} ) \\  ", "  \\  '-'  /  ", "   '-===-'   "),
    },
    "sentinel": {
        "name": "Sentinel Matrix",
        "req": "boss_slayer",
        "core": ("  ╔═══╦═══╗  ", "  ║ ◄ {s} ► ║  ", "  ╚═══╩═══╝  ", "   [SYNTH]   "),
    },
    "singularity": {
        "name": "Singularity Core",
        "req": "all_bosses",
        "core": ("  .::/ \\::.  ", "  ::( {s} )::  ", "  '::\\ /::'  ", "  [QUANTUM]  "),
    },
    "nightmare": {
        "name": "Nightmare Reactor",
        "req": "nightmare_clear",
        "core": ("  /!\\===/!\\  ", "  | [{s} {s}] |  ", "  \\!/===/!\\  ", "  [INFERNO]  "),
    },
}


def apply_theme(theme_key: str) -> None:
    """Initialize curses color pairs for the selected theme."""
    theme = THEMES.get(theme_key, THEMES["cyber_cyan"])
    for idx, fg in theme["pairs"].items():
        try:
            curses.init_pair(idx, fg, -1)
        except curses.error:
            try:
                curses.init_pair(idx, fg, curses.COLOR_BLACK)
            except curses.error:
                pass
