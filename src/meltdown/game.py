#!/usr/bin/env python3
"""
MELTDOWN v3.0 — Orbital Command Terminal Survival Game.

Modular entry point orchestrating alarms, bosses, audio, themes,
LAN multiplayer, ghost replays, perks, hazards, and the curses cockpit.
"""

import collections
import curses
import hashlib
import random
import sys
import time
from datetime import date

from meltdown.alarms import (
    ALARM_MANUAL,
    ALL_KINDS,
    MORSE,
    POWERUP_TYPES,
    SHORT_WORDS,
    WORDS,
    WORDS_EASY,
    WORDS_HARD,
    WORDS_MED,
    Alarm,
)
from meltdown.audio import Sound
from meltdown.bosses import BOSS_AFTER_LEVEL, BOSSES
from meltdown.lan import (
    get_local_ip,
    host_lan_handshake,
    join_lan_handshake,
    recv_json,
    send_json,
)
from meltdown.save import (
    ACH_DEFS,
    DEFAULT_DATA,
    DEFAULT_SETTINGS,
    SAVE_DIR,
    SAVE_FILE,
    SaveManager,
    Stats,
    compute_rank,
    format_run_card,
    get_save_dir,
)
from meltdown.themes import SKINS, THEMES, apply_theme

# Re-export symbols for backwards compatibility
__all__ = [
    "ALL_KINDS", "DIFFICULTY", "LEVELS", "MORSE", "POWERUP_TYPES",
    "WORDS", "WORDS_EASY", "WORDS_MED", "WORDS_HARD", "SHORT_WORDS",
    "Alarm", "SaveManager", "Stats", "Sound", "Game",
    "daily_seed", "level_cfg", "run", "main",
    "SAVE_DIR", "SAVE_FILE", "DEFAULT_DATA", "DEFAULT_SETTINGS", "get_save_dir",
]

# ═══════════════════════════════════════════════════════════════════════════════
#  LEVELS, DIFFICULTY, PERKS & MUTATORS
# ═══════════════════════════════════════════════════════════════════════════════

LEVELS = [
    ("BOOT SEQUENCE",  "Easy does it. Systems warming up...",
     6, 3.5, 14, 2, 0.8, ["type", "logic"], False, False),
    ("COOLANT LEAK",   "Things are getting slippery.",
     8, 3.0, 12, 3, 1.0, ["type", "reverse", "typo"], False, False),
    ("PRESSURE SPIKE", "Your calculator hand better be ready.",
     10, 2.6, 11, 3, 1.1, ["type", "reverse", "math", "sequence", "mash"], False, False),
    ("SOLAR FLARE",    "Displays will get corrupted. Squint.",
     12, 2.3, 10, 4, 1.2, ["type", "reverse", "math", "scramble", "binary", "hex"], True, False),
    ("BLACKOUT",       "Memorize codes before they vanish!",
     14, 2.0, 9, 4, 1.3, ["type", "reverse", "math", "scramble", "memory", "morse", "port"], True, False),
    ("CORE BREACH",    "Alarm surges incoming. Breathe. Or don't.",
     16, 1.7, 8, 5, 1.4, ["type", "reverse", "math", "scramble", "memory", "decode", "hex", "logic"], True, True),
    ("TOTAL MELTDOWN", "Nobody has survived this. Good luck.",
     20, 1.4, 7, 6, 1.6, ALL_KINDS, True, True),
]

DIFFICULTY = {
    "casual":    {"spawn": 1.5, "ttl": 1.4, "stress": 0.6,
                  "hull_dmg": 10, "pup": 0.15, "label": "CASUAL"},
    "operator":  {"spawn": 1.0, "ttl": 1.0, "stress": 1.0,
                  "hull_dmg": 15, "pup": 0.08, "label": "OPERATOR"},
    "nightmare": {"spawn": 0.7, "ttl": 0.75, "stress": 1.4,
                  "hull_dmg": 20, "pup": 0.04, "label": "NIGHTMARE"},
}

PERKS = {
    "auto_coolant":  ("Auto-Coolant",        "-1.5 stress/s when < 2 alarms active"),
    "bulkhead":      ("Reinforced Bulkhead", "-5% hull damage per missed alarm"),
    "buffer_shield": ("Buffer Shield",       "First wrong Enter per level keeps combo"),
    "quick_fingers": ("Quick Fingers",       "+15% score for answers under 1.5s"),
    "pup_magnet":    ("Power-up Magnet",     "More power-ups & 7s FREEZE duration"),
}

MUTATORS = {
    "none":         ("None",         "Standard rules"),
    "glass_cannon": ("Glass Cannon", "1 HP hull, 2x score multiplier"),
    "blindfold":    ("Blindfold",    "All alarms hide after 1.5s"),
    "turbo":        ("Turbo",        "1.5x speed, 1.5x combo multiplier"),
}

STORY = [
    ["[INCOMING TRANSMISSION]", "",
     "\"This is Control. The other operators...\"",
     "\"They didn't make it. You're on your own.\"", "",
     "\"Keep the core stable. We're sending help.\""],
    ["[SYSTEM ALERT]", "",
     "Coolant reserves critical.",
     "Rerouting auxiliary power to containment.", "",
     "The walls are getting warmer."],
    ["[TRANSMISSION - STATIC]", "",
     "\"We... *static*... reading massive energy spike...\"",
     "\"Something is in the system. Be ready.\""],
    ["[PROXIMITY ALERT]", "",
     "Unidentified signal detected on all frequencies.",
     "The station's lights are flickering.", "",
     "Whatever it is, it's getting closer."],
    ["[CREW LOG - AUTOMATED]", "",
     "Station integrity at minimum threshold.",
     "Automated distress beacon activated.", "",
     "No response from Control for 47 minutes."],
    ["[FINAL TRANSMISSION]", "",
     "\"If you're still alive in there...\"",
     "\"The core is going critical.\"", "",
     "\"You know what to do. It's all on you now.\""],
    ["[VICTORY]", "",
     "\"By some miracle, you held it together.\"",
     "\"The station is yours. The core is stable.\"", "",
     "\"...for now.\""],
]

CHOICES = {
    1: {"prompt": "REROUTE REMAINING POWER?",
        "opts": [("SHIELDS: +15 hull integrity", "hull", 15),
                 ("SENSORS: +1s alarm time next level", "ttl_bonus", 1.0),
                 ("WEAPONS: +500 score bonus", "score", 500)]},
    3: {"prompt": "EMERGENCY PROTOCOL?",
        "opts": [("LOCKDOWN: -20 stress", "stress", -20),
                 ("OVERDRIVE: 1.5x score next level", "score_mult", 1.5),
                 ("VENT: +10 hull", "hull", 10)]},
    5: {"prompt": "FINAL STAND?",
        "opts": [("FORTIFY: +25 hull", "hull", 25),
                 ("FOCUS: -40 stress", "stress", -40),
                 ("OVERCLOCK: extra power-up chance", "pup_bonus", 0.10)]},
}


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def level_cfg(i):
    if i < len(LEVELS):
        return LEVELS[i]
    n = i - len(LEVELS) + 1
    return (f"ENDLESS DREAD {n}", "There is no escape. Only the score.",
            20 + 2 * n, max(0.8, 1.4 - 0.08 * n), max(4.5, 7 - 0.3 * n),
            6, 1.6 + 0.1 * n, ALL_KINDS, True, True)


def daily_seed():
    return int(hashlib.md5(date.today().isoformat().encode()).hexdigest(), 16) % (2**31)


def encode_sandbox_code(seed: int, start_lvl: int, mutator: str) -> str:
    """Create a short shareable Sandbox config code."""
    m_code = {"none": "N", "glass_cannon": "G", "blindfold": "B", "turbo": "T"}.get(mutator, "N")
    return f"SBX-{seed % 100000:05d}-L{start_lvl + 1}-{m_code}"


def decode_sandbox_code(code: str):
    """Parse SBX-XXXXX-LY-M into (seed, start_lvl_idx, mutator) or None."""
    try:
        parts = code.strip().upper().split("-")
        if len(parts) != 4 or parts[0] != "SBX":
            return None
        seed = int(parts[1])
        lvl = max(0, min(20, int(parts[2].lstrip("L")) - 1))
        mut = {"N": "none", "G": "glass_cannon", "B": "blindfold", "T": "turbo"}.get(parts[3], "none")
        return seed, lvl, mut
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#  GAME
# ═══════════════════════════════════════════════════════════════════════════════

