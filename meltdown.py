#!/usr/bin/env python3
"""
MELTDOWN v2.0 — A stressful, fast-typing survival game in your terminal.

You are the last operator on a failing space station. Alarms pop up
faster and faster. Type the right answer and press ENTER before the
timer runs out. Keep your STRESS and HULL under control. Survive all levels.

Run:      python3 meltdown.py
Windows:  pip install windows-curses   (then run the same command)

Features:  10 alarm types · 7 handcrafted levels + endless mode · 3 boss fights
           power-ups · difficulty modes · co-op & versus 2-player · daily challenge
           achievements · leaderboard · save/resume · story events · accessibility
"""

import curses
import hashlib
import json
import os
import random
import time
from datetime import date, datetime

# ═══════════════════════════════════════════════════════════════════════════════
#  DATA
# ═══════════════════════════════════════════════════════════════════════════════

WORDS = [
    "reactor", "coolant", "plasma", "airlock", "thruster", "oxygen", "gravity",
    "quantum", "fusion", "hatch", "vacuum", "orbit", "warp", "shield", "core",
    "valve", "circuit", "turbine", "pressure", "cryo", "nebula", "meteor",
    "ignite", "eject", "breach", "sensor", "uplink", "photon", "isotope",
    "helium", "piston", "beacon", "carbon", "dynamo", "flare", "impulse",
]

SHORT_WORDS = [
    "core", "warp", "fuel", "hull", "beam", "dock", "scan", "flux", "ion",
    "pod", "vent", "arc", "bolt", "fuse", "grid", "node", "byte", "chip",
]

MORSE = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',   'E': '.',
    'F': '..-.',  'G': '--.',   'H': '....',  'I': '..',    'J': '.---',
    'K': '-.-',   'L': '.-..',  'M': '--',    'N': '-.',    'O': '---',
    'P': '.--.',  'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',  'Y': '-.--',
    'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
}

# ═══════════════════════════════════════════════════════════════════════════════
#  LEVEL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# (name, flavour, quota, spawn_secs, alarm_ttl, max_active, pressure,
#  kinds, glitch, surge)
LEVELS = [
    ("BOOT SEQUENCE",  "Easy does it. Systems warming up...",
     6, 3.5, 14, 2, 0.8, ["type"], False, False),
    ("COOLANT LEAK",   "Things are getting slippery.",
     8, 3.0, 12, 3, 1.0, ["type", "reverse"], False, False),
    ("PRESSURE SPIKE", "Your calculator hand better be ready.",
     10, 2.6, 11, 3, 1.1, ["type", "reverse", "math", "sequence"], False, False),
    ("SOLAR FLARE",    "Displays will get corrupted. Squint.",
     12, 2.3, 10, 4, 1.2, ["type", "reverse", "math", "scramble", "binary"], True, False),
    ("BLACKOUT",       "Memorize codes before they vanish!",
     14, 2.0, 9, 4, 1.3,
     ["type", "reverse", "math", "scramble", "memory", "morse"], True, False),
    ("CORE BREACH",    "Alarm surges incoming. Breathe. Or don't.",
     16, 1.7, 8, 5, 1.4,
     ["type", "reverse", "math", "scramble", "memory", "decode"], True, True),
    ("TOTAL MELTDOWN", "Nobody has survived this. Good luck.",
     20, 1.4, 7, 6, 1.6,
     ["type", "reverse", "math", "scramble", "memory", "morse",
      "sequence", "binary", "decode", "seqlock"], True, True),
]

ALL_KINDS = ["type", "reverse", "math", "scramble", "memory",
             "morse", "sequence", "binary", "decode", "seqlock"]

DIFFICULTY = {
    "casual":    {"spawn": 1.5, "ttl": 1.4, "stress": 0.6,
                  "hull_dmg": 10, "pup": 0.15, "label": "CASUAL"},
    "operator":  {"spawn": 1.0, "ttl": 1.0, "stress": 1.0,
                  "hull_dmg": 15, "pup": 0.08, "label": "OPERATOR"},
    "nightmare": {"spawn": 0.7, "ttl": 0.75, "stress": 1.4,
                  "hull_dmg": 20, "pup": 0.04, "label": "NIGHTMARE"},
}

# ═══════════════════════════════════════════════════════════════════════════════
#  BOSS DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

BOSSES = [
    {"name": "THE SENTINEL", "sub": "Defense system online. Break through.",
     "phases": 3, "codes": 2, "code_len": (5, 7), "reg_spawn": 4.0,
     "reg_kinds": ["type", "reverse"], "stress_atk": 0, "total_hp": 100},
    {"name": "THE GUARDIAN", "sub": "It knows you are here. Fight back.",
     "phases": 4, "codes": 2, "code_len": (6, 8), "reg_spawn": 3.0,
     "reg_kinds": ["type", "reverse", "math"], "stress_atk": 5, "total_hp": 150},
    {"name": "THE CORE",     "sub": "The core awakens. This ends now.",
     "phases": 5, "codes": 3, "code_len": (7, 10), "reg_spawn": 2.5,
     "reg_kinds": ["type", "reverse", "math", "scramble"], "stress_atk": 8,
     "total_hp": 200},
]
BOSS_AFTER_LEVEL = {2: 0, 4: 1, 6: 2}  # after clearing level index → boss index

# ═══════════════════════════════════════════════════════════════════════════════
#  STORY EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

