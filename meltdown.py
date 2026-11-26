#!/usr/bin/env python3
"""
MELTDOWN - a stressful terminal game with levels.

You are the last operator on a failing space station. Alarms pop up
faster and faster. Type the right answer and press ENTER before the
timer runs out. Keep your STRESS and HULL under control. Survive all levels.

Run:      python3 meltdown.py
Windows:  pip install windows-curses   (then run the same command)
"""
import curses
import json
import os
import random
import time

WORDS = [
    "reactor", "coolant", "plasma", "airlock", "thruster", "oxygen", "gravity",
    "quantum", "fusion", "hatch", "vacuum", "orbit", "warp", "shield", "core",
    "valve", "circuit", "turbine", "pressure", "cryo", "nebula", "meteor",
    "ignite", "eject", "breach", "sensor", "uplink", "photon", "isotope",
]

# name, flavour, quota, spawn_secs, alarm_ttl, max_active, pressure, kinds, glitch, surge
LEVELS = [
    ("BOOT SEQUENCE",  "Easy does it. Systems warming up...",       6, 3.5, 14, 2, 0.8, ["type"], False, False),
    ("COOLANT LEAK",   "Things are getting slippery.",              8, 3.0, 12, 3, 1.0, ["type", "reverse"], False, False),
    ("PRESSURE SPIKE", "Your calculator hand better be ready.",    10, 2.6, 11, 3, 1.1, ["type", "reverse", "math"], False, False),
    ("SOLAR FLARE",    "Displays will get corrupted. Squint.",     12, 2.3, 10, 4, 1.2, ["type", "reverse", "math", "scramble"], True, False),
    ("BLACKOUT",       "Memorize codes before they vanish!",       14, 2.0, 9, 4, 1.3, ["type", "reverse", "math", "scramble", "memory"], True, False),
    ("CORE BREACH",    "Alarm surges incoming. Breathe. Or don't.", 16, 1.7, 8, 5, 1.4, ["type", "reverse", "math", "scramble", "memory"], True, True),
    ("TOTAL MELTDOWN", "Nobody has survived this. Good luck.",     20, 1.4, 7, 6, 1.6, ["type", "reverse", "math", "scramble", "memory"], True, True),
]

SAVE = os.path.join(os.path.expanduser("~"), ".meltdown_highscore.json")


def level_cfg(i):
    if i < len(LEVELS):
        return LEVELS[i]
    n = i - len(LEVELS) + 1  # endless mode keeps scaling
    return (f"ENDLESS DREAD {n}", "There is no escape. Only the score.", 20 + 2 * n,
            max(0.8, 1.4 - 0.08 * n), max(4.5, 7 - 0.3 * n), 6, 1.6 + 0.1 * n,
            LEVELS[-1][7], True, True)


class Alarm:
    def __init__(self, kind, ttl, now):
        self.kind, self.ttl, self.born = kind, ttl, now
        self.hide_after = None
        if kind == "type":
            w = random.choice(WORDS)
            self.label, self.text, self.answer = "TYPE", w.upper(), w
        elif kind == "reverse":
            w = random.choice(WORDS)
            self.label, self.text, self.answer = "REVERSE", w.upper(), w[::-1]
        elif kind == "scramble":
            w = random.choice(WORDS)
            letters = list(w)
            for _ in range(10):
                random.shuffle(letters)
                if "".join(letters) != w:
                    break
            self.label, self.text, self.answer = "UNSCRAMBLE", "".join(letters).upper(), w
        elif kind == "math":
            a, b = random.randint(3, 15), random.randint(2, 12)
            op = random.choice("+-*")
            self.label, self.text = "SOLVE", f"{a} {op} {b}"
            self.answer = str(eval(f"{a}{op}{b}"))
        else:  # memory
            code = "".join(random.choice("0123456789") for _ in range(random.randint(4, 6)))
            self.label, self.text, self.answer = "MEMORIZE", code, code
            self.hide_after = now + 2.0

    def shown(self, now):
        if self.hide_after and now > self.hide_after:
            return "*" * len(self.text)
        return self.text