class Game:
    def __init__(self, s, save_mgr):
        self.s = s
        self.sm = save_mgr
        self.score = 0
        self.combo = 0
        self.stress = 0.0
        self.hull = 100.0
        self.h, self.w = s.getmaxyx()
        self.diff = "operator"
        self.mode = "solo"       # solo, coop, versus, boss_rush, practice, sandbox, lan
        self.mutator = "none"
        self.perks = set()
        self.stats = Stats()
        self.ach_queue = []
        self.ttl_bonus = 0.0
        self.score_mult = 1.0
        self.pup_bonus = 0.0
        self.freeze_until = 0.0
        self.shake_until = 0.0
        self.daily = False
        self.recent_prompts = collections.deque(maxlen=15)
        self.event_log = collections.deque(maxlen=5)
        self.ghost_timeline = []
        self._last_ghost_t = -1.0
        self._last_warn_beep = 0.0
        # co-op state
        self.active_p = 0
        self.p_combos = [0, 0]
        self.p_scores = [0, 0]
        self.p_bufs = ["", ""]

    # ── drawing helpers ─────────────────────────────────────────────────────

    def put(self, y, x, text, attr=0):
        try:
            if 0 <= y < self.h and x < self.w:
                self.s.addstr(y, max(0, x), text[:max(0, self.w - x - 1)], attr)
        except curses.error:
            pass

    def center(self, y, text, attr=0):
        self.put(y, max(0, (self.w - len(text)) // 2), text, attr)

    def bar(self, y, x, label, frac, width, col, show_num=False):
        frac = max(0.0, min(1.0, frac))
        filled = int(frac * width)
        self.put(y, x, label)
        if self.sm.settings.get("ascii_bars", False):
            fill_ch, empty_ch = "#", "-"
        else:
            fill_ch, empty_ch = "\u2588", "\u2591"
        bar_text = "[" + fill_ch * filled + empty_ch * (width - filled) + "]"
        if show_num and self.sm.settings.get("show_timer_numbers", True):
            bar_text += f" {frac * 100:3.0f}%"
        self.put(y, x + len(label), bar_text, col)

    def box(self, y, x, h, w, title="", col=0, double=False):
        if h < 3 or w < 4:
            return
        if double:
            tl, hz, tr, vt, bl, br = "\u2554", "\u2550", "\u2557", "\u2551", "\u255a", "\u255d"
        else:
            tl, hz, tr, vt, bl, br = "\u250c", "\u2500", "\u2510", "\u2502", "\u2514", "\u2518"
        self.put(y, x, tl + hz * (w - 2) + tr, col)
        for row in range(y + 1, y + h - 1):
            self.put(row, x, vt, col)
            self.put(row, x + w - 1, vt, col)
        self.put(y + h - 1, x, bl + hz * (w - 2) + br, col)
        if title and w > len(title) + 6:
            badge = f" {title} "
            self.put(y, x + 2, badge, col | curses.A_BOLD)

    def _log_event(self, text, col=0):
        self.event_log.append((text, col))

    def _check_min_size(self):
        """Show friendly overlay if terminal is smaller than 80x24."""
        self.h, self.w = self.s.getmaxyx()
        if self.w < 60 or self.h < 18:
            self.s.erase()
            self.center(max(0, self.h // 2 - 1), "TERMINAL TOO SMALL", self.C(3) | curses.A_BOLD)
            self.center(max(1, self.h // 2 + 1), f"Need at least 80x24 (now {self.w}x{self.h})", self.C(2))
            self.s.refresh()
            return False
        return True

    def _draw_reactor_core(self, y, x, w, now, frozen):
        if w < 22:
            return
        pulse = int(now * (6 if self.stress > 75 else 2)) % 2 == 0
        if frozen:
            core_col = self.C(4) | curses.A_BOLD
            sym, state = ("*" if pulse else "+"), "CRYO LOCK"
        elif self.stress > 80 or self.hull < 25:
            core_col = self.C(3) | curses.A_BOLD
            sym, state = ("!" if pulse else "X"), "CRITICAL"
        elif self.stress > 50 or self.hull < 55:
            core_col = self.C(2) | curses.A_BOLD
            sym, state = ("#" if pulse else "="), "ELEVATED"
        else:
            core_col = self.C(1) | curses.A_BOLD
            sym, state = ("O" if pulse else "o"), "NOMINAL"

        skin_key = self.sm.settings.get("skin", "default")
        skin = SKINS.get(skin_key, SKINS["default"])
        if skin["req"] and not self.sm.has_ach(skin["req"]):
            skin = SKINS["default"]

        cx = x + max(1, (w - 13) // 2)
        for i, line in enumerate(skin["core"]):
            self.put(y + i, cx, line.format(s=sym), core_col)
        lbl = f"CORE: {state}"
        self.put(y + 4, x + max(1, (w - len(lbl)) // 2), lbl, core_col)

    def _cb(self, frac):
        if not self.sm.settings.get("colorblind", False):
            return ""
        if frac > 0.5:
            return "+"
        elif frac > 0.25:
            return "~"
        return "!"

    def animate_transition(self, label="ENGAGING SECTOR"):
        """Brief animated warp-line transition between levels."""
        if self.sm.settings.get("reduced_flash", False):
            return
        self.h, self.w = self.s.getmaxyx()
        for step in range(4):
            self.s.erase()
            bar = "=" * min(self.w - 4, (step + 1) * max(6, self.w // 5))
            self.center(self.h // 2 - 1, bar, self.C(4) | curses.A_BOLD)
            self.center(self.h // 2, label, self.C(2) | curses.A_BOLD)
            self.center(self.h // 2 + 1, bar, self.C(4) | curses.A_BOLD)
            self.s.refresh()
            time.sleep(0.06)

    def screen(self, lines, wait_key=True):
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()
        box_w = min(self.w - 4, max(46, max((len(t) for t, _ in lines), default=30) + 8))
        box_h = min(self.h - 2, len(lines) + 4)
        bx = max(1, (self.w - box_w) // 2)
        by = max(1, (self.h - box_h) // 2)
        self.box(by, bx, box_h, box_w, "ORBITAL COMMAND :: TRANSMISSION", self.C(4), double=True)
        top = by + 2
        for i, (txt, attr) in enumerate(lines):
            if top + i < by + box_h - 1:
                self.center(top + i, txt, attr)
        self.s.refresh()
        if wait_key:
            self.s.nodelay(False)
            self.s.getch()
            self.s.nodelay(True)
        else:
            time.sleep(1.5)
        curses.flushinp()

    def C(self, n):
        try:
            return curses.color_pair(n)
        except Exception:
            return 0

    # ── menus ───────────────────────────────────────────────────────────────

    def menu(self, title, options, subtitle="", hints=None, banner=None):
        sel = 0
        self.s.nodelay(False)
        curses.curs_set(0)
        while True:
            self.s.erase()
            self.h, self.w = self.s.getmaxyx()
            banner_h = len(banner) + 1 if banner else 0
            hint_h = 2 if hints else 0
            box_w = min(
                self.w - 4,
                max(
                    58,
                    len(subtitle) + 6,
                    *(len(o) + 14 for o in options),
                    *(len(b) + 6 for b in (banner or [])),
                ),
            )
            box_h = min(self.h - 2, len(options) + 9 + banner_h + hint_h)
            bx = max(1, (self.w - box_w) // 2)
            by = max(1, (self.h - box_h) // 2)

            self.box(by, bx, box_h, box_w, "ORBITAL COMMAND OS :: v3.0", self.C(4), double=True)
            cur_y = by + 2
            if banner:
                for b_line in banner:
                    self.center(cur_y, b_line, self.C(3) | curses.A_BOLD)
                    cur_y += 1
                cur_y += 1
            else:
                self.center(cur_y, f"[ {title} ]", self.C(3) | curses.A_BOLD)
                cur_y += 1

            if subtitle:
                self.center(cur_y, subtitle, self.C(4))
                cur_y += 1
            self.put(cur_y, bx + 2, "\u2500" * (box_w - 4), self.C(4))
            cur_y += 1

            for i, opt in enumerate(options):
                if cur_y + i >= by + box_h - (2 + hint_h):
                    break
                if i == sel:
                    label = f" \u25b8  {opt}  \u25c2 "
                    attr = self.C(4) | curses.A_REVERSE | curses.A_BOLD
                else:
                    label = f"    {opt}    "
                    attr = 0
                self.center(cur_y + i, label, attr)

            if hints and 0 <= sel < len(hints):
                hy = by + box_h - 3
                self.put(hy, bx + 2, "\u2500" * (box_w - 4), self.C(4))
                self.center(hy + 1, hints[sel], self.C(2))

            self.center(min(self.h - 1, by + box_h + 1),
                        "[Up/Down] Navigate   [Enter] Select   [Esc] Back", self.C(4))
            self.s.refresh()
            ch = self.s.getch()
            if ch == curses.KEY_UP:
                sel = (sel - 1) % len(options)
            elif ch == curses.KEY_DOWN:
                sel = (sel + 1) % len(options)
            elif ch in (10, 13, curses.KEY_ENTER):
                curses.curs_set(1)
                return sel
            elif ch == 27:
                curses.curs_set(1)
                return -1

    def prompt_text(self, title, prompt, max_len=30, alpha_only=False):
        buf = ""
        self.s.nodelay(False)
        while True:
            self.s.erase()
            self.h, self.w = self.s.getmaxyx()
            bw = min(self.w - 4, 54)
            bh = 9
            bx = max(1, (self.w - bw) // 2)
            by = max(1, (self.h - bh) // 2)
            self.box(by, bx, bh, bw, title, self.C(4), double=True)
            self.center(by + 2, prompt, self.C(2) | curses.A_BOLD)
            self.center(by + 4, f"> {buf}_", curses.A_BOLD)
            self.center(by + 6, "[Enter] Confirm   [Esc] Cancel", self.C(4))
            self.s.refresh()
            ch = self.s.getch()
            if ch == 27:
                return None
            if ch in (10, 13, curses.KEY_ENTER) and len(buf) >= 1:
                return buf
            elif ch in (8, 127, curses.KEY_BACKSPACE):
                buf = buf[:-1]
            elif 32 <= ch < 127 and len(buf) < max_len:
                c = chr(ch)
                if not alpha_only or c.isalpha():
                    buf += c

    def get_initials(self):
        res = self.prompt_text("RECORD QUALIFIED", "NEW TOP-10 HIGH SCORE! Enter 1-3 letters:",
                               max_len=3, alpha_only=True)
        return (res or "OPR").upper()[:3]

    # ── main menu ───────────────────────────────────────────────────────────

    def main_menu(self):
        banner = [
            "███╗   ███╗███████╗██╗  ████████╗██████╗  ██████╗ ██╗    ██╗███╗   ██╗",
            "████╗ ████║██╔════╝██║  ╚══██╔══╝██╔══██╗██╔═══██╗██║    ██║████╗  ██║",
            "██╔████╔██║█████╗  ██║     ██║   ██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║",
            "██║╚██╔╝██║██╔══╝  ██║     ██║   ██║  ██║██║   ██║██║███╗██║██║╚██╗██║",
            "██║ ╚═╝ ██║███████╗███████╗██║   ██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║",
        ]
        hint_map = {
            "New Game": "Solo, Co-op, Versus, Boss Rush, Practice, Sandbox, or LAN",
            "Continue": "Resume your auto-saved station shift",
            "Daily Challenge": "Today's global seeded 5-level gauntlet",
            "Field Manual": "Encyclopedia & examples for all 15 alarm types",
            "Leaderboard": "Top 10 operator scores and today's daily best",
            "Achievements": "View all 19 station commendations",
            "Statistics": "Lifetime accuracy, speed, and mission totals",
            "Settings": "Audio, themes, skins, colorblind mode & accessibility",
            "Quit": "Power down the orbital console",
        }
        while True:
            opts = ["New Game"]
            has_save = self.sm.load_state() is not None
            if has_save:
                opts.append("Continue")
            opts += ["Daily Challenge", "Field Manual", "Leaderboard",
                     "Achievements", "Statistics", "Settings", "Quit"]
            best = self.sm.best_score()
            ach_got = len(self.sm.data.get("achievements", []))
            sub = f"BEST: {best}  |  MEDALS: {ach_got}/{len(ACH_DEFS)}"
            if has_save:
                sub += "  |  [SAVED RUN READY]"
            hints = [hint_map[o] for o in opts]
            use_banner = banner if self.w >= 78 and self.h >= 24 else None
            choice = self.menu("M E L T D O W N", opts, sub, hints=hints, banner=use_banner)
            if choice == -1 or opts[choice] == "Quit":
                return "quit"
            picked = opts[choice]
            if picked == "New Game":
                self.new_game_flow()
            elif picked == "Continue":
                self.continue_game()
            elif picked == "Daily Challenge":
                self.play_daily()
            elif picked == "Field Manual":
                self.show_manual()
            elif picked == "Leaderboard":
                self.show_leaderboard()
            elif picked == "Achievements":
                self.show_achievements()
            elif picked == "Statistics":
                self.show_statistics()
            elif picked == "Settings":
                self.settings_menu()

    def new_game_flow(self):
        modes = [
            "Solo",
            "Co-op (2 Players)",
            "Versus (2 Players)",
            "Boss Rush",
            "Practice / Training",
            "Custom Sandbox",
            "LAN Versus (Host/Join)",
        ]
        hints = [
            "Standard 7 levels + bosses + endless dread",
            "Shared terminal; Tab switches between P1 and P2",
            "Alternating runs using the exact same random seed",
            "Fight all 3 station bosses back-to-back",
            "Drill any single alarm type with zero hull/stress loss",
            "Pick starting level, mutators & shareable config code",
            "Play Versus over local network sockets",
        ]
        mi = self.menu("SELECT MODE", modes, "Choose your mission profile", hints=hints)
        if mi == -1:
            return
        self.mode = ["solo", "coop", "versus", "boss_rush", "practice", "sandbox", "lan"][mi]
        self.mutator = "none"

        if self.mode == "practice":
            return self.play_practice()
        if self.mode == "sandbox":
            return self.play_sandbox()
        if self.mode == "lan":
            return self.play_lan()

        di = self.menu("SELECT DIFFICULTY", ["Casual", "Operator", "Nightmare"],
                       "Choose your pain level")
        if di == -1:
            return
        self.diff = ["casual", "operator", "nightmare"][di]

        if self.mode in ("solo", "boss_rush"):
            mut_keys = list(MUTATORS.keys())
            mut_opts = [f"{MUTATORS[k][0]}: {MUTATORS[k][1]}" for k in mut_keys]
            mui = self.menu("SELECT MUTATOR", mut_opts, "Optional challenge modifier")
            if mui == -1:
                return
            self.mutator = mut_keys[mui]

        if self.mode == "versus":
            return self.play_versus()
        if self.mode == "boss_rush":
            return self.play_boss_rush()
        return self.play()

    # ── settings ────────────────────────────────────────────────────────────

    def settings_menu(self):
        keys = ["sound", "reduced_flash", "show_timer_numbers", "colorblind", "large_ui", "ascii_bars"]
        labels = ["Sound Effects", "Reduced Flashing", "Show Timer Numbers",
                  "Colorblind Mode", "Large UI", "ASCII Progress Bars"]
        theme_keys = list(THEMES.keys())
        skin_keys = [k for k, v in SKINS.items() if not v["req"] or self.sm.has_ach(v["req"])]
        while True:
            opts = []
            for k, lb in zip(keys, labels):
                v = self.sm.settings.get(k, DEFAULT_SETTINGS.get(k, False))
                pill = "[ * ON  ]" if v else "[ o OFF ]"
                opts.append(f"{lb:<22} {pill}")
            cur_theme = self.sm.settings.get("theme", "cyber_cyan")
            opts.append(f"Color Theme:           {THEMES.get(cur_theme, THEMES['cyber_cyan'])['name']}")
            cur_skin = self.sm.settings.get("skin", "default")
            opts.append(f"Console Skin:          {SKINS.get(cur_skin, SKINS['default'])['name']}")
            opts.append("Save & Back")
            ch = self.menu("SYSTEM SETTINGS", opts, "Configure audio, themes, skins & accessibility")
            if ch == -1 or ch == len(opts) - 1:
                Sound.enabled = self.sm.settings.get("sound", True)
                apply_theme(self.sm.settings.get("theme", "cyber_cyan"))
                self.sm.save()
                return
            if ch < len(keys):
                k = keys[ch]
                self.sm.settings[k] = not self.sm.settings.get(k, DEFAULT_SETTINGS.get(k, False))
            elif ch == len(keys):
                ti = (theme_keys.index(cur_theme) + 1) % len(theme_keys) if cur_theme in theme_keys else 0
                self.sm.settings["theme"] = theme_keys[ti]
                apply_theme(theme_keys[ti])
            elif ch == len(keys) + 1:
                si = (skin_keys.index(cur_skin) + 1) % len(skin_keys) if cur_skin in skin_keys else 0
                self.sm.settings["skin"] = skin_keys[si]

    # ── field manual ────────────────────────────────────────────────────────

    def show_manual(self):
        self.s.nodelay(False)
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()
        bw = min(self.w - 4, 82)
        bh = min(self.h - 2, len(ALARM_MANUAL) + 6)
        bx = max(1, (self.w - bw) // 2)
        by = max(1, (self.h - bh) // 2)
        self.box(by, bx, bh, bw, "FIELD MANUAL :: ALL 15 ALARMS", self.C(4), double=True)
        self.put(by + 2, bx + 3, f"{'ALARM':<12}{'HOW TO SOLVE':<40}{'EXAMPLE'}", self.C(4) | curses.A_BOLD)
        self.put(by + 3, bx + 2, "\u2500" * (bw - 4), self.C(4))
        for i, (name, desc, ex) in enumerate(ALARM_MANUAL):
            if by + 4 + i >= by + bh - 1:
                break
            line = f"{name:<12}{desc:<40}{ex}"
            self.put(by + 4 + i, bx + 3, line[:bw - 6])
        self.center(min(self.h - 1, by + bh + 1), "Press any key to return...", self.C(4))
        self.s.refresh()
        self.s.getch()

    # ── leaderboard / achievements / stats ──────────────────────────────────

    def show_leaderboard(self):
        self.s.nodelay(False)
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()
        bw = min(self.w - 4, 68)
        bh = min(self.h - 2, 21)
        bx = max(1, (self.w - bw) // 2)
        by = max(1, (self.h - bh) // 2)
        self.box(by, bx, bh, bw, "ORBITAL LEADERBOARD", self.C(4), double=True)
        self.put(by + 2, bx + 3,
                 f"{'RANK':<6}{'OPR':<7}{'SCORE':<10}{'LVL':<6}{'MODE':<12}{'DATE'}",
                 self.C(4) | curses.A_BOLD)
        self.put(by + 3, bx + 2, "\u2500" * (bw - 4), self.C(4))
        if not self.sm.scores:
            self.center(by + 6, "No mission records yet. Deploy to set a score!", self.C(2))
        for i, e in enumerate(self.sm.scores[:10]):
            if by + 4 + i >= by + bh - 4:
                break
            col = self.C(2) | curses.A_BOLD if i == 0 else (self.C(4) if i < 3 else 0)
            self.put(
                by + 4 + i, bx + 3,
                f"#{i+1:<5}{e.get('name','???'):<7}{e.get('score',0):<10}"
                f"{e.get('level',0):<6}{e.get('diff','?'):<12}{e.get('date','?')}",
                col,
            )
        daily = self.sm.get_daily()
        dy = by + bh - 4
        self.put(dy, bx + 2, "\u2500" * (bw - 4), self.C(4))
        d_txt = (f"DAILY CHALLENGE BEST: {daily['score']}  (LVL {daily['level']})"
                 if daily else "DAILY CHALLENGE: Not attempted today")
        self.center(dy + 1, d_txt, self.C(1) if daily else self.C(4))
        self.center(min(self.h - 1, by + bh + 1), "Press any key to return...", self.C(4))
        self.s.refresh()
        self.s.getch()

    def show_achievements(self):
        self.s.nodelay(False)
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()
        bw = min(self.w - 4, 72)
        bh = min(self.h - 2, len(ACH_DEFS) + 7)
        bx = max(1, (self.w - bw) // 2)
        by = max(1, (self.h - bh) // 2)
        self.box(by, bx, bh, bw, "STATION COMMENDATIONS", self.C(4), double=True)
        unlocked = self.sm.data.get("achievements", [])
        total = len(ACH_DEFS)
        got = sum(1 for k in ACH_DEFS if k in unlocked)
        self.bar(by + 2, bx + 3, f"PROGRESS {got:2d}/{total} ", got / total if total else 0,
                 min(28, bw - 24), self.C(1), True)
        self.put(by + 3, bx + 2, "\u2500" * (bw - 4), self.C(4))
        row = by + 4
        for aid, (name, desc) in ACH_DEFS.items():
            if row >= by + bh - 1:
                break
            done = aid in unlocked
            mark = "[*]" if done else "[ ]"
            col = self.C(1) | curses.A_BOLD if done else self.C(4)
            self.put(row, bx + 3, f"{mark} {name:<18} {desc}"[:bw - 6], col)
            row += 1
        self.center(min(self.h - 1, by + bh + 1), "Press any key to return...", self.C(4))
        self.s.refresh()
        self.s.getch()

    def show_statistics(self):
        self.s.nodelay(False)
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()
        lt = self.sm.lifetime
        bw = min(self.w - 4, 56)
        bh = 16
        bx = max(1, (self.w - bw) // 2)
        by = max(1, (self.h - bh) // 2)
        self.box(by, bx, bh, bw, "LIFETIME TELEMETRY", self.C(4), double=True)
        fast_str = f"{lt.get('fastest_ever', 0):.2f}s" if lt.get('fastest_ever', 999) < 999 else "---"
        tc, tw = lt.get("total_correct", 0), lt.get("total_wrong", 0)
        acc = (tc / (tc + tw) * 100) if (tc + tw) > 0 else 0.0
        rows = [
            ("Games Played", str(lt.get("total_games", 0))),
            ("Total Score", str(lt.get("total_score", 0))),
            ("Alarms Cleared", str(tc)),
            ("Wrong Entries", str(tw)),
            ("Alarms Missed", str(lt.get("total_missed", 0))),
            ("Best Combo", f"x{lt.get('best_combo', 0)}"),
            ("Fastest Answer", fast_str),
            ("Total Flight Time", f"{lt.get('total_play_time', 0) / 60:.1f} min"),
            ("Bosses Defeated", str(len(lt.get("bosses_killed", [])))),
            ("Lifetime Accuracy", f"{acc:.1f}%"),
        ]
        for i, (k, v) in enumerate(rows):
            col = (self.C(1) if acc > 70 else self.C(2)) if k == "Lifetime Accuracy" else 0
            self.put(by + 2 + i, bx + 4, f"{k:<22} {v}", col)
        self.center(min(self.h - 1, by + bh + 1), "Press any key to return...", self.C(4))
        self.s.refresh()
        self.s.getch()

    def show_game_stats(self, level_reached=1):
        self.s.nodelay(False)
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()
        st = self.stats
        rank = compute_rank(self.score, st.accuracy, level_reached)
        card = format_run_card(self.score, level_reached, st.accuracy,
                               st.combo_max, st.play_time, self.diff, self.mode)
        card_path = self.sm.export_run_card(card)

        bw = min(self.w - 4, 62)
        extra = min(5, len(self.ach_queue) + 2) if self.ach_queue else 0
        bh = min(self.h - 2, 18 + extra)
        bx = max(1, (self.w - bw) // 2)
        by = max(1, (self.h - bh) // 2)
        self.box(by, bx, bh, bw, f"MISSION DEBRIEF :: RANK {rank}", self.C(2), double=True)

        rows = [
            ("Operator Rank", rank),
            ("Final Score", str(self.score)),
            ("Accuracy", f"{st.accuracy:.1f}%"),
            ("Correct / Wrong", f"{st.correct} / {st.wrong}"),
            ("Alarms Missed", str(st.missed)),
            ("Longest Combo", f"x{st.combo_max}"),
            ("Fastest Answer", f"{st.fastest:.2f}s" if st.fastest < 999 else "---"),
            ("Avg Response", f"{st.avg_resp:.2f}s" if st.responses else "---"),
            ("Most Missed Type", st.worst_type.upper()),
            ("Power-ups Used", str(st.powerups)),
            ("Survival Time", f"{st.play_time:.0f}s"),
        ]
        for i, (k, v) in enumerate(rows):
            if by + 2 + i < by + bh - 2:
                col = self.C(1) | curses.A_BOLD if k == "Operator Rank" else 0
                self.put(by + 2 + i, bx + 4, f"{k:<22} {v}", col)
        if card_path and by + 14 < by + bh - 1:
            self.put(by + 14, bx + 4, f"Run Card saved: ~/.meltdown/last_run_card.md", self.C(4))
        if self.ach_queue:
            ay = by + 15
            if ay < by + bh - 2:
                self.center(ay, "MEDALS UNLOCKED:", self.C(1) | curses.A_BOLD)
                for j, aid in enumerate(self.ach_queue[:3]):
                    if ay + 1 + j < by + bh - 1:
                        name = ACH_DEFS.get(aid, ("?", ""))[0]
                        self.center(ay + 1 + j, f"* {name}", self.C(1))
        self.center(min(self.h - 1, by + bh + 1), "Press any key to continue...", self.C(4))
        self.s.refresh()
        self.s.getch()
        self.ach_queue.clear()

    # ── story, choices & perk draft ─────────────────────────────────────────

    def show_story(self, level_idx):
        if level_idx >= len(STORY):
            return
        lines = [(l, self.C(4) | curses.A_BOLD if l.startswith("[") else 0)
                 for l in STORY[level_idx]]
        self.screen(lines)

    def show_choice(self, level_idx):
        if level_idx not in CHOICES:
            return
        ch_data = CHOICES[level_idx]
        opts = [o[0] for o in ch_data["opts"]]
        ci = self.menu(ch_data["prompt"], opts, "Choose wisely, operator.")
        if ci == -1:
            ci = 0
        _, key, val = ch_data["opts"][ci]
        if key == "hull":
            self.hull = max(0, min(100, self.hull + val))
        elif key == "stress":
            self.stress = max(0, min(100, self.stress + val))
        elif key == "score":
            self.score += val
        elif key == "ttl_bonus":
            self.ttl_bonus = val
        elif key == "score_mult":
            self.score_mult = val
        elif key == "pup_bonus":
            self.pup_bonus = val

    def draft_perks(self):
        """Reactor Bay Upgrade Draft: pick 1 of 3 available perks."""
        avail = [k for k in PERKS if k not in self.perks]
        if not avail:
            return
        picks = random.sample(avail, min(3, len(avail)))
        opts = [f"{PERKS[k][0]}: {PERKS[k][1]}" for k in picks]
        ci = self.menu("REACTOR BAY UPGRADE DRAFT", opts, "Install 1 permanent ship upgrade")
        if ci == -1:
            ci = 0
        self.perks.add(picks[ci])

    # ── achievements ────────────────────────────────────────────────────────

    def check_ach(self, **kw):
        newly = []

        def _try(aid):
            if self.sm.unlock(aid):
                newly.append(aid)
                self.ach_queue.append(aid)

        if kw.get("level_clear"):
            _try("first_clear")
            lvl = kw.get("level", 0)
            if lvl >= 4:
                _try("survive_5")
            if lvl >= 6:
                _try("survive_7")
            if lvl >= len(LEVELS):
                _try("endless")
            if lvl >= len(LEVELS) + 4:
                _try("endless_5")
            if self.stats.level_no_mistakes:
                _try("no_mistakes")
            if self.stats.level_no_hull_dmg:
                _try("perfect_level")
            if self.diff == "nightmare" and lvl >= 1:
                _try("nightmare_clear")

        if kw.get("combo"):
            c = kw["combo"]
            if c >= 5:
                _try("combo_5")
            if c >= 10:
                _try("combo_10")
            if c >= 20:
                _try("combo_20")

        if kw.get("speed") and kw["speed"] < 1.0:
            _try("speed_solver")

        if kw.get("boss_kill"):
            _try("boss_slayer")
            bi = kw.get("boss_idx", -1)
            killed = self.sm.lifetime.get("bosses_killed", [])
            if bi not in killed:
                killed.append(bi)
                self.sm.lifetime["bosses_killed"] = killed
            if len(set(killed)) >= 3:
                _try("all_bosses")

        if kw.get("powerups") and kw["powerups"] >= 10:
            _try("powerup_10")
        if self.score >= 5000:
            _try("score_5000")
        if self.score >= 10000:
            _try("score_10000")
        if kw.get("daily"):
            _try("daily_driver")
        if kw.get("check_all_types") and len(self.stats.types_answered) >= len(ALL_KINDS):
            _try("all_types")
        return newly

    def pause_menu(self):
        opts = ["Resume", "Restart", "Settings", "Save & Quit to Menu"]
        ch = self.menu("PAUSED", opts, "Take a breath, operator.")
        if ch == -1 or ch == 0:
            return "resume"
        elif ch == 1:
            return "restart"
        elif ch == 2:
            self.settings_menu()
            return "resume"
        return "quit"

    # ── run one level ───────────────────────────────────────────────────────

    def run_level(self, idx, custom_kinds=None, practice=False):
        name, _, quota, spawn, ttl, max_active, pressure, kinds, glitch, surge = level_cfg(idx)
        if custom_kinds:
            kinds = custom_kinds
        self.stats.begin_level()

        d = DIFFICULTY[self.diff]
        spawn *= d["spawn"]
        ttl *= d["ttl"]
        ttl += self.ttl_bonus
        pressure *= d["stress"]
        hull_dmg = d["hull_dmg"]
        if "bulkhead" in self.perks:
            hull_dmg = max(5, hull_dmg - 5)
        pup_chance = d["pup"] + self.pup_bonus + (0.07 if "pup_magnet" in self.perks else 0.0)

        # Mutators
        blindfold = self.mutator == "blindfold"
        combo_mult_step = 0.25
        score_mult = self.score_mult
        if self.mutator == "glass_cannon":
            self.hull = min(self.hull, 1.0)
            score_mult *= 2.0
        elif self.mutator == "turbo":
            spawn /= 1.5
            ttl /= 1.3
            combo_mult_step = 0.375

        if self.sm.settings.get("large_ui", False):
            max_active = max(2, max_active - 1)

        alarms = []
        cleared = 0
        bufs = list(self.p_bufs) if self.mode == "coop" else [""]
        msg, msg_until, msg_col = "", 0, 0
        last = time.time()
        next_spawn = last + 0.8
        next_glitch = last + random.uniform(8, 14)
        glitch_until = 0.0
        next_pup = last + random.uniform(12, 24)
        next_hazard = last + random.uniform(14, 24)
        hazard_emp_until = 0.0
        hazard_overheat_until = 0.0
        buffer_shield_used = False
        ach_msg, ach_msg_until = "", 0.0

        reduced = self.sm.settings.get("reduced_flash", False)
        show_nums = self.sm.settings.get("show_timer_numbers", True)
        large = self.sm.settings.get("large_ui", False)
        alarm_rows = 4 if large else 3

        G, Y, R, C, M, W = (self.C(i) for i in (1, 2, 3, 4, 5, 6))

        self.ttl_bonus = 0.0
        self.score_mult = 1.0
        self.pup_bonus = 0.0
        self.s.nodelay(True)

        while True:
            now = time.time()
            dt = now - last
            last = now
            self.h, self.w = self.s.getmaxyx()

            # Ghost timeline sample every 1s
            elapsed_run = self.stats.play_time
            if elapsed_run - self._last_ghost_t >= 1.0:
                self._last_ghost_t = elapsed_run
                self.ghost_timeline.append((round(elapsed_run, 1), self.score))

            # ── input ──
            while True:
                ch = self.s.getch()
                if ch == -1:
                    break
                if ch == curses.KEY_RESIZE:
                    self.h, self.w = self.s.getmaxyx()
                    continue
                if ch == 27:
                    pause_start = time.time()
                    res = self.pause_menu()
                    self.s.nodelay(True)
                    curses.flushinp()
                    resume_now = time.time()
                    pause_dur = resume_now - pause_start
                    last = resume_now
                    next_spawn += pause_dur
                    next_glitch += pause_dur
                    next_pup += pause_dur
                    next_hazard += pause_dur
                    if self.freeze_until > pause_start:
                        self.freeze_until += pause_dur
                    for a in alarms:
                        a.born += pause_dur
                        if a.hide_after:
                            a.hide_after += pause_dur
                    if res == "quit":
                        if not practice:
                            self._auto_save(idx)
                        return "quit"
                    elif res == "restart":
                        return "restart"
                    continue

                if self.mode == "coop" and ch == 9:
                    self.active_p = 1 - self.active_p
                    continue

                bp = self.active_p if self.mode == "coop" else 0

                if ch in (10, 13, curses.KEY_ENTER):
                    guess = bufs[bp].strip().lower()
                    bufs[bp] = ""
                    if not guess:
                        continue

                    pup_hits = [a for a in alarms if a.is_powerup and a.answer == guess]
                    if pup_hits:
                        a = pup_hits[0]
                        alarms.remove(a)
                        self.stats.powerups += 1
                        cleared += self._apply_powerup(a.pup_name, alarms, now)
                        Sound.powerup()
                        msg = f"POWER-UP: {a.pup_desc}"
                        msg_col, msg_until = C, now + 2.0
                        self.check_ach(powerups=self.stats.powerups)
                        continue

                    hazard_hits = [a for a in alarms if a.is_hazard and a.answer == guess]
                    if hazard_hits:
                        a = hazard_hits[0]
                        alarms.remove(a)
                        Sound.powerup()
                        msg = f"HAZARD RESOLVED: {a.hazard_kind.upper()} CLEARED"
                        msg_col, msg_until = G, now + 1.8
                        continue

                    boss_hits = [a for a in alarms if a.is_boss and a.answer == guess]
                    if boss_hits:
                        a = min(boss_hits, key=lambda x: x.born + x.ttl)
                        alarms.remove(a)
                        resp = now - a.born
                        self.stats.hit("boss", resp)
                        pts = int(200 * (1 + self.combo * combo_mult_step) * score_mult)
                        self.combo += 1
                        self.score += pts
                        self.stress = max(0, self.stress - 12)
                        Sound.combo(self.combo)
                        msg, msg_col, msg_until = f"+{pts}  BOSS HIT!  COMBO x{self.combo}", M, now + 1.5
                        continue

                    normal = [a for a in alarms if not a.is_boss and not a.is_powerup and not a.is_hazard]
                    hits = [a for a in normal if a.answer == guess]
                    if hits:
                        a = min(hits, key=lambda x: x.born + x.ttl)
                        if not a.hit_mash():
                            msg = f"VENTING... {a.hits_left} more!"
                            msg_col, msg_until = Y, now + 0.8
                            continue
                        alarms.remove(a)
                        cleared += 1
                        resp = now - a.born
                        remaining = max(0, (a.born + a.ttl - now) / a.ttl)
                        qf_mult = 1.15 if ("quick_fingers" in self.perks and resp < 1.5) else 1.0
                        pts = int(100 * (1 + self.combo * combo_mult_step) * (0.5 + remaining) * score_mult * qf_mult)
                        self.combo += 1
                        if self.mode == "coop":
                            self.p_combos[bp] += 1
                            self.p_scores[bp] += pts
                        self.score += pts
                        self.stress = max(0, self.stress - 9)
                        self.stats.hit(a.kind, resp)
                        self.stats.combo_max = max(self.stats.combo_max, self.combo)
                        Sound.combo(self.combo)
                        msg = f"+{pts}  COMBO x{self.combo}"
                        msg_col, msg_until = G, now + 1.2
                        self.check_ach(combo=self.combo, speed=resp)
                    else:
                        if "buffer_shield" in self.perks and not buffer_shield_used:
                            buffer_shield_used = True
                            msg, msg_col, msg_until = "BUFFER SHIELD ABSORBED MISTAKE!", C, now + 1.5
                        else:
                            self.combo = 0
                            if self.mode == "coop":
                                self.p_combos[bp] = 0
                            if not practice:
                                self.stress += 10 * d["stress"]
                            self.stats.wrong_answer()
                            msg, msg_col, msg_until = "WRONG! stress up", R, now + 1.2
                            Sound.wrong()

                elif ch in (8, 127, curses.KEY_BACKSPACE):
                    bufs[bp] = bufs[bp][:-1]
                elif 32 <= ch < 127 and len(bufs[bp]) < 30:
                    if now < hazard_overheat_until and random.random() < 0.12:
                        msg, msg_col, msg_until = "OVERHEAT! key dropped", Y, now + 0.8
                    else:
                        bufs[bp] += chr(ch)

            # ── freeze check ──
            frozen = now < self.freeze_until
            if frozen:
                for a in alarms:
                    if not a.is_powerup:
                        a.born += dt
                        if a.hide_after:
                            a.hide_after += dt
                next_spawn += dt

            # ── spawning ──
            need = (999 if practice else quota) - cleared - sum(
                1 for a in alarms if not a.is_boss and not a.is_powerup and not a.is_hazard
            )
            if now >= next_spawn and need > 0:
                active_normal = sum(1 for a in alarms if not a.is_boss and not a.is_powerup and not a.is_hazard)
                if active_normal < max_active:
                    count = 1
                    if surge and not practice and random.random() < 0.18:
                        count = min(3, need, max_active - active_normal)
                        msg, msg_col, msg_until = "!! SURGE !!", R, now + 1.5
                        Sound.surge()
                    for _ in range(count):
                        alarms.append(Alarm(random.choice(kinds), ttl, now,
                                            level=idx, recent=self.recent_prompts,
                                            blindfold=blindfold))
                    next_spawn = now + spawn * random.uniform(0.6, 1.4)

            # ── power-up spawn ──
            if not practice and now >= next_pup and random.random() < pup_chance:
                pt = random.choice(POWERUP_TYPES)
                alarms.append(Alarm.make_powerup(pt, ttl * 0.8, now))
                next_pup = now + random.uniform(15, 30)
            elif now >= next_pup:
                next_pup = now + random.uniform(8, 15)

            # ── station hazards (Level 3+, non-practice) ──
            if not practice and idx >= 2 and now >= next_hazard:
                hk = random.choice(["overheat", "emp", "radiation", "oxygen"])
                if hk == "overheat":
                    hazard_overheat_until = now + 6.0
                    msg, msg_col, msg_until = "HAZARD: OVERHEAT! keys may drop", Y, now + 2.0
                elif hk == "emp":
                    hazard_emp_until = now + 5.0
                    msg, msg_col, msg_until = "HAZARD: EMP FLICKER! labels scrambled", Y, now + 2.0
                elif not any(a.is_hazard for a in alarms):
                    alarms.append(Alarm.make_hazard(hk, ttl * 1.3, now))
                    msg, msg_col, msg_until = f"HAZARD: {hk.upper()} DETECTED!", R, now + 2.0
                next_hazard = now + random.uniform(18, 28)

            # ── glitch ──
            if glitch and not reduced and now >= next_glitch:
                glitch_until = now + 4
                next_glitch = now + random.uniform(12, 20)
                msg, msg_col, msg_until = "DISPLAY CORRUPTED!", Y, now + 2

            # ── hazard ticks + expiry / stress ──
            rad_active = any(a.is_hazard and a.hazard_kind == "radiation" for a in alarms)
            oxy_active = any(a.is_hazard and a.hazard_kind == "oxygen" for a in alarms)
            if not frozen and not practice:
                if rad_active:
                    self.hull -= dt * 0.8
                if oxy_active:
                    self.stress += dt * 1.3

            for a in alarms[:]:
                if not frozen and now >= a.born + a.ttl:
                    alarms.remove(a)
                    if a.is_powerup or practice:
                        continue
                    if a.is_hazard:
                        self.hull -= 10
                        self.stress += 10
                        self.shake_until = now + 0.25
                        msg, msg_col, msg_until = "HAZARD UNRESOLVED!", R, now + 1.5
                        Sound.expire()
                        continue
                    self.hull -= hull_dmg
                    self.stress += 12 * d["stress"]
                    self.combo = 0
                    self.shake_until = now + 0.25
                    if self.mode == "coop":
                        self.p_combos = [0, 0]
                    cleared += 1
                    self.stats.miss(a.kind)
                    msg, msg_col, msg_until = "ALARM MISSED! hull damaged", R, now + 1.5
                    Sound.expire()

            if not frozen and not practice:
                active_stress = sum(1 for a in alarms if not a.is_powerup)
                if active_stress > 0:
                    self.stress += dt * active_stress * pressure
                    if active_stress < 2 and "auto_coolant" in self.perks:
                        self.stress -= dt * 1.5
                else:
                    self.stress -= dt * (5.5 if "auto_coolant" in self.perks else 4.0)
            self.stress = max(0.0, min(100.0, self.stress))

            if not practice and (self.stress > 85 or self.hull < 25) and now - self._last_warn_beep > 2.5:
                self._last_warn_beep = now
                Sound.warning_pulse()

            if not practice and (self.hull <= 0 or self.stress >= 100):
                return "dead"
            normal_left = sum(1 for a in alarms if not a.is_boss and not a.is_powerup and not a.is_hazard)
            if not practice and cleared >= quota and normal_left == 0:
                return "clear"

            # ── draw ──
            if not self._check_min_size():
                time.sleep(0.08)
                continue

            self.s.erase()
            shake_x = 1 if (not reduced and now < self.shake_until and int(now * 30) % 2 == 0) else 0
            panic = not reduced and self.stress > 80 and int(now * 5) % 2 == 0
            title_str = f" MELTDOWN :: {'PRACTICE' if practice else f'LVL {idx + 1} {name}'} "
            if self.daily:
                title_str = f" DAILY CHALLENGE :: LVL {idx + 1} {name} "
            self.put(0, shake_x, title_str.ljust(self.w - 1), curses.A_REVERSE | (R if panic else C))

            best = max(self.sm.best_score(), self.score)
            quota_str = f"CLEARED {cleared}" if practice else f"QUOTA {min(cleared, quota)}/{quota}"
            info = f" SCORE {self.score}  |  BEST {best}  |  COMBO x{self.combo}  |  {quota_str}"
            if self.mode == "coop":
                info += f"  |  P1:{self.p_scores[0]} P2:{self.p_scores[1]}"
            self.put(1, shake_x, info, C | curses.A_BOLD)

            scol = G if self.stress < 50 else (Y if self.stress < 80 else R)
            hcol = G if self.hull > 60 else (Y if self.hull > 30 else R)
            sfrac, hfrac = self.stress / 100, self.hull / 100
            cb = self.sm.settings.get("colorblind", False)
            slbl = f"{'!' if cb and sfrac>0.75 else '~' if cb and sfrac>0.5 else ''}STRESS "
            hlbl = f"{'!' if cb and hfrac<0.25 else '~' if cb and hfrac<0.5 else ''}HULL   "

            if now < msg_until and (not self.event_log or self.event_log[-1][0] != msg):
                self._log_event(msg, msg_col)

            wide = self.w >= 96 and self.h >= 22
            if wide:
                right_w = 38
                left_w = self.w - right_w - 1
                panel_h = max(8, self.h - 6)
                self.box(2, shake_x, panel_h, left_w, "INCOMING ALARMS", R if panic else C)
                self.box(2, left_w + 1 + shake_x, panel_h, right_w, "REACTOR TELEMETRY", C)

                rx = left_w + 3 + shake_x
                self._draw_reactor_core(3, left_w + 1 + shake_x, right_w, now, frozen)
                rbw = max(8, right_w - 18)
                self.bar(9, rx, slbl, sfrac, rbw, scol, show_nums)
                self.bar(10, rx, hlbl, hfrac, rbw, hcol, show_nums)
                self.put(12, rx, f"DIFF: {d['label']}  MUT: {MUTATORS[self.mutator][0]}", C)
                status_tags = []
                if frozen:
                    status_tags.append(f"FREEZE:{max(0.0, self.freeze_until - now):.1f}s")
                if rad_active:
                    status_tags.append("RAD")
                if oxy_active:
                    status_tags.append("LOW-O2")
                if now < hazard_overheat_until:
                    status_tags.append("HEAT")
                if now < hazard_emp_until:
                    status_tags.append("EMP")
                if status_tags:
                    self.put(13, rx, "SYS: " + " ".join(status_tags), Y | curses.A_BOLD)

                ghost_s = self.sm.get_ghost_score_at(elapsed_run)
                if ghost_s > 0:
                    self.put(14, rx, f"GHOST BEST: {ghost_s}", M)

                self.put(15, rx, "\u2500" * (right_w - 4), C)
                self.put(16, rx, "COMMS LOG", C | curses.A_BOLD)
                for li, (ltxt, lcol) in enumerate(list(self.event_log)[-4:]):
                    if 17 + li < 2 + panel_h - 1:
                        self.put(17 + li, rx, ltxt[:right_w - 5], lcol)

                alarm_x = 2 + shake_x
                alarm_bar_w = max(8, min(32, left_w - 16))
                row = 4
                max_row = 2 + panel_h - 2
            else:
                bw = max(10, min(40, self.w - 22))
                self.bar(3, 1 + shake_x, slbl, sfrac, bw, scol, show_nums)
                self.bar(4, 1 + shake_x, hlbl, hfrac, bw, hcol, show_nums)
                if frozen:
                    self.put(5, 1, "** CRYO FREEZE ACTIVE **", C | curses.A_BOLD)
                alarm_x = 1 + shake_x
                alarm_bar_w = max(8, min(30, self.w - 16))
                row = 6
                max_row = self.h - 4

            for a in sorted(alarms, key=lambda x: x.born + x.ttl):
                left = a.born + a.ttl - now
                frac = max(0.01, left / a.ttl) if a.ttl > 0 else 0.01
                txt = a.shown(now)
                if not reduced and now < glitch_until and not a.is_powerup:
                    rng = random.Random(int(now * 4) + id(a) % 97)
                    txt = "".join(c if c == " " or rng.random() > 0.3
                                  else rng.choice("#@%&?!$") for c in txt)

                if a.is_powerup:
                    col, tag = C | curses.A_BOLD, "[PWR ]"
                elif a.is_hazard:
                    col, tag = R | curses.A_BOLD, "[HZRD]"
                elif a.is_boss:
                    col, tag = M | curses.A_BOLD, "[BOSS]"
                elif frac > 0.5:
                    col, tag = G, "[SAFE]"
                elif frac > 0.25:
                    col, tag = Y, "[WARN]"
                else:
                    col, tag = R | curses.A_BOLD, "[CRIT]"

                lbl = "?????" if (now < hazard_emp_until and not a.is_powerup) else a.label
                pre = self._cb(frac) if not a.is_powerup and not a.is_boss else ""
                self.put(row, alarm_x, f"{tag} {pre}{lbl:<11} {txt}", col)
                timer_lbl = f" {max(0, left):4.1f}s " if show_nums else "  time "
                self.bar(row + 1, alarm_x + 2, timer_lbl, frac, alarm_bar_w, col)
                row += alarm_rows
                if row >= max_row:
                    break

            if now < ach_msg_until:
                self.put(self.h - 4, 1, f"* {ach_msg}", G | curses.A_BOLD)
            elif self.ach_queue:
                aid = self.ach_queue[-1]
                aname = ACH_DEFS.get(aid, ("?",))[0]
                ach_msg = f"ACHIEVEMENT UNLOCKED: {aname}!"
                ach_msg_until = now + 3.0
            elif now < msg_until:
                self.put(self.h - 4, 1, msg, msg_col | curses.A_BOLD)

            self.put(self.h - 3, 0, "\u2500" * (self.w - 1), C)
            if self.mode == "coop":
                plbl = f"CMD [P{self.active_p + 1}] \u25b8 "
                self.put(self.h - 2, 1, plbl + bufs[self.active_p], curses.A_BOLD)
                cursor_x = 1 + len(plbl) + len(bufs[self.active_p])
            else:
                plbl = "CMD \u25b8 "
                self.put(self.h - 2, 1, plbl + bufs[0], curses.A_BOLD)
                cursor_x = 1 + len(plbl) + len(bufs[0])
            self.put(self.h - 1, 1, "[Enter] Submit  [Esc] Pause" + ("  [Tab] Switch Player" if self.mode == "coop" else ""), C)
            try:
                self.s.move(self.h - 2, min(self.w - 2, cursor_x))
            except curses.error:
                pass
            self.s.refresh()
            time.sleep(0.03)

    def _apply_powerup(self, name, alarms, now):
        if name == "FREEZE":
            dur = 7.0 if "pup_magnet" in self.perks else 5.0
            self.freeze_until = now + dur
        elif name == "REPAIR":
            self.hull = min(100, self.hull + 20)
        elif name == "CALM":
            self.stress = max(0, self.stress - 30)
        elif name == "CLEAR":
            to_remove = [a for a in alarms if not a.is_boss and not a.is_powerup and not a.is_hazard]
            for a in to_remove:
                alarms.remove(a)
            return len(to_remove)
        return 0

    def _auto_save(self, level_idx):
        state = {
            "level": level_idx, "score": self.score, "hull": self.hull,
            "stress": self.stress, "combo": self.combo, "diff": self.diff,
            "mode": self.mode, "mutator": self.mutator,
            "perks": list(self.perks), "stats": self.stats.to_dict(),
        }
        self.sm.save_state(state)

    # ── boss fight ──────────────────────────────────────────────────────────

    def run_boss(self, boss_idx):
        b = BOSSES[boss_idx]
        self.animate_transition(f"BOSS INBOUND :: {b['name']}")
        self.screen([
            ("BOSS FIGHT", self.C(5) | curses.A_BOLD),
            (b["name"], self.C(3) | curses.A_BOLD),
            ("", 0),
            (b["sub"], 0),
            ("", 0),
            ("Type the BOSS CODES to break through!", self.C(4)),
            ("Press any key...", self.C(2)),
        ])
        Sound.boss()

        d = DIFFICULTY[self.diff]
        boss_hp = b["total_hp"]
        boss_max_hp = b["total_hp"]
        phase = 0
        total_phases = b["phases"]
        codes_per = b["codes"]
        reg_spawn = b["reg_spawn"] * d["spawn"]
        reg_kinds = b["reg_kinds"]
        stress_atk = b["stress_atk"]
        code_lo, code_hi = b["code_len"]

        alarms = []
        buf = ""
        msg, msg_until, msg_col = "", 0, 0
        last = time.time()
        next_spawn = last + 2.0
        next_stress_atk = last + 8.0
        phase_codes_left = codes_per
        boss_ttl = 25.0

        for _ in range(codes_per):
            alarms.append(Alarm.make_boss_code(random.randint(code_lo, code_hi), boss_ttl, last))

        G, Y, R, C, M, W = (self.C(i) for i in (1, 2, 3, 4, 5, 6))
        self.s.nodelay(True)

        while True:
            now = time.time()
            dt = now - last
            last = now
            self.h, self.w = self.s.getmaxyx()

            while True:
                ch = self.s.getch()
                if ch == -1:
                    break
                if ch == curses.KEY_RESIZE:
                    self.h, self.w = self.s.getmaxyx()
                    continue
                if ch == 27:
                    pause_start = time.time()
                    res = self.pause_menu()
                    self.s.nodelay(True)
                    curses.flushinp()
                    resume_now = time.time()
                    pause_dur = resume_now - pause_start
                    last = resume_now
                    next_spawn += pause_dur
                    next_stress_atk += pause_dur
                    for a in alarms:
                        a.born += pause_dur
                    if res == "quit":
                        return "quit"
                    elif res == "restart":
                        return "restart"
                    continue
                if ch in (10, 13, curses.KEY_ENTER):
                    guess = buf.strip().lower()
                    buf = ""
                    if not guess:
                        continue
                    boss_hits = [a for a in alarms if a.is_boss and a.answer == guess]
                    if boss_hits:
                        a = min(boss_hits, key=lambda x: x.born + x.ttl)
                        alarms.remove(a)
                        resp = now - a.born
                        pts = int(300 * (1 + self.combo * 0.25))
                        self.combo += 1
                        self.score += pts
                        self.stress = max(0, self.stress - 15)
                        self.stats.hit("boss", resp)
                        self.stats.combo_max = max(self.stats.combo_max, self.combo)
                        phase_codes_left -= 1
                        boss_hp -= boss_max_hp // total_phases
                        self.shake_until = now + 0.15
                        Sound.combo(self.combo)
                        msg = f"+{pts}  BOSS DAMAGED!  HP: {max(0, boss_hp)}/{boss_max_hp}"
                        msg_col, msg_until = M, now + 1.5
                        self.check_ach(combo=self.combo, speed=resp)

                        if phase_codes_left <= 0:
                            phase += 1
                            if phase >= total_phases or boss_hp <= 0:
                                boss_hp = 0
                                break
                            phase_codes_left = codes_per
                            boss_ttl = max(15, boss_ttl - 2)
                            for _ in range(codes_per):
                                alarms.append(Alarm.make_boss_code(random.randint(code_lo, code_hi), boss_ttl, now))
                            msg, msg_col, msg_until = f"PHASE {phase + 1}/{total_phases}!", M, now + 2.0
                            Sound.boss()
                        continue

                    hits = [a for a in alarms if not a.is_boss and a.answer == guess]
                    if hits:
                        a = min(hits, key=lambda x: x.born + x.ttl)
                        if not a.hit_mash():
                            continue
                        alarms.remove(a)
                        resp = now - a.born
                        pts = int(100 * (1 + self.combo * 0.25))
                        self.combo += 1
                        self.score += pts
                        self.stress = max(0, self.stress - 9)
                        self.stats.hit(a.kind, resp)
                        self.stats.combo_max = max(self.stats.combo_max, self.combo)
                        msg, msg_col, msg_until = f"+{pts}  COMBO x{self.combo}", G, now + 1.2
                    else:
                        self.combo = 0
                        self.stress += 10
                        self.stats.wrong_answer()
                        msg, msg_col, msg_until = "WRONG!", R, now + 1.2
                        Sound.wrong()
                elif ch in (8, 127, curses.KEY_BACKSPACE):
                    buf = buf[:-1]
                elif 32 <= ch < 127 and len(buf) < 30:
                    buf += chr(ch)

            active_reg = sum(1 for a in alarms if not a.is_boss)
            if now >= next_spawn and active_reg < 3:
                alarms.append(Alarm(random.choice(reg_kinds), 10 * d["ttl"], now,
                                    level=(boss_idx + 1) * 2, recent=self.recent_prompts))
                next_spawn = now + reg_spawn * random.uniform(0.7, 1.3)

            if stress_atk > 0 and now >= next_stress_atk:
                self.stress += stress_atk
                msg, msg_col, msg_until = f"BOSS ATTACKS! +{stress_atk} stress", R, now + 1.5
                next_stress_atk = now + random.uniform(6, 12)

            for a in alarms[:]:
                if now >= a.born + a.ttl:
                    alarms.remove(a)
                    if a.is_boss:
                        self.hull -= 20
                        self.stress += 15
                        self.shake_until = now + 0.25
                        phase_codes_left -= 1
                        if phase_codes_left <= 0:
                            phase += 1
                            if phase >= total_phases:
                                break
                            phase_codes_left = codes_per
                            for _ in range(codes_per):
                                alarms.append(Alarm.make_boss_code(random.randint(code_lo, code_hi), boss_ttl, now))
                        msg, msg_col, msg_until = "BOSS CODE EXPIRED!", R, now + 1.5
                    else:
                        self.hull -= d["hull_dmg"]
                        self.stress += 12
                        self.combo = 0
                    Sound.expire()

            if alarms:
                self.stress += dt * len(alarms) * 1.2
            self.stress = max(0.0, min(100.0, self.stress))

            if self.hull <= 0 or self.stress >= 100:
                return "dead"
            if boss_hp <= 0 or phase >= total_phases:
                break

            if not self._check_min_size():
                time.sleep(0.08)
                continue

            self.s.erase()
            self.put(0, 0, f" BOSS THREAT :: {b['name']} ".ljust(self.w - 1), curses.A_REVERSE | M)
            boss_frac = max(0, boss_hp / boss_max_hp)
            self.put(1, 0, f" PHASE {phase + 1}/{total_phases}  |  SCORE {self.score}  |  COMBO x{self.combo}", M | curses.A_BOLD)
            bw = max(10, min(42, self.w - 22))
            self.bar(3, 1, "BOSS HP ", boss_frac, bw, M | curses.A_BOLD, True)
            scol = G if self.stress < 50 else (Y if self.stress < 80 else R)
            hcol = G if self.hull > 60 else (Y if self.hull > 30 else R)
            self.bar(4, 1, "STRESS  ", self.stress / 100, bw, scol, True)
            self.bar(5, 1, "HULL    ", self.hull / 100, bw, hcol, True)

            row = 7
            for a in sorted(alarms, key=lambda x: (0 if x.is_boss else 1, x.born + x.ttl)):
                left = a.born + a.ttl - now
                frac = max(0.01, left / a.ttl) if a.ttl > 0 else 0.01
                txt = a.shown(now)
                tag = "[BOSS]" if a.is_boss else ("[SAFE]" if frac > 0.5 else ("[WARN]" if frac > 0.25 else "[CRIT]"))
                col = M | curses.A_BOLD if a.is_boss else (G if frac > 0.5 else (Y if frac > 0.25 else R | curses.A_BOLD))
                self.put(row, 1, f"{tag} {a.label:<11} {txt}", col)
                self.bar(row + 1, 3, f" {max(0, left):4.1f}s ", frac, max(8, min(30, self.w - 16)), col)
                row += 3
                if row >= self.h - 4:
                    break

            if now < msg_until:
                self.put(self.h - 4, 1, msg, msg_col | curses.A_BOLD)
            self.put(self.h - 3, 0, "\u2500" * (self.w - 1), M)
            plbl = "CMD \u25b8 "
            self.put(self.h - 2, 1, plbl + buf, curses.A_BOLD)
            try:
                self.s.move(self.h - 2, min(self.w - 2, 1 + len(plbl) + len(buf)))
            except curses.error:
                pass
            self.s.refresh()
            time.sleep(0.03)

        self.check_ach(boss_kill=True, boss_idx=boss_idx)
        bonus = 1000 * (boss_idx + 1)
        self.score += bonus
        self.hull = min(100, self.hull + 15)
        self.stress = max(0, self.stress - 25)
        self.screen([
            ("BOSS DEFEATED!", self.C(1) | curses.A_BOLD),
            (b["name"], self.C(5) | curses.A_BOLD),
            ("", 0),
            (f"Bonus: +{bonus}", 0),
            ("Hull repaired. Stress reduced.", 0),
            ("", 0),
            ("Press any key...", self.C(2)),
        ])
        return "clear"

    # ── main play loops ─────────────────────────────────────────────────────

    def _reset_run(self):
        self.score, self.combo, self.stress, self.hull = 0, 0, 0.0, 100.0
        self.perks.clear()
        self.stats.reset()
        self.ach_queue.clear()
        self.ghost_timeline = []
        self._last_ghost_t = -1.0
        self.freeze_until = 0.0
        self.shake_until = 0.0
        self.ttl_bonus = 0.0
        self.score_mult = 1.0
        self.pup_bonus = 0.0
        if self.mode == "coop":
            self.p_combos = [0, 0]
            self.p_scores = [0, 0]
            self.p_bufs = ["", ""]
            self.active_p = 0

    def play(self, start_idx=0):
        self._reset_run()
        self.sm.clear_state()
        idx = start_idx

        while True:
            name, flavour, *_ = level_cfg(idx)
            self.animate_transition(f"SECTOR {idx + 1} :: {name}")
            self.screen([(f"LEVEL {idx + 1}", self.C(4) | curses.A_BOLD),
                         (name, self.C(3) | curses.A_BOLD), ("", 0),
                         (flavour, 0), ("", 0),
                         (f"Difficulty: {DIFFICULTY[self.diff]['label']}  |  Mutator: {MUTATORS[self.mutator][0]}", self.C(2))],
                        wait_key=False)
            result = self.run_level(idx)

            if result == "dead":
                return self._finish_game(idx, "dead")
            if result == "quit":
                return "quit"
            if result == "restart":
                return self.play(start_idx=start_idx)

            bonus = 500 * (idx + 1)
            self.score += bonus
            self.hull = min(100, self.hull + 10)
            self.stress = max(0, self.stress - 30)
            self.check_ach(level_clear=True, level=idx, check_all_types=True)
            self._auto_save(idx + 1)

            self.screen([(f"LEVEL {idx + 1} CLEARED", self.C(1) | curses.A_BOLD),
                         (f"Bonus +{bonus}   Hull repaired", 0), ("", 0),
                         ("Press any key for next...", 0)])

            self.show_story(idx)
            self.show_choice(idx)
            if idx in (0, 2, 4):
                self.draft_perks()

            if idx in BOSS_AFTER_LEVEL:
                br = self.run_boss(BOSS_AFTER_LEVEL[idx])
                if br == "dead":
                    return self._finish_game(idx, "dead")
                if br == "quit":
                    return "quit"
                if br == "restart":
                    return self.play(start_idx=start_idx)
            idx += 1

    def play_boss_rush(self):
        self._reset_run()
        self.screen([
            ("BOSS RUSH", self.C(5) | curses.A_BOLD),
            ("All 3 Station Bosses. Back-to-back.", 0),
            ("", 0),
            ("Press any key...", self.C(2)),
        ])
        for bi in range(len(BOSSES)):
            br = self.run_boss(bi)
            if br == "dead":
                return self._finish_game(bi + 1, "dead")
            if br == "quit":
                return "quit"
            if br == "restart":
                return self.play_boss_rush()
        return self._finish_game(len(LEVELS), "clear")

    def play_practice(self):
        opts = [k.upper() for k in ALL_KINDS]
        ci = self.menu("PRACTICE / TRAINING", opts, "Select an alarm type to drill (no damage)")
        if ci == -1:
            return
        kind = ALL_KINDS[ci]
        self._reset_run()
        self.diff = "operator"
        self.run_level(2, custom_kinds=[kind], practice=True)

    def play_sandbox(self):
        opts = ["Configure New Sandbox", "Enter Sandbox Code (SBX-...)"]
        ci = self.menu("CUSTOM SANDBOX", opts, "Customize rules or load a friend's seed code")
        if ci == -1:
            return
        if ci == 1:
            code = self.prompt_text("SANDBOX CODE", "Enter code (e.g. SBX-12345-L3-T):", max_len=24)
            if not code:
                return
            parsed = decode_sandbox_code(code)
            if not parsed:
                self.screen([("Invalid Sandbox Code!", self.C(3) | curses.A_BOLD), ("", 0), ("Press any key...", 0)])
                return
            seed, start_lvl, mut = parsed
        else:
            li = self.menu("STARTING LEVEL", [f"Level {i + 1}: {LEVELS[i][0]}" for i in range(len(LEVELS))],
                           "Select starting sector")
            if li == -1:
                return
            mut_keys = list(MUTATORS.keys())
            mui = self.menu("SELECT MUTATOR", [f"{MUTATORS[k][0]}: {MUTATORS[k][1]}" for k in mut_keys],
                            "Choose modifier")
            if mui == -1:
                return
            start_lvl = li
            mut = mut_keys[mui]
            seed = random.randint(10000, 99999)

        di = self.menu("SELECT DIFFICULTY", ["Casual", "Operator", "Nightmare"], "Sandbox difficulty")
        if di == -1:
            return
        self.diff = ["casual", "operator", "nightmare"][di]
        self.mutator = mut
        random.seed(seed)
        code_str = encode_sandbox_code(seed, start_lvl, mut)
        self.screen([
            ("SANDBOX DEPLOYMENT", self.C(4) | curses.A_BOLD),
            (f"Share Code: {code_str}", self.C(2) | curses.A_BOLD),
            ("", 0),
            ("Press any key to launch...", 0),
        ])
        self.play(start_idx=start_lvl)

    def play_lan(self):
        ci = self.menu("LAN VERSUS", ["Host Match", "Join Match"], "Local network head-to-head")
        if ci == -1:
            return
        port = 50555
        if ci == 0:
            di = self.menu("SELECT DIFFICULTY", ["Casual", "Operator", "Nightmare"], "Host difficulty")
            if di == -1:
                return
            self.diff = ["casual", "operator", "nightmare"][di]
            seed = random.randint(1, 2**30)
            ip = get_local_ip()
            self.screen([
                ("HOSTING LAN MATCH", self.C(4) | curses.A_BOLD),
                (f"Tell peer to join: {ip}:{port}", self.C(2) | curses.A_BOLD),
                ("Waiting for connection (up to 45s)...", 0),
            ], wait_key=False)
            try:
                conn = host_lan_handshake(port, seed, self.diff, timeout=45.0)
            except Exception as exc:
                self.screen([("LAN Host Failed", self.C(3) | curses.A_BOLD), (str(exc), 0), ("", 0), ("Press any key...", 0)])
                return
        else:
            host = self.prompt_text("JOIN LAN MATCH", "Enter Host IP (e.g. 192.168.1.10):", max_len=40)
            if not host:
                return
            try:
                conn, seed, self.diff = join_lan_handshake(host.strip(), port, timeout=15.0)
            except Exception as exc:
                self.screen([("LAN Join Failed", self.C(3) | curses.A_BOLD), (str(exc), 0), ("", 0), ("Press any key...", 0)])
                return

        try:
            random.seed(seed)
            self._reset_run()
            final_lvl = 0
            for idx in range(len(LEVELS)):
                result = self.run_level(idx)
                if result in ("dead", "quit"):
                    final_lvl = idx + 1
                    break
                final_lvl = idx + 1
                self.score += 500 * (idx + 1)
                self.hull = min(100, self.hull + 10)
                self.stress = max(0, self.stress - 30)

            self.screen([("MATCH COMPLETE", self.C(4) | curses.A_BOLD), ("Waiting for peer result...", 0)], wait_key=False)
            send_json(conn, {"score": self.score, "level": final_lvl})
            peer = recv_json(conn, timeout=120.0)
            p_score = int(peer.get("score", 0))
            verdict = "YOU WIN!" if self.score > p_score else ("YOU LOSE!" if self.score < p_score else "TIE!")
            self.screen([
                ("LAN VERSUS RESULTS", self.C(2) | curses.A_BOLD),
                (f"YOU: {self.score} (LVL {final_lvl})", self.C(4)),
                (f"PEER: {p_score} (LVL {peer.get('level', 0)})", self.C(4)),
                ("", 0),
                (verdict, self.C(1) | curses.A_BOLD),
                ("", 0),
                ("Press any key...", 0),
            ])
        except Exception as exc:
            self.screen([("LAN Connection Lost", self.C(3)), (str(exc), 0), ("", 0), ("Press any key...", 0)])
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # ── game over ───────────────────────────────────────────────────────────

    def show_game_over(self, idx, why):
        """Render the retro CRT Hazard Box Game Over screen."""
        self.s.nodelay(False)
        curses.curs_set(0)
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()

        R, Y, C, G = self.C(3), self.C(2), self.C(4), self.C(1)
        bw = min(self.w - 4, 68)
        bh = min(self.h - 4, 19)
        bx = max(1, (self.w - bw) // 2)
        by = max(2, (self.h - bh) // 2)

        caution = "/// CAUTION /// CRITICAL BREACH /// CAUTION ///"
        self.center(max(0, by - 1), caution, Y | curses.A_BOLD)
        self.box(by, bx, bh, bw, "STATION LOST", R, double=True)

        core_art = [
            "  .-\u2550\u2550\u2550-.  ",
            " / \\ | / \\ ",
            "\u2502 \u2500 (X) \u2500 \u2502",
            " \\ / | \\ / ",
            "  '-\u2550\u2550\u2550-'  ",
        ]
        ay = by + 2
        for i, line in enumerate(core_art):
            if ay + i < by + bh - 1:
                self.center(ay + i, line, R | curses.A_BOLD)

        gy = ay + 6
        if gy < by + bh - 1:
            self.center(gy, "G A M E   O V E R", R | curses.A_BOLD)
        if gy + 1 < by + bh - 1:
            self.center(gy + 1, why)

        best = max(self.sm.best_score(), self.score)
        if self.score > 0 and self.score >= best and gy + 2 < by + bh - 5:
            self.center(gy + 2, "[ * NEW HIGH SCORE! * ]", G | curses.A_BOLD)

        inner_w = min(bw - 8, 54)
        inner_h = 5
        ix = max(bx + 2, (self.w - inner_w) // 2)
        iy = min(by + bh - 7, gy + 3)
        if iy > gy + 1 and iy + inner_h < by + bh - 1:
            self.box(iy, ix, inner_h, inner_w, "RUN SUMMARY", Y)
            self.center(
                iy + 1,
                f"LVL {idx + 1}   |   SCORE {self.score:,}   |   BEST {best:,}",
                C | curses.A_BOLD,
            )
            self.center(
                iy + 2,
                f"COMBO x{self.stats.combo_max}   |   ACCURACY {self.stats.accuracy:.1f}%",
                G,
            )

        self.center(min(by + bh - 2, iy + inner_h + 1), "[ PRESS ANY KEY ]", Y | curses.A_BOLD)
        self.center(min(self.h - 1, by + bh), caution, Y | curses.A_BOLD)
        self.s.refresh()
        self.s.getch()
        curses.flushinp()
        curses.curs_set(1)

    def _finish_game(self, idx, reason):
        self.sm.clear_state()
        why = ("Your hull ruptured." if self.hull <= 0
               else "You cracked under the stress.")
        self.show_game_over(idx, why)

        sd = self.stats.to_dict()
        sd["score"] = self.score
        self.sm.update_lifetime(sd)
        self.sm.save_ghost(self.score, self.ghost_timeline)

        if self.sm.qualifies(self.score):
            initials = self.get_initials()
            self.sm.add_score(initials, self.score, idx + 1, self.diff, self.stats.play_time)

        if self.daily:
            self.sm.set_daily(self.score, idx + 1)
            self.check_ach(daily=True)

        self.show_game_stats(level_reached=idx + 1)
        return "done"

    def continue_game(self):
        state = self.sm.load_state()
        if not state:
            self.screen([("No saved game found.", self.C(3)), ("", 0), ("Press any key...", 0)])
            return
        self._reset_run()
        self.score = state.get("score", 0)
        self.hull = state.get("hull", 100)
        self.stress = state.get("stress", 0)
        self.combo = state.get("combo", 0)
        self.diff = state.get("diff", "operator")
        self.mode = state.get("mode", "solo")
        self.mutator = state.get("mutator", "none")
        self.perks = set(state.get("perks", []))
        self.sm.clear_state()
        idx = state.get("level", 0)

        while True:
            name, flavour, *_ = level_cfg(idx)
            self.screen([(f"LEVEL {idx + 1}", self.C(4) | curses.A_BOLD),
                         (name, self.C(3) | curses.A_BOLD), ("", 0), (flavour, 0)], wait_key=False)
            result = self.run_level(idx)
            if result == "dead":
                return self._finish_game(idx, "dead")
            if result == "quit":
                return "quit"
            if result == "restart":
                return self.play()

            bonus = 500 * (idx + 1)
            self.score += bonus
            self.hull = min(100, self.hull + 10)
            self.stress = max(0, self.stress - 30)
            self.check_ach(level_clear=True, level=idx, check_all_types=True)
            self._auto_save(idx + 1)
            self.screen([(f"LEVEL {idx + 1} CLEARED", self.C(1) | curses.A_BOLD),
                         (f"Bonus +{bonus}   Hull repaired", 0), ("", 0),
                         ("Press any key for next...", 0)])
            self.show_story(idx)
            self.show_choice(idx)
            if idx in BOSS_AFTER_LEVEL:
                br = self.run_boss(BOSS_AFTER_LEVEL[idx])
                if br == "dead":
                    return self._finish_game(idx, "dead")
                if br == "quit":
                    return "quit"
                if br == "restart":
                    return self.play()
            idx += 1

    def play_daily(self):
        self.daily = True
        random.seed(daily_seed())
        self.diff = "operator"
        self.mode = "solo"
        self.mutator = "none"
        self._reset_run()

        self.screen([
            ("DAILY CHALLENGE", self.C(2) | curses.A_BOLD),
            (f"Date: {date.today().isoformat()}", self.C(4)),
            ("", 0),
            ("Same alarms for everyone today.", 0),
            ("5 levels. One shot. Make it count.", 0),
            ("", 0),
            ("Press any key...", self.C(2)),
        ])

        for idx in range(5):
            name, flavour, *_ = level_cfg(idx)
            self.screen([(f"LEVEL {idx + 1}", self.C(4) | curses.A_BOLD),
                         (name, self.C(3) | curses.A_BOLD), ("", 0), (flavour, 0)], wait_key=False)
            result = self.run_level(idx)
            if result == "dead":
                self.daily = False
                return self._finish_game(idx, "dead")
            if result == "quit":
                self.daily = False
                return "quit"
            if result == "restart":
                self.daily = False
                return
            self.score += 500 * (idx + 1)
            self.hull = min(100, self.hull + 10)
            self.stress = max(0, self.stress - 30)

        self.sm.set_daily(self.score, 5)
        self.check_ach(daily=True)
        sd = self.stats.to_dict()
        sd["score"] = self.score
        self.sm.update_lifetime(sd)

        self.screen([("DAILY CHALLENGE COMPLETE!", self.C(1) | curses.A_BOLD),
                     (f"Score: {self.score}", 0), ("", 0), ("Press any key...", self.C(2))])
        self.show_game_stats(level_reached=5)
        self.daily = False

    def play_versus(self):
        seed = random.randint(0, 2**31)
        scores = []
        for player in (1, 2):
            self.screen([(f"PLAYER {player}", self.C(4) | curses.A_BOLD),
                         ("Get ready!", 0), ("", 0), ("Press any key to start...", self.C(2))])
            random.seed(seed)
            self.mode = "solo"
            self._reset_run()
            final_level = 0
            for idx in range(len(LEVELS)):
                name, flavour, *_ = level_cfg(idx)
                self.screen([(f"P{player} - LEVEL {idx + 1}", self.C(4) | curses.A_BOLD),
                             (name, self.C(3) | curses.A_BOLD), ("", 0), (flavour, 0)], wait_key=False)
                result = self.run_level(idx)
                if result == "dead":
                    final_level = idx + 1
                    break
                if result == "quit":
                    return "quit"
                if result == "restart":
                    return
                self.score += 500 * (idx + 1)
                self.hull = min(100, self.hull + 10)
                self.stress = max(0, self.stress - 30)
                final_level = idx + 1
            else:
                final_level = len(LEVELS)
            scores.append((player, self.score, final_level))
            self.screen([(f"PLAYER {player} DONE", self.C(4) | curses.A_BOLD),
                         (f"Score: {self.score}   Level: {final_level}", 0), ("", 0), ("Press any key...", self.C(2))])

        s1, s2 = scores[0], scores[1]
        winner = "PLAYER 1 WINS!" if s1[1] > s2[1] else ("PLAYER 2 WINS!" if s2[1] > s1[1] else "IT'S A TIE!")
        self.screen([
            ("VERSUS RESULTS", self.C(2) | curses.A_BOLD), ("", 0),
            (f"P1: Score {s1[1]}  Level {s1[2]}", self.C(4)),
            (f"P2: Score {s2[1]}  Level {s2[2]}", self.C(4)),
            ("", 0), (winner, self.C(1) | curses.A_BOLD), ("", 0), ("Press any key...", self.C(2)),
        ])
        return "done"


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main(stdscr):
    curses.curs_set(1)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    curses.start_color()
    curses.use_default_colors()
    try:
        curses.set_escdelay(25)
    except Exception:
        pass

    sm = SaveManager()
    apply_theme(sm.settings.get("theme", "cyber_cyan"))
    Sound.enabled = sm.settings.get("sound", True)
    g = Game(stdscr, sm)
    g.main_menu()


def run() -> int:
    """Launch the game inside curses, restoring the terminal on exit."""
    try:
        curses.wrapper(main)
        return 0
    except KeyboardInterrupt:
        print("Station abandoned. Coward.")
        return 0
    except curses.error as exc:
        print(
            f"Terminal error: {exc}\n"
            "Ensure your terminal supports curses and is at least 80x24.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(run())