STORY = [
    # after level 1 (index 0)
    ["[INCOMING TRANSMISSION]", "",
     "\"This is Control. The other operators...\"",
     "\"They didn't make it. You're on your own.\"", "",
     "\"Keep the core stable. We're sending help.\""],
    # after level 2 (index 1)
    ["[SYSTEM ALERT]", "",
     "Coolant reserves critical.",
     "Rerouting auxiliary power to containment.", "",
     "The walls are getting warmer."],
    # after level 3 (index 2)
    ["[TRANSMISSION - STATIC]", "",
     "\"We... *static*... reading massive energy spike...\"",
     "\"Something is in the system. Be ready.\""],
    # after level 4 (index 3)
    ["[PROXIMITY ALERT]", "",
     "Unidentified signal detected on all frequencies.",
     "The station's lights are flickering.", "",
     "Whatever it is, it's getting closer."],
    # after level 5 (index 4)
    ["[CREW LOG - AUTOMATED]", "",
     "Station integrity at minimum threshold.",
     "Automated distress beacon activated.", "",
     "No response from Control for 47 minutes."],
    # after level 6 (index 5)
    ["[FINAL TRANSMISSION]", "",
     "\"If you're still alive in there...\"",
     "\"The core is going critical.\"", "",
     "\"You know what to do. It's all on you now.\""],
    # after level 7 (index 6)
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
#  ACHIEVEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

ACH_DEFS = {
    "first_clear":     ("First Clear",       "Clear your first level"),
    "no_mistakes":     ("No Mistakes",       "Clear a level with zero wrong answers"),
    "perfect_level":   ("Perfect Level",     "Clear a level without hull damage"),
    "speed_solver":    ("Speed Solver",      "Answer an alarm within 1 second"),
    "combo_5":         ("Combo x5",          "Reach a combo of 5"),
    "combo_10":        ("Combo x10",         "Reach a combo of 10"),
    "combo_20":        ("Combo x20",         "Reach a combo of 20"),
    "survive_5":       ("Halfway There",     "Reach level 5"),
    "survive_7":       ("Total Meltdown",    "Survive to level 7"),
    "endless":         ("Endless Survivor",  "Enter endless mode"),
    "endless_5":       ("Endless Warrior",   "Survive 5 endless rounds"),
    "boss_slayer":     ("Boss Slayer",       "Defeat any boss"),
    "all_bosses":      ("Core Crusher",      "Defeat all 3 bosses"),
    "daily_driver":    ("Daily Driver",      "Complete a daily challenge"),
    "powerup_10":      ("Power Player",      "Collect 10 power-ups in one run"),
    "score_5000":      ("High Scorer",       "Reach score 5000"),
    "score_10000":     ("Score Legend",       "Reach score 10000"),
    "nightmare_clear": ("Nightmare Fuel",    "Clear level 1 on Nightmare"),
    "all_types":       ("Polyglot",          "Answer every alarm type in one run"),
}

# ═══════════════════════════════════════════════════════════════════════════════
#  POWER-UP TYPES
# ═══════════════════════════════════════════════════════════════════════════════

POWERUP_TYPES = [
    ("FREEZE", "freeze", "Timers frozen for 5s"),
    ("REPAIR", "repair", "+20 hull integrity"),
    ("CALM",   "calm",   "-30 stress"),
    ("CLEAR",  "clear",  "All alarms cleared"),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  SAVE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

SAVE_DIR = os.path.join(os.path.expanduser("~"), ".meltdown")
SAVE_FILE = os.path.join(SAVE_DIR, "data.json")

DEFAULT_SETTINGS = {
    "sound": True,
    "reduced_flash": False,
    "show_timer_numbers": True,
    "colorblind": False,
    "large_ui": False,
}

DEFAULT_DATA = {
    "scores": [],
    "daily": {},
    "achievements": [],
    "settings": dict(DEFAULT_SETTINGS),
    "lifetime": {
        "total_games": 0, "total_score": 0, "total_correct": 0,
        "total_wrong": 0, "total_missed": 0, "best_combo": 0,
        "fastest_ever": 999.0, "total_play_time": 0.0,
        "bosses_killed": [],
    },
    "save_state": None,
}


class SaveManager:
    def __init__(self):
        self.data = dict(DEFAULT_DATA)
        self._load()

    def _load(self):
        try:
            with open(SAVE_FILE) as f:
                loaded = json.load(f)
            for k in DEFAULT_DATA:
                if k in loaded:
                    if isinstance(DEFAULT_DATA[k], dict) and isinstance(loaded[k], dict):
                        merged = dict(DEFAULT_DATA[k])
                        merged.update(loaded[k])
                        self.data[k] = merged
                    else:
                        self.data[k] = loaded[k]
        except Exception:
            pass
        # Migrate old single-score save
        old = os.path.join(os.path.expanduser("~"), ".meltdown_highscore.json")
        if os.path.exists(old):
            try:
                with open(old) as f:
                    ob = json.load(f)
                if ob.get("best", 0) > 0 and not self.data["scores"]:
                    self.data["scores"].append({
                        "name": "???", "score": ob["best"], "level": 0,
                        "diff": "operator", "date": "legacy", "time": 0})
                os.remove(old)
            except Exception:
                pass

    def save(self):
        try:
            os.makedirs(SAVE_DIR, exist_ok=True)
            with open(SAVE_FILE, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    @property
    def settings(self):
        return self.data["settings"]

    @property
    def scores(self):
        return self.data["scores"]

    @property
    def lifetime(self):
        return self.data["lifetime"]

    def add_score(self, name, score, level, diff, play_time):
        entry = {"name": name, "score": score, "level": level,
                 "diff": diff, "date": date.today().isoformat(),
                 "time": round(play_time, 1)}
        self.data["scores"].append(entry)
        self.data["scores"].sort(key=lambda e: e["score"], reverse=True)
        self.data["scores"] = self.data["scores"][:10]
        self.save()

    def qualifies(self, score):
        if len(self.data["scores"]) < 10:
            return True
        return score > self.data["scores"][-1]["score"]

    def best_score(self):
        return self.data["scores"][0]["score"] if self.data["scores"] else 0

    def unlock(self, ach_id):
        if ach_id not in self.data["achievements"]:
            self.data["achievements"].append(ach_id)
            self.save()
            return True
        return False

    def has_ach(self, ach_id):
        return ach_id in self.data["achievements"]

    def set_daily(self, score, level):
        key = date.today().isoformat()
        cur = self.data["daily"].get(key, {})
        if score > cur.get("score", 0):
            self.data["daily"][key] = {"score": score, "level": level}
            self.save()

    def get_daily(self):
        return self.data["daily"].get(date.today().isoformat())

    def save_state(self, state):
        self.data["save_state"] = state
        self.save()

    def load_state(self):
        return self.data["save_state"]

    def clear_state(self):
        self.data["save_state"] = None
        self.save()

    def update_lifetime(self, stats):
        lt = self.data["lifetime"]
        lt["total_games"] = lt.get("total_games", 0) + 1
        lt["total_score"] = lt.get("total_score", 0) + stats.get("score", 0)
        lt["total_correct"] = lt.get("total_correct", 0) + stats.get("correct", 0)
        lt["total_wrong"] = lt.get("total_wrong", 0) + stats.get("wrong", 0)
        lt["total_missed"] = lt.get("total_missed", 0) + stats.get("missed", 0)
        lt["best_combo"] = max(lt.get("best_combo", 0), stats.get("combo_max", 0))
        fast = stats.get("fastest", 999.0)
        if fast < lt.get("fastest_ever", 999.0):
            lt["fastest_ever"] = fast
        lt["total_play_time"] = lt.get("total_play_time", 0) + stats.get("play_time", 0)
        self.save()


# ═══════════════════════════════════════════════════════════════════════════════
#  STATISTICS TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

class Stats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.correct = 0
        self.wrong = 0
        self.missed = 0
        self.fastest = 999.0
        self.responses = []
        self.combo_max = 0
        self.by_type_ok = {}
        self.by_type_miss = {}
        self.types_answered = set()
        self.powerups = 0
        self.start = time.time()
        self.level_no_mistakes = True
        self.level_no_hull_dmg = True

    def hit(self, kind, resp_time):
        self.correct += 1
        self.fastest = min(self.fastest, resp_time)
        self.responses.append(resp_time)
        self.by_type_ok[kind] = self.by_type_ok.get(kind, 0) + 1
        self.types_answered.add(kind)

    def miss(self, kind):
        self.missed += 1
        self.by_type_miss[kind] = self.by_type_miss.get(kind, 0) + 1
        self.level_no_hull_dmg = False

    def wrong_answer(self):
        self.wrong += 1
        self.level_no_mistakes = False

    def begin_level(self):
        self.level_no_mistakes = True
        self.level_no_hull_dmg = True

    @property
    def accuracy(self):
        t = self.correct + self.wrong
        return (self.correct / t * 100) if t > 0 else 0.0

    @property
    def avg_resp(self):
        return (sum(self.responses) / len(self.responses)) if self.responses else 0.0

    @property
    def play_time(self):
        return time.time() - self.start

    @property
    def worst_type(self):
        if not self.by_type_miss:
            return "none"
        return max(self.by_type_miss, key=self.by_type_miss.get)

    def to_dict(self):
        return {"correct": self.correct, "wrong": self.wrong,
                "missed": self.missed, "fastest": self.fastest,
                "combo_max": self.combo_max, "play_time": self.play_time,
                "score": 0}


# ═══════════════════════════════════════════════════════════════════════════════
#  SOUND
# ═══════════════════════════════════════════════════════════════════════════════

class Sound:
    enabled = True

    @staticmethod
    def beep():
        if Sound.enabled:
            try:
                curses.beep()
            except Exception:
                pass

    @staticmethod
    def wrong():
        Sound.beep()

    @staticmethod
    def expire():
        Sound.beep()

    @staticmethod
    def surge():
        Sound.beep()

    @staticmethod
    def boss():
        Sound.beep()


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


# ═══════════════════════════════════════════════════════════════════════════════
#  ALARM
# ═══════════════════════════════════════════════════════════════════════════════

class Alarm:
    def __init__(self, kind, ttl, now):
        self.kind = kind
        self.ttl = ttl
        self.born = now
        self.hide_after = None
        self.is_boss = False
        self.is_powerup = False

        if kind == "type":
            w = random.choice(WORDS)
            self.label, self.text, self.answer = "TYPE", w.upper(), w
        elif kind == "reverse":
            w = random.choice(WORDS)
            self.label, self.text, self.answer = "REVERSE", w.upper(), w[::-1]
        elif kind == "scramble":
            w = random.choice(WORDS)
            letters = list(w)
            for _ in range(20):
                random.shuffle(letters)
                if "".join(letters) != w:
                    break
            self.label, self.text, self.answer = "UNSCRAMBLE", "".join(letters).upper(), w
        elif kind == "math":
            a, b = random.randint(3, 15), random.randint(2, 12)
            op = random.choice("+-*")
            res = {"+": a + b, "-": a - b, "*": a * b}[op]
            self.label, self.text, self.answer = "SOLVE", f"{a} {op} {b}", str(res)
        elif kind == "memory":
            code = "".join(random.choice("0123456789") for _ in range(random.randint(4, 6)))
            self.label, self.text, self.answer = "MEMORIZE", code, code
            self.hide_after = now + 2.0
        elif kind == "sequence":
            start = random.randint(1, 10)
            step = random.randint(2, 5)
            seq = [start + step * i for i in range(4)]
            nxt = start + step * 4
            self.label = "SEQUENCE"
            self.text = ", ".join(str(x) for x in seq) + ", ?"
            self.answer = str(nxt)
        elif kind == "binary":
            num = random.randint(3, 63)
            self.label, self.text, self.answer = "BINARY", bin(num)[2:], str(num)
        elif kind == "morse":
            w = random.choice(SHORT_WORDS)
            m = "  ".join(MORSE.get(c.upper(), "?") for c in w)
            self.label, self.text, self.answer = "MORSE", m, w
        elif kind == "decode":
            w = random.choice(WORDS)
            def _corrupt(word):
                chars = list(word.upper())
                n = max(1, len(word) // 3)
                for p in random.sample(range(len(word)), min(n, len(word))):
                    chars[p] = random.choice("#@$%&?!")
                return "".join(chars)
            c1 = _corrupt(w)
            c2 = _corrupt(w)
            for _ in range(10):
                if c2 != c1:
                    break
                c2 = _corrupt(w)
            self.label, self.text, self.answer = "DECODE", f"{c1} | {c2}", w
        elif kind == "seqlock":
            dirs = "".join(random.choice("udlr") for _ in range(random.randint(4, 7)))
            self.label, self.text, self.answer = "SEQ LOCK", dirs.upper(), dirs
            self.hide_after = now + 2.5
        else:
            w = random.choice(WORDS)
            self.label, self.text, self.answer = "TYPE", w.upper(), w

    def shown(self, now):
        if self.hide_after and now > self.hide_after:
            return "*" * len(self.text)
        return self.text

    @staticmethod
    def make_boss_code(length, ttl, now):
        chars = "abcdefghjkmnpqrstuvwxyz23456789"
        code = "".join(random.choice(chars) for _ in range(length))
        a = Alarm.__new__(Alarm)
        a.kind = "boss"
        a.ttl = ttl
        a.born = now
        a.hide_after = None
        a.is_boss = True
        a.is_powerup = False
        a.label = "BOSS CODE"
        a.text = code.upper()
        a.answer = code
        return a

    @staticmethod
    def make_powerup(ptype, ttl, now):
        name, keyword, desc = ptype
        a = Alarm.__new__(Alarm)
        a.kind = "powerup"
        a.ttl = ttl
        a.born = now
        a.hide_after = None
        a.is_boss = False
        a.is_powerup = True
        a.label = f">> {name} <<"
        a.text = keyword.upper()
        a.answer = keyword
        a.pup_name = name
        a.pup_desc = desc
        return a


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
        self.mode = "solo"       # solo, coop, versus
        self.stats = Stats()
        self.ach_queue = []      # pending achievement unlock messages
        self.ttl_bonus = 0.0     # bonus seconds from story choices
        self.score_mult = 1.0    # score multiplier from story choices
        self.pup_bonus = 0.0     # extra power-up chance from choices
        self.freeze_until = 0.0
        self.daily = False
        # co-op state
        self.active_p = 0        # 0=P1, 1=P2
        self.p_combos = [0, 0]
        self.p_scores = [0, 0]
        self.p_bufs = ["", ""]

    # ── drawing helpers ─────────────────────────────────────────────────────

    def put(self, y, x, text, attr=0):
        try:
            if 0 <= y < self.h and 0 <= x < self.w:
                self.s.addstr(y, max(0, x), text[:max(0, self.w - x - 1)], attr)
        except curses.error:
            pass

    def center(self, y, text, attr=0):
        self.put(y, max(0, (self.w - len(text)) // 2), text, attr)

    def bar(self, y, x, label, frac, width, col, show_num=False):
        frac = max(0.0, min(1.0, frac))
        filled = int(frac * width)
        self.put(y, x, label)
        bar_text = "[" + "#" * filled + "-" * (width - filled) + "]"
        if show_num and self.sm.settings.get("show_timer_numbers", True):
            bar_text += f" {frac * 100:3.0f}%"
        self.put(y, x + len(label), bar_text, col)

    def _cb(self, frac):
        """Colorblind-safe prefix."""
        if not self.sm.settings.get("colorblind", False):
            return ""
        if frac > 0.5:
            return "+"
        elif frac > 0.25:
            return "~"
        return "!"

    def screen(self, lines, wait_key=True):
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()
        top = max(1, (self.h - len(lines)) // 2)
        for i, (txt, attr) in enumerate(lines):
            self.center(top + i, txt, attr)
        self.s.refresh()
        if wait_key:
            self.s.nodelay(False)
            self.s.getch()
            self.s.nodelay(True)
        else:
            time.sleep(1.8)
        curses.flushinp()

    def C(self, n):
        """Safe color pair."""
        try:
            return curses.color_pair(n)
        except Exception:
            return 0

    # ── menus ───────────────────────────────────────────────────────────────

    def menu(self, title, options, subtitle=""):
        sel = 0
        self.s.nodelay(False)
        curses.curs_set(0)
        while True:
            self.s.erase()
            self.h, self.w = self.s.getmaxyx()
            top = max(1, (self.h - len(options) - 6) // 2)
            self.center(top, title, self.C(3) | curses.A_BOLD)
            if subtitle:
                self.center(top + 1, subtitle, self.C(4))
            base = top + 3
            for i, opt in enumerate(options):
                attr = curses.A_REVERSE | curses.A_BOLD if i == sel else 0
                self.center(base + i, f"  {opt}  ", attr)
            self.center(min(self.h - 2, base + len(options) + 2),
                        "Up/Down: Navigate   Enter: Select   Esc: Back", self.C(4))
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

    def get_initials(self):
        """Prompt for 3-letter initials."""
        buf = ""
        self.s.nodelay(False)
        while True:
            self.s.erase()
            self.h, self.w = self.s.getmaxyx()
            mid = self.h // 2
            self.center(mid - 2, "NEW HIGH SCORE!", self.C(1) | curses.A_BOLD)
            self.center(mid, f"Enter initials: {buf}_", curses.A_BOLD)
            self.center(mid + 2, "(3 letters, then Enter)", self.C(4))
            self.s.refresh()
            ch = self.s.getch()
            if ch in (10, 13, curses.KEY_ENTER) and len(buf) >= 1:
                return buf.upper()[:3]
            elif ch in (8, 127, curses.KEY_BACKSPACE):
                buf = buf[:-1]
            elif 32 <= ch < 127 and len(buf) < 3:
                c = chr(ch)
                if c.isalpha():
                    buf += c.upper()

    # ── main menu ───────────────────────────────────────────────────────────

    def main_menu(self):
        while True:
            opts = ["New Game"]
            has_save = self.sm.load_state() is not None
            if has_save:
                opts.append("Continue")
            opts += ["Daily Challenge", "Leaderboard", "Achievements",
                     "Statistics", "Settings", "Quit"]
            choice = self.menu("M E L T D O W N", opts,
                               "The station is failing. You are the only operator left.")
            if choice == -1 or opts[choice] == "Quit":
                return "quit"
            picked = opts[choice]
            if picked == "New Game":
                self.new_game_flow()
            elif picked == "Continue":
                self.continue_game()
            elif picked == "Daily Challenge":
                self.play_daily()
            elif picked == "Leaderboard":
                self.show_leaderboard()
            elif picked == "Achievements":
                self.show_achievements()
            elif picked == "Statistics":
                self.show_statistics()
            elif picked == "Settings":
                self.settings_menu()

    def new_game_flow(self):
        # difficulty
        di = self.menu("SELECT DIFFICULTY", ["Casual", "Operator", "Nightmare"],
                       "Choose your pain level")
        if di == -1:
            return
        self.diff = ["casual", "operator", "nightmare"][di]
        # mode
        mi = self.menu("SELECT MODE", ["Solo", "Co-op (2 Players)", "Versus (2 Players)"],
                       "How many operators?")
        if mi == -1:
            return
        self.mode = ["solo", "coop", "versus"][mi]
        if self.mode == "versus":
            return self.play_versus()
        return self.play()

    # ── settings ────────────────────────────────────────────────────────────

    def settings_menu(self):
        keys = ["sound", "reduced_flash", "show_timer_numbers", "colorblind", "large_ui"]
        labels = ["Sound Effects", "Reduced Flashing", "Show Timer Numbers",
                  "Colorblind Mode", "Large UI"]
        while True:
            opts = []
            for k, lb in zip(keys, labels):
                v = self.sm.settings.get(k, DEFAULT_SETTINGS.get(k, False))
                opts.append(f"{lb}: {'ON' if v else 'OFF'}")
            opts.append("Back")
            ch = self.menu("SETTINGS", opts, "Toggle options")
            if ch == -1 or ch == len(keys):
                Sound.enabled = self.sm.settings.get("sound", True)
                self.sm.save()
                return
            k = keys[ch]
            self.sm.settings[k] = not self.sm.settings.get(k, DEFAULT_SETTINGS.get(k, False))

    # ── leaderboard ─────────────────────────────────────────────────────────

    def show_leaderboard(self):
        self.s.nodelay(False)
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()
        self.center(1, "LEADERBOARD", self.C(2) | curses.A_BOLD)
        self.center(2, "-" * 50, self.C(4))
        row = 4
        self.put(row, 2, f"{'#':<4}{'NAME':<6}{'SCORE':<10}{'LVL':<6}{'DIFF':<12}{'DATE'}", self.C(4))
        row += 1
        if not self.sm.scores:
            self.center(row + 2, "No scores yet. Go play!", self.C(4))
        for i, e in enumerate(self.sm.scores[:10]):
            self.put(row + i, 2,
                     f"{i+1:<4}{e.get('name','???'):<6}{e.get('score',0):<10}"
                     f"{e.get('level',0):<6}{e.get('diff','?'):<12}{e.get('date','?')}")
        # daily
        daily = self.sm.get_daily()
        dy = row + 12
        self.center(dy, "TODAY'S DAILY CHALLENGE", self.C(2) | curses.A_BOLD)
        if daily:
            self.center(dy + 1, f"Best: {daily['score']}  Level: {daily['level']}")
        else:
            self.center(dy + 1, "Not attempted yet", self.C(4))
        self.center(self.h - 2, "Press any key...", self.C(4))
        self.s.refresh()
        self.s.getch()

    # ── achievements ────────────────────────────────────────────────────────

    def show_achievements(self):
        self.s.nodelay(False)
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()
        self.center(1, "ACHIEVEMENTS", self.C(2) | curses.A_BOLD)
        unlocked = self.sm.data.get("achievements", [])
        total = len(ACH_DEFS)
        got = sum(1 for k in ACH_DEFS if k in unlocked)
        self.center(2, f"{got}/{total} unlocked", self.C(4))
        row = 4
        for aid, (name, desc) in ACH_DEFS.items():
            if row >= self.h - 3:
                break
            done = aid in unlocked
            mark = "[*]" if done else "[ ]"
            col = self.C(1) if done else self.C(4)
            self.put(row, 2, f"{mark} {name}: {desc}", col)
            row += 1
        self.center(self.h - 2, "Press any key...", self.C(4))
        self.s.refresh()
        self.s.getch()

    # ── statistics ──────────────────────────────────────────────────────────

    def show_statistics(self):
        self.s.nodelay(False)
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()
        lt = self.sm.lifetime
        self.center(1, "LIFETIME STATISTICS", self.C(2) | curses.A_BOLD)
        lines = [
            f"Games Played:     {lt.get('total_games', 0)}",
            f"Total Score:      {lt.get('total_score', 0)}",
            f"Alarms Answered:  {lt.get('total_correct', 0)}",
            f"Wrong Answers:    {lt.get('total_wrong', 0)}",
            f"Alarms Missed:    {lt.get('total_missed', 0)}",
            f"Best Combo:       x{lt.get('best_combo', 0)}",
            f"Fastest Answer:   {lt.get('fastest_ever', 0):.2f}s" if lt.get('fastest_ever', 999) < 999 else "Fastest Answer:   ---",
            f"Total Play Time:  {lt.get('total_play_time', 0) / 60:.1f} min",
            f"Bosses Defeated:  {len(lt.get('bosses_killed', []))}",
        ]
        for i, line in enumerate(lines):
            self.put(4 + i, 4, line)
        acc = 0
        tc = lt.get("total_correct", 0)
        tw = lt.get("total_wrong", 0)
        if tc + tw > 0:
            acc = tc / (tc + tw) * 100
        self.put(4 + len(lines) + 1, 4, f"Lifetime Accuracy: {acc:.1f}%", self.C(1) if acc > 70 else self.C(2))
        self.center(self.h - 2, "Press any key...", self.C(4))
        self.s.refresh()
        self.s.getch()

    # ── game-over stats screen ──────────────────────────────────────────────

    def show_game_stats(self):
        self.s.nodelay(False)
        self.s.erase()
        self.h, self.w = self.s.getmaxyx()
        st = self.stats
        self.center(1, "MISSION REPORT", self.C(2) | curses.A_BOLD)
        lines = [
            f"Score:           {self.score}",
            f"Accuracy:        {st.accuracy:.1f}%",
            f"Correct:         {st.correct}",
            f"Wrong:           {st.wrong}",
            f"Missed:          {st.missed}",
            f"Longest Combo:   x{st.combo_max}",
            f"Fastest Answer:  {st.fastest:.2f}s" if st.fastest < 999 else "Fastest Answer:  ---",
            f"Avg Response:    {st.avg_resp:.2f}s" if st.responses else "Avg Response:    ---",
            f"Most Missed:     {st.worst_type.upper()}",
            f"Power-ups Used:  {st.powerups}",
            f"Survival Time:   {st.play_time:.0f}s",
        ]
        for i, line in enumerate(lines):
            self.put(4 + i, 4, line)
        # show newly unlocked achievements
        if self.ach_queue:
            ay = 4 + len(lines) + 1
            self.center(ay, "ACHIEVEMENTS UNLOCKED:", self.C(1) | curses.A_BOLD)
            for j, aid in enumerate(self.ach_queue[:4]):
                name = ACH_DEFS.get(aid, ("?", ""))[0]
                self.center(ay + 1 + j, f"  * {name}", self.C(1))
        self.center(self.h - 2, "Press any key...", self.C(4))
        self.s.refresh()
        self.s.getch()
        self.ach_queue.clear()

    # ── story events ────────────────────────────────────────────────────────

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

    # ── achievement checker ─────────────────────────────────────────────────

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

    # ── pause menu ──────────────────────────────────────────────────────────

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
        elif ch == 3:
            return "quit"
        return "resume"

    # ── run one level ───────────────────────────────────────────────────────

    def run_level(self, idx):
        name, _, quota, spawn, ttl, max_active, pressure, kinds, glitch, surge = level_cfg(idx)
        self.stats.begin_level()

        # apply difficulty
        d = DIFFICULTY[self.diff]
        spawn *= d["spawn"]
        ttl *= d["ttl"]
        ttl += self.ttl_bonus
        pressure *= d["stress"]
        hull_dmg = d["hull_dmg"]
        pup_chance = d["pup"] + self.pup_bonus

        # apply large UI
        if self.sm.settings.get("large_ui", False):
            max_active = max(2, max_active - 1)

        alarms = []
        cleared = 0
        # input buffer (single or coop)
        if self.mode == "coop":
            bufs = list(self.p_bufs)
        else:
            bufs = [""]
        msg, msg_until, msg_col = "", 0, 0
        last = time.time()
        next_spawn = last + 1.0
        next_glitch = last + random.uniform(8, 14)
        glitch_until = 0.0
        next_pup = last + random.uniform(12, 25)
        ach_msg, ach_msg_until = "", 0.0

        reduced = self.sm.settings.get("reduced_flash", False)
        show_nums = self.sm.settings.get("show_timer_numbers", True)
        large = self.sm.settings.get("large_ui", False)
        alarm_rows = 4 if large else 3

        G, Y, R, C, M, W = (self.C(i) for i in (1, 2, 3, 4, 5, 6))

        # Reset per-level bonuses after use
        self.ttl_bonus = 0.0
        score_mult = self.score_mult
        self.score_mult = 1.0
        self.pup_bonus = 0.0

        self.s.nodelay(True)

        while True:
            now = time.time()
            dt = now - last
            last = now
            self.h, self.w = self.s.getmaxyx()

            # ── input ──
            while True:
                ch = self.s.getch()
                if ch == -1:
                    break
                # pause
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
                    if self.freeze_until > pause_start:
                        self.freeze_until += pause_dur
                    for a in alarms:
                        a.born += pause_dur
                        if a.hide_after:
                            a.hide_after += pause_dur
                    if res == "quit":
                        self._auto_save(idx)
                        return "quit"
                    elif res == "restart":
                        return "restart"
                    continue

                # coop: tab switches player
                if self.mode == "coop" and ch == 9:
                    self.active_p = 1 - self.active_p
                    continue

                bp = self.active_p if self.mode == "coop" else 0

                if ch in (10, 13, curses.KEY_ENTER):
                    guess = bufs[bp].strip().lower()
                    bufs[bp] = ""
                    if not guess:
                        continue

                    # check power-ups first
                    pup_hits = [a for a in alarms if a.is_powerup and a.answer == guess]
                    if pup_hits:
                        a = pup_hits[0]
                        alarms.remove(a)
                        self.stats.powerups += 1
                        cleared += self._apply_powerup(a.pup_name, alarms, now)
                        msg = f"POWER-UP: {a.pup_desc}"
                        msg_col, msg_until = self.C(4), now + 2.0
                        self.check_ach(powerups=self.stats.powerups)
                        continue

                    # check boss codes
                    boss_hits = [a for a in alarms if a.is_boss and a.answer == guess]
                    if boss_hits:
                        a = min(boss_hits, key=lambda x: x.born + x.ttl)
                        alarms.remove(a)
                        resp = now - a.born
                        self.stats.hit("boss", resp)
                        pts = int(200 * (1 + self.combo * 0.25) * score_mult)
                        self.combo += 1
                        if self.mode == "coop":
                            self.p_combos[bp] += 1
                            self.p_scores[bp] += pts
                        self.score += pts
                        self.stress = max(0, self.stress - 12)
                        self.stats.combo_max = max(self.stats.combo_max, self.combo)
                        msg = f"+{pts}  BOSS HIT!  COMBO x{self.combo}"
                        msg_col, msg_until = M, now + 1.5
                        self.check_ach(combo=self.combo, speed=resp)
                        continue

                    # check normal alarms
                    normal = [a for a in alarms if not a.is_boss and not a.is_powerup]
                    hits = [a for a in normal if a.answer == guess]
                    if hits:
                        a = min(hits, key=lambda x: x.born + x.ttl)
                        alarms.remove(a)
                        cleared += 1
                        resp = now - a.born
                        remaining = max(0, (a.born + a.ttl - now) / a.ttl)
                        pts = int(100 * (1 + self.combo * 0.25) * (0.5 + remaining) * score_mult)
                        self.combo += 1
                        if self.mode == "coop":
                            self.p_combos[bp] += 1
                            self.p_scores[bp] += pts
                        self.score += pts
                        self.stress = max(0, self.stress - 9)
                        self.stats.hit(a.kind, resp)
                        self.stats.combo_max = max(self.stats.combo_max, self.combo)
                        msg = f"+{pts}  COMBO x{self.combo}"
                        msg_col, msg_until = G, now + 1.2
                        self.check_ach(combo=self.combo, speed=resp)
                    else:
                        self.combo = 0
                        if self.mode == "coop":
                            self.p_combos[bp] = 0
                        self.stress += 10 * DIFFICULTY[self.diff]["stress"]
                        self.stats.wrong_answer()
                        msg, msg_col, msg_until = "WRONG! stress up", R, now + 1.2
                        Sound.wrong()

                elif ch in (8, 127, curses.KEY_BACKSPACE):
                    bufs[bp] = bufs[bp][:-1]
                elif 32 <= ch < 127 and len(bufs[bp]) < 30:
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
            need = quota - cleared - sum(1 for a in alarms if not a.is_boss and not a.is_powerup)
            if now >= next_spawn and need > 0:
                active_normal = sum(1 for a in alarms if not a.is_boss and not a.is_powerup)
                if active_normal < max_active:
                    count = 1
                    if surge and random.random() < 0.18:
                        count = min(3, need, max_active - active_normal)
                        msg, msg_col, msg_until = "!! SURGE !!", R, now + 1.5
                        Sound.surge()
                    for _ in range(count):
                        alarms.append(Alarm(random.choice(kinds), ttl, now))
                    next_spawn = now + spawn * random.uniform(0.6, 1.4)

            # ── power-up spawn ──
            if now >= next_pup and random.random() < pup_chance:
                pt = random.choice(POWERUP_TYPES)
                alarms.append(Alarm.make_powerup(pt, ttl * 0.8, now))
                next_pup = now + random.uniform(15, 30)
            elif now >= next_pup:
                next_pup = now + random.uniform(8, 15)

            # ── glitch ──
            if glitch and not reduced and now >= next_glitch:
                glitch_until = now + 4
                next_glitch = now + random.uniform(12, 20)
                msg, msg_col, msg_until = "DISPLAY CORRUPTED!", Y, now + 2

            # ── expiry / stress ──
            for a in alarms[:]:
                elapsed = now - a.born if not frozen else max(0, self.freeze_until - ttl - a.born)
                if not frozen and now >= a.born + a.ttl:
                    alarms.remove(a)
                    if a.is_powerup:
                        continue
                    if a.is_boss:
                        self.hull -= hull_dmg
                        self.stress += 15
                        msg, msg_col, msg_until = "BOSS CODE EXPIRED!", R, now + 1.5
                        Sound.expire()
                        continue
                    self.hull -= hull_dmg
                    self.stress += 12 * DIFFICULTY[self.diff]["stress"]
                    self.combo = 0
                    if self.mode == "coop":
                        self.p_combos = [0, 0]
                    cleared += 1
                    self.stats.miss(a.kind)
                    msg, msg_col, msg_until = "ALARM MISSED! hull damaged", R, now + 1.5
                    Sound.expire()

            if not frozen:
                active_stress = sum(1 for a in alarms if not a.is_powerup)
                if active_stress > 0:
                    self.stress += dt * active_stress * pressure
                else:
                    self.stress -= dt * 4
            self.stress = max(0.0, min(100.0, self.stress))

            if self.hull <= 0 or self.stress >= 100:
                return "dead"
            normal_left = sum(1 for a in alarms if not a.is_boss and not a.is_powerup)
            if cleared >= quota and normal_left == 0:
                return "clear"

            # ── draw ──
            self.s.erase()
            panic = not reduced and self.stress > 80 and int(now * 5) % 2 == 0
            title_str = f" MELTDOWN :: LVL {idx + 1} {name} "
            if self.daily:
                title_str = f" DAILY CHALLENGE :: LVL {idx + 1} {name} "
            self.put(0, 0, title_str.ljust(self.w - 1),
                     curses.A_REVERSE | (R if panic else C))

            # score line
            best = max(self.sm.best_score(), self.score)
            info = f"SCORE {self.score}   BEST {best}   COMBO x{self.combo}   {min(cleared,quota)}/{quota}"
            if self.mode == "coop":
                info += f"   P1:{self.p_scores[0]} P2:{self.p_scores[1]}"
            self.put(1, 0, info)

            bw = max(10, min(40, self.w - 20))
            scol = G if self.stress < 50 else (Y if self.stress < 80 else R)
            hcol = G if self.hull > 60 else (Y if self.hull > 30 else R)
            sfrac = self.stress / 100
            hfrac = self.hull / 100
            cb = self.sm.settings.get("colorblind", False)
            slbl = f"{'!' if cb and sfrac>0.75 else '~' if cb and sfrac>0.5 else ''}STRESS "
            hlbl = f"{'!' if cb and hfrac<0.25 else '~' if cb and hfrac<0.5 else ''}HULL   "
            self.bar(3, 0, slbl, sfrac, bw, scol, show_nums)
            self.bar(4, 0, hlbl, hfrac, bw, hcol, show_nums)

            if frozen:
                self.put(5, 0, "** TIMERS FROZEN **", C | curses.A_BOLD)

            row = 6
            for a in sorted(alarms, key=lambda x: x.born + x.ttl):
                if frozen and not a.is_powerup:
                    left = a.ttl - (self.freeze_until - a.born - a.ttl)
                    left = max(0.1, a.born + a.ttl - self.freeze_until + (now - self.freeze_until) if now > self.freeze_until else a.ttl)
                    frac = max(0.01, min(1.0, (a.born + a.ttl - now) / a.ttl))
                else:
                    left = a.born + a.ttl - now
                    frac = max(0.01, left / a.ttl) if a.ttl > 0 else 0.01

                txt = a.shown(now)
                if not reduced and now < glitch_until and not a.is_powerup:
                    rng = random.Random(int(now * 4) + id(a) % 97)
                    txt = "".join(c if c == " " or rng.random() > 0.3
                                 else rng.choice("#@%&?!$") for c in txt)

                if a.is_powerup:
                    col = C | curses.A_BOLD
                elif a.is_boss:
                    col = M | curses.A_BOLD
                else:
                    col = G if frac > 0.5 else (Y if frac > 0.25 else R)

                pre = self._cb(frac) if not a.is_powerup and not a.is_boss else ""
                self.put(row, 0, f" {pre}{a.label:<11} {txt}", col)
                timer_lbl = "   time "
                if show_nums:
                    secs = max(0, left)
                    timer_lbl = f"  {secs:4.1f}s "
                self.bar(row + 1, 0, timer_lbl, frac, max(8, min(30, self.w - 14)), col)
                row += alarm_rows
                if row >= self.h - 4:
                    break

            # messages
            if now < msg_until:
                self.put(self.h - 4, 0, msg, msg_col | curses.A_BOLD)

            # achievement flash
            if now < ach_msg_until:
                self.put(self.h - 5, 0, ach_msg, self.C(1) | curses.A_BOLD)
            elif self.ach_queue:
                aid = self.ach_queue[-1]
                aname = ACH_DEFS.get(aid, ("?",))[0]
                ach_msg = f"ACHIEVEMENT UNLOCKED: {aname}!"
                ach_msg_until = now + 3.0

            # input line
            if self.mode == "coop":
                plbl = f"P{self.active_p + 1}> "
                self.put(self.h - 2, 0, plbl + bufs[self.active_p])
                cursor_x = len(plbl) + len(bufs[self.active_p])
            else:
                self.put(self.h - 2, 0, "> " + bufs[0])
                cursor_x = 2 + len(bufs[0])
            try:
                self.s.move(self.h - 2, min(self.w - 2, cursor_x))
            except curses.error:
                pass
            self.s.refresh()
            time.sleep(0.03)

    def _apply_powerup(self, name, alarms, now):
        if name == "FREEZE":
            self.freeze_until = now + 5.0
        elif name == "REPAIR":
            self.hull = min(100, self.hull + 20)
        elif name == "CALM":
            self.stress = max(0, self.stress - 30)
        elif name == "CLEAR":
            to_remove = [a for a in alarms if not a.is_boss and not a.is_powerup]
            for a in to_remove:
                alarms.remove(a)
            return len(to_remove)
        return 0

    def _auto_save(self, level_idx):
        state = {
            "level": level_idx, "score": self.score, "hull": self.hull,
            "stress": self.stress, "combo": self.combo, "diff": self.diff,
            "mode": self.mode, "stats": self.stats.to_dict(),
        }
        self.sm.save_state(state)

    # ── boss fight ──────────────────────────────────────────────────────────

    def run_boss(self, boss_idx):
        b = BOSSES[boss_idx]
        self.screen([
            (f"BOSS FIGHT", self.C(5) | curses.A_BOLD),
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

        # spawn initial boss codes
        for _ in range(codes_per):
            length = random.randint(code_lo, code_hi)
            alarms.append(Alarm.make_boss_code(length, boss_ttl, last))

        G, Y, R, C, M, W = (self.C(i) for i in (1, 2, 3, 4, 5, 6))
        self.s.nodelay(True)

        while True:
            now = time.time()
            dt = now - last
            last = now
            self.h, self.w = self.s.getmaxyx()

            # input
            while True:
                ch = self.s.getch()
                if ch == -1:
                    break
                if ch == 27:
                    res = self.pause_menu()
                    self.s.nodelay(True)
                    curses.flushinp()
                    last = time.time()
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
                    # boss codes
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
                        dmg = boss_max_hp // total_phases
                        boss_hp -= dmg
                        msg = f"+{pts}  BOSS DAMAGED!  HP: {max(0,boss_hp)}/{boss_max_hp}"
                        msg_col, msg_until = M, now + 1.5
                        self.check_ach(combo=self.combo, speed=resp)

                        if phase_codes_left <= 0:
                            phase += 1
                            if phase >= total_phases or boss_hp <= 0:
                                # boss defeated
                                boss_hp = 0
                                break
                            phase_codes_left = codes_per
                            boss_ttl = max(15, boss_ttl - 2)
                            for _ in range(codes_per):
                                length = random.randint(code_lo, code_hi)
                                alarms.append(Alarm.make_boss_code(length, boss_ttl, now))
                            msg = f"PHASE {phase+1}/{total_phases}!"
                            msg_col, msg_until = M, now + 2.0
                            Sound.boss()
                        continue

                    # regular alarms
                    hits = [a for a in alarms if not a.is_boss and a.answer == guess]
                    if hits:
                        a = min(hits, key=lambda x: x.born + x.ttl)
                        alarms.remove(a)
                        resp = now - a.born
                        pts = int(100 * (1 + self.combo * 0.25))
                        self.combo += 1
                        self.score += pts
                        self.stress = max(0, self.stress - 9)
                        self.stats.hit(a.kind, resp)
                        self.stats.combo_max = max(self.stats.combo_max, self.combo)
                        msg = f"+{pts}  COMBO x{self.combo}"
                        msg_col, msg_until = G, now + 1.2
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

            # regular alarm spawn
            active_reg = sum(1 for a in alarms if not a.is_boss)
            if now >= next_spawn and active_reg < 3:
                alarms.append(Alarm(random.choice(reg_kinds),
                                    10 * d["ttl"], now))
                next_spawn = now + reg_spawn * random.uniform(0.7, 1.3)

            # boss stress attack
            if stress_atk > 0 and now >= next_stress_atk:
                self.stress += stress_atk
                msg = f"BOSS ATTACKS! +{stress_atk} stress"
                msg_col, msg_until = R, now + 1.5
                next_stress_atk = now + random.uniform(6, 12)

            # expiry
            for a in alarms[:]:
                if now >= a.born + a.ttl:
                    alarms.remove(a)
                    if a.is_boss:
                        self.hull -= 20
                        self.stress += 15
                        phase_codes_left -= 1
                        if phase_codes_left <= 0:
                            phase += 1
                            if phase >= total_phases:
                                break
                            phase_codes_left = codes_per
                            for _ in range(codes_per):
                                length = random.randint(code_lo, code_hi)
                                alarms.append(Alarm.make_boss_code(length, boss_ttl, now))
                        msg, msg_col, msg_until = "BOSS CODE EXPIRED!", R, now + 1.5
                    else:
                        self.hull -= d["hull_dmg"]
                        self.stress += 12
                        self.combo = 0
                    Sound.expire()

            active_stress_count = len(alarms)
            if active_stress_count > 0:
                self.stress += dt * active_stress_count * 1.2
            self.stress = max(0.0, min(100.0, self.stress))

            if self.hull <= 0 or self.stress >= 100:
                return "dead"

            # check if boss done (from inner break)
            if boss_hp <= 0 or phase >= total_phases:
                break

            # draw
            self.s.erase()
            self.put(0, 0, f" BOSS: {b['name']} ".ljust(self.w - 1),
                     curses.A_REVERSE | M)
            boss_frac = max(0, boss_hp / boss_max_hp)
            self.put(1, 0, f"Phase {phase+1}/{total_phases}   "
                           f"SCORE {self.score}   COMBO x{self.combo}")
            self.bar(3, 0, "BOSS HP ", boss_frac,
                     max(10, min(40, self.w - 20)), M)
            bw = max(10, min(40, self.w - 20))
            scol = G if self.stress < 50 else (Y if self.stress < 80 else R)
            hcol = G if self.hull > 60 else (Y if self.hull > 30 else R)
            self.bar(4, 0, "STRESS  ", self.stress / 100, bw, scol)
            self.bar(5, 0, "HULL    ", self.hull / 100, bw, hcol)

            row = 7
            for a in sorted(alarms, key=lambda x: (0 if x.is_boss else 1, x.born + x.ttl)):
                left = a.born + a.ttl - now
                frac = max(0.01, left / a.ttl) if a.ttl > 0 else 0.01
                txt = a.shown(now)
                col = M | curses.A_BOLD if a.is_boss else (G if frac > 0.5 else (Y if frac > 0.25 else R))
                self.put(row, 0, f" {a.label:<11} {txt}", col)
                self.bar(row + 1, 0, "   time ", frac, max(8, min(30, self.w - 14)), col)
                row += 3
                if row >= self.h - 4:
                    break

            if now < msg_until:
                self.put(self.h - 3, 0, msg, msg_col | curses.A_BOLD)
            self.put(self.h - 2, 0, "> " + buf)
            try:
                self.s.move(self.h - 2, min(self.w - 2, 2 + len(buf)))
            except curses.error:
                pass
            self.s.refresh()
            time.sleep(0.03)

        # boss defeated!
        self.check_ach(boss_kill=True, boss_idx=boss_idx)
        bonus = 1000 * (boss_idx + 1)
        self.score += bonus
        self.hull = min(100, self.hull + 15)
        self.stress = max(0, self.stress - 25)
        self.screen([
            (f"BOSS DEFEATED!", self.C(1) | curses.A_BOLD),
            (b["name"], self.C(5) | curses.A_BOLD),
            ("", 0),
            (f"Bonus: +{bonus}", 0),
            ("Hull repaired. Stress reduced.", 0),
            ("", 0),
            ("Press any key...", self.C(2)),
        ])
        return "clear"

    # ── main play loop ──────────────────────────────────────────────────────

    def play(self):
        self.score, self.combo, self.stress, self.hull = 0, 0, 0.0, 100.0
        self.stats.reset()
        self.ach_queue.clear()
        self.freeze_until = 0.0
        self.ttl_bonus = 0.0
        self.score_mult = 1.0
        self.pup_bonus = 0.0

        if self.mode == "coop":
            self.p_combos = [0, 0]
            self.p_scores = [0, 0]
            self.p_bufs = ["", ""]
            self.active_p = 0

        self.sm.clear_state()
        idx = 0

        while True:
            name, flavour, *_ = level_cfg(idx)
            self.screen([(f"LEVEL {idx + 1}", self.C(4) | curses.A_BOLD),
                         (name, self.C(3) | curses.A_BOLD), ("", 0),
                         (flavour, 0),
                         ("", 0),
                         (f"Difficulty: {DIFFICULTY[self.diff]['label']}", self.C(2))],
                        wait_key=False)
            result = self.run_level(idx)

            if result == "dead":
                return self._finish_game(idx, "dead")
            if result == "quit":
                return "quit"
            if result == "restart":
                return self.play()

            # level cleared
            bonus = 500 * (idx + 1)
            self.score += bonus
            self.hull = min(100, self.hull + 10)
            self.stress = max(0, self.stress - 30)
            self.check_ach(level_clear=True, level=idx, check_all_types=True)
            self._auto_save(idx + 1)

            self.screen([(f"LEVEL {idx + 1} CLEARED", self.C(1) | curses.A_BOLD),
                         (f"Bonus +{bonus}   Hull repaired", 0), ("", 0),
                         ("Press any key for next...", 0)])

            # story events
            self.show_story(idx)
            self.show_choice(idx)

            # boss check
            if idx in BOSS_AFTER_LEVEL:
                br = self.run_boss(BOSS_AFTER_LEVEL[idx])
                if br == "dead":
                    return self._finish_game(idx, "dead")
                if br == "quit":
                    return "quit"
                if br == "restart":
                    return self.play()

            idx += 1

    def _finish_game(self, idx, reason):
        self.sm.clear_state()
        why = ("Your hull ruptured." if self.hull <= 0
               else "You cracked under the stress.")
        self.screen([
            ("*** STATION LOST ***", self.C(3) | curses.A_BOLD),
            (why, 0), ("", 0),
            (f"Reached level {idx + 1}   Score {self.score}", 0),
            ("", 0), ("Press any key...", 0),
        ])

        # update stats
        sd = self.stats.to_dict()
        sd["score"] = self.score
        self.sm.update_lifetime(sd)

        # leaderboard
        if self.sm.qualifies(self.score):
            initials = self.get_initials()
            self.sm.add_score(initials, self.score, idx + 1,
                              self.diff, self.stats.play_time)

        if self.daily:
            self.sm.set_daily(self.score, idx + 1)
            self.check_ach(daily=True)

        self.show_game_stats()
        return "done"

    # ── continue from save ──────────────────────────────────────────────────

    def continue_game(self):
        state = self.sm.load_state()
        if not state:
            self.screen([("No saved game found.", self.C(3)), ("", 0),
                         ("Press any key...", 0)])
            return
        self.score = state.get("score", 0)
        self.hull = state.get("hull", 100)
        self.stress = state.get("stress", 0)
        self.combo = state.get("combo", 0)
        self.diff = state.get("diff", "operator")
        self.mode = state.get("mode", "solo")
        self.stats.reset()
        self.ach_queue.clear()
        self.freeze_until = 0.0

        self.sm.clear_state()
        idx = state.get("level", 0)

        while True:
            name, flavour, *_ = level_cfg(idx)
            self.screen([(f"LEVEL {idx + 1}", self.C(4) | curses.A_BOLD),
                         (name, self.C(3) | curses.A_BOLD), ("", 0),
                         (flavour, 0)], wait_key=False)
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

    # ── daily challenge ─────────────────────────────────────────────────────

    def play_daily(self):
        self.daily = True
        seed = daily_seed()
        random.seed(seed)
        self.diff = "operator"
        self.mode = "solo"
        self.score, self.combo, self.stress, self.hull = 0, 0, 0.0, 100.0
        self.stats.reset()
        self.ach_queue.clear()
        self.freeze_until = 0.0

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
                         (name, self.C(3) | curses.A_BOLD), ("", 0),
                         (flavour, 0)], wait_key=False)
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
            bonus = 500 * (idx + 1)
            self.score += bonus
            self.hull = min(100, self.hull + 10)
            self.stress = max(0, self.stress - 30)

        # completed all 5
        self.sm.set_daily(self.score, 5)
        self.check_ach(daily=True)
        sd = self.stats.to_dict()
        sd["score"] = self.score
        self.sm.update_lifetime(sd)

        self.screen([
            ("DAILY CHALLENGE COMPLETE!", self.C(1) | curses.A_BOLD),
            (f"Score: {self.score}", 0),
            ("", 0),
            ("Press any key...", self.C(2)),
        ])
        self.show_game_stats()
        self.daily = False

    # ── versus mode ─────────────────────────────────────────────────────────

    def play_versus(self):
        seed = random.randint(0, 2**31)
        scores = []

        for player in (1, 2):
            self.screen([
                (f"PLAYER {player}", self.C(4) | curses.A_BOLD),
                ("Get ready!", 0), ("", 0),
                ("Press any key to start...", self.C(2)),
            ])

            random.seed(seed)
            self.mode = "solo"
            self.score, self.combo, self.stress, self.hull = 0, 0, 0.0, 100.0
            self.stats.reset()
            self.ach_queue.clear()
            self.freeze_until = 0.0

            final_level = 0
            for idx in range(len(LEVELS)):
                name, flavour, *_ = level_cfg(idx)
                self.screen([(f"P{player} - LEVEL {idx + 1}", self.C(4) | curses.A_BOLD),
                             (name, self.C(3) | curses.A_BOLD), ("", 0),
                             (flavour, 0)], wait_key=False)
                result = self.run_level(idx)
                if result == "dead":
                    final_level = idx + 1
                    break
                if result == "quit":
                    return "quit"
                if result == "restart":
                    return
                bonus = 500 * (idx + 1)
                self.score += bonus
                self.hull = min(100, self.hull + 10)
                self.stress = max(0, self.stress - 30)
                final_level = idx + 1
            else:
                final_level = len(LEVELS)

            scores.append((player, self.score, final_level))

            self.screen([
                (f"PLAYER {player} DONE", self.C(4) | curses.A_BOLD),
                (f"Score: {self.score}   Level: {final_level}", 0),
                ("", 0),
                ("Press any key...", self.C(2)),
            ])

        # compare
        s1, s2 = scores[0], scores[1]
        if s1[1] > s2[1]:
            winner = "PLAYER 1 WINS!"
        elif s2[1] > s1[1]:
            winner = "PLAYER 2 WINS!"
        else:
            winner = "IT'S A TIE!"

        self.screen([
            ("VERSUS RESULTS", self.C(2) | curses.A_BOLD),
            ("", 0),
            (f"P1: Score {s1[1]}  Level {s1[2]}", self.C(4)),
            (f"P2: Score {s2[1]}  Level {s2[2]}", self.C(4)),
            ("", 0),
            (winner, self.C(1) | curses.A_BOLD),
            ("", 0),
            ("Press any key...", self.C(2)),
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

    colors = [
        (1, curses.COLOR_GREEN,   -1),
        (2, curses.COLOR_YELLOW,  -1),
        (3, curses.COLOR_RED,     -1),
        (4, curses.COLOR_CYAN,    -1),
        (5, curses.COLOR_MAGENTA, -1),
        (6, curses.COLOR_WHITE,   -1),
    ]
    for idx, fg, bg in colors:
        try:
            curses.init_pair(idx, fg, bg)
        except curses.error:
            curses.init_pair(idx, fg, curses.COLOR_BLACK)

    sm = SaveManager()
    Sound.enabled = sm.settings.get("sound", True)
    g = Game(stdscr, sm)
    g.main_menu()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("Station abandoned. Coward.")