class Game:
    def __init__(self, s):
        self.s = s
        self.score = 0
        self.combo = 0
        self.stress = 0.0
        self.hull = 100.0
        self.best = self.load_best()
        self.h, self.w = s.getmaxyx()

    # ---------- helpers ----------
    def load_best(self):
        try:
            with open(SAVE) as f:
                return json.load(f).get("best", 0)
        except Exception:
            return 0

    def save_best(self):
        if self.score > self.best:
            self.best = self.score
            try:
                with open(SAVE, "w") as f:
                    json.dump({"best": self.best}, f)
            except Exception:
                pass

    def put(self, y, x, text, attr=0):
        try:
            if 0 <= y < self.h and x < self.w:
                self.s.addstr(y, max(0, x), text[: max(0, self.w - x - 1)], attr)
        except curses.error:
            pass

    def center(self, y, text, attr=0):
        self.put(y, max(0, (self.w - len(text)) // 2), text, attr)

    def bar(self, y, x, label, frac, width, col):
        frac = max(0.0, min(1.0, frac))
        filled = int(frac * width)
        self.put(y, x, label)
        self.put(y, x + len(label), "[" + "#" * filled + "-" * (width - filled) + "]", col)

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

    # ---------- one level ----------
    def run_level(self, idx):
        name, _, quota, spawn, ttl, max_active, pressure, kinds, glitch, surge = level_cfg(idx)
        alarms, cleared, buf = [], 0, ""
        msg, msg_until, msg_col = "", 0, 0
        last = time.time()
        next_spawn = last + 1.0
        next_glitch = last + random.uniform(8, 14)
        glitch_until = 0
        G, Y, R, C = (curses.color_pair(i) for i in (1, 2, 3, 4))

        while True:
            now = time.time()
            dt = now - last
            last = now
            self.h, self.w = self.s.getmaxyx()

            # --- input ---
            while True:
                ch = self.s.getch()
                if ch == -1:
                    break
                if ch in (10, 13, curses.KEY_ENTER):
                    guess = buf.strip().lower()
                    buf = ""
                    if not guess:
                        continue
                    hits = [a for a in alarms if a.answer == guess]
                    if hits:
                        a = min(hits, key=lambda x: x.born + x.ttl)
                        alarms.remove(a)
                        cleared += 1
                        remaining = max(0, (a.born + a.ttl - now) / a.ttl)
                        pts = int(100 * (1 + self.combo * 0.25) * (0.5 + remaining))
                        self.combo += 1
                        self.score += pts
                        self.stress = max(0, self.stress - 9)
                        msg, msg_col, msg_until = f"+{pts}  COMBO x{self.combo}", G, now + 1.2
                    else:
                        self.combo = 0
                        self.stress += 10
                        msg, msg_col, msg_until = "WRONG! stress up", R, now + 1.2
                        curses.beep()
                elif ch in (8, 127, curses.KEY_BACKSPACE):
                    buf = buf[:-1]
                elif 32 <= ch < 127 and len(buf) < 30:
                    buf += chr(ch)

            # --- spawning ---
            need = quota - cleared - len(alarms)
            if now >= next_spawn and need > 0 and len(alarms) < max_active:
                count = 1
                if surge and random.random() < 0.18:
                    count = min(3, need, max_active - len(alarms))
                    msg, msg_col, msg_until = "!! SURGE !!", R, now + 1.5
                    curses.beep()
                for _ in range(count):
                    alarms.append(Alarm(random.choice(kinds), ttl, now))
                next_spawn = now + spawn * random.uniform(0.6, 1.4)

            # --- random display glitch ---
            if glitch and now >= next_glitch:
                glitch_until = now + 4
                next_glitch = now + random.uniform(12, 20)
                msg, msg_col, msg_until = "DISPLAY CORRUPTED!", Y, now + 2

            # --- expiry / stress ---
            for a in alarms[:]:
                if now >= a.born + a.ttl:
                    alarms.remove(a)
                    self.hull -= 15
                    self.stress += 12
                    self.combo = 0
                    cleared += 1  # a missed alarm still counts toward the quota
                    msg, msg_col, msg_until = "ALARM MISSED! hull damaged", R, now + 1.5
                    curses.beep()
            if alarms:
                self.stress += dt * len(alarms) * pressure
            else:
                self.stress -= dt * 4
            self.stress = max(0.0, min(100.0, self.stress))

            if self.hull <= 0 or self.stress >= 100:
                return "dead"
            if cleared >= quota and not alarms:
                return "clear"

            # --- draw ---
            self.s.erase()
            panic = self.stress > 80 and int(now * 5) % 2 == 0
            title = f" MELTDOWN :: LVL {idx + 1} {name} "
            self.put(0, 0, title.ljust(self.w - 1), curses.A_REVERSE | (R if panic else C))
            self.put(1, 0, f"SCORE {self.score}   BEST {max(self.best, self.score)}   "
                           f"COMBO x{self.combo}   PROGRESS {min(cleared, quota)}/{quota}")
            bw = max(10, min(40, self.w - 20))
            scol = G if self.stress < 50 else (Y if self.stress < 80 else R)
            hcol = G if self.hull > 60 else (Y if self.hull > 30 else R)
            self.bar(3, 0, "STRESS ", self.stress / 100, bw, scol)
            self.bar(4, 0, "HULL   ", self.hull / 100, bw, hcol)

            row = 6
            for a in sorted(alarms, key=lambda x: x.born + x.ttl):
                left = a.born + a.ttl - now
                frac = left / a.ttl
                txt = a.shown(now)
                if now < glitch_until:
                    rng = random.Random(int(now * 4) + id(a) % 97)
                    txt = "".join(c if c == " " or rng.random() > 0.3 else rng.choice("#@%&?!$")
                                  for c in txt)
                col = G if frac > 0.5 else (Y if frac > 0.25 else R)
                self.put(row, 0, f" {a.label:<11} {txt}", col | curses.A_BOLD)
                self.bar(row + 1, 0, "   time ", frac, max(8, min(30, self.w - 14)), col)
                row += 3
                if row >= self.h - 4:
                    break

            if now < msg_until:
                self.put(self.h - 3, 0, msg, msg_col | curses.A_BOLD)
            self.put(self.h - 2, 0, "> " + buf)
            self.s.move(self.h - 2, min(self.w - 2, 2 + len(buf)))
            self.s.refresh()
            time.sleep(0.03)

    # ---------- whole run ----------
    def play(self):
        self.score, self.combo, self.stress, self.hull = 0, 0, 0.0, 100.0
        idx = 0
        while True:
            name, flavour, *_ = level_cfg(idx)
            self.screen([(f"LEVEL {idx + 1}", curses.color_pair(4) | curses.A_BOLD),
                         (name, curses.color_pair(3) | curses.A_BOLD), ("", 0),
                         (flavour, 0)], wait_key=False)
            result = self.run_level(idx)
            if result == "dead":
                self.save_best()
                why = "Your hull ruptured." if self.hull <= 0 else "You cracked under the stress."
                self.screen([("*** STATION LOST ***", curses.color_pair(3) | curses.A_BOLD),
                             (why, 0), ("", 0),
                             (f"Reached level {idx + 1}   Score {self.score}   Best {self.best}", 0),
                             ("", 0), ("Press any key...", 0)])
                return
            bonus = 500 * (idx + 1)
            self.score += bonus
            self.hull = min(100, self.hull + 10)
            self.stress = max(0, self.stress - 30)
            self.save_best()
            self.screen([(f"LEVEL {idx + 1} CLEARED", curses.color_pair(1) | curses.A_BOLD),
                         (f"Bonus +{bonus}   Hull repaired a bit", 0), ("", 0),
                         ("Press any key for the next level...", 0)])
            idx += 1


def main(stdscr):
    curses.curs_set(1)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    curses.start_color()
    for i, c in enumerate((curses.COLOR_GREEN, curses.COLOR_YELLOW,
                           curses.COLOR_RED, curses.COLOR_CYAN), 1):
        curses.init_pair(i, c, curses.COLOR_BLACK)
    g = Game(stdscr)
    while True:
        g.screen([
            ("M E L T D O W N", curses.color_pair(3) | curses.A_BOLD),
            ("", 0),
            ("The station is failing. You are the only operator left.", 0),
            ("Alarms appear on screen. Type the answer, press ENTER.", 0),
            ("", 0),
            ("TYPE      -> type the word", 0),
            ("REVERSE   -> type it backwards", 0),
            ("SOLVE     -> type the result", 0),
            ("UNSCRAMBLE-> fix the letters", 0),
            ("MEMORIZE  -> remember the code before it hides", 0),
            ("", 0),
            ("Missed alarms damage the hull. Everything raises stress.", 0),
            ("Stress 100% or hull 0% = game over.", 0),
            ("", 0),
            ("Press any key to start (Ctrl+C quits)", curses.color_pair(2)),
        ])
        g.play()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("Station abandoned. Coward.")
