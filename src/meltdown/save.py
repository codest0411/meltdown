"""Persistent save data, achievements, stats, ghost replays, and rank cards."""

import copy
import json
import os
import time
from datetime import date

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
    "score_10000":     ("Score Legend",      "Reach score 10000"),
    "nightmare_clear": ("Nightmare Fuel",    "Clear level 1 on Nightmare"),
    "all_types":       ("Polyglot",          "Answer every alarm type in one run"),
}


def get_save_dir(data_dir=None):
    """Return the directory for persistent user save data."""
    if data_dir:
        return data_dir
    env_dir = os.environ.get("MELTDOWN_DATA_DIR")
    if env_dir:
        return env_dir
    return os.path.join(os.path.expanduser("~"), ".meltdown")


SAVE_DIR = os.path.join(os.path.expanduser("~"), ".meltdown")
SAVE_FILE = os.path.join(SAVE_DIR, "data.json")

DEFAULT_SETTINGS = {
    "sound": True,
    "reduced_flash": False,
    "show_timer_numbers": True,
    "colorblind": False,
    "large_ui": False,
    "ascii_bars": False,
    "custom_words": True,
    "theme": "cyber_cyan",
    "skin": "default",
}

DEFAULT_DATA = {
    "scores": [],
    "daily": {},
    "weekly": {},
    "achievements": [],
    "settings": dict(DEFAULT_SETTINGS),
    "lifetime": {
        "total_games": 0, "total_score": 0, "total_correct": 0,
        "total_wrong": 0, "total_missed": 0, "best_combo": 0,
        "fastest_ever": 999.0, "total_play_time": 0.0,
        "bosses_killed": [],
    },
    "save_state": None,
    "ghost_best": None,
}


def compute_rank(score: int, accuracy: float, level: int) -> str:
    """Compute an Operator Rank grade (S+, S, A, B, C, D) for a run."""
    pts = score / 100.0 + accuracy * 0.8 + level * 15.0
    if pts >= 230 and accuracy >= 90:
        return "S+"
    if pts >= 180 and accuracy >= 82:
        return "S"
    if pts >= 135:
        return "A"
    if pts >= 95:
        return "B"
    if pts >= 55:
        return "C"
    return "D"


def format_run_card(score: int, level: int, accuracy: float, combo_max: int,
                    play_time: float, diff: str, mode: str = "solo") -> str:
    """Generate a shareable Markdown/ASCII run summary card."""
    rank = compute_rank(score, accuracy, level)
    return (
        "```text\n"
        "+--------------------------------------+\n"
        "|  MELTDOWN :: OPERATOR MISSION CARD   |\n"
        "+--------------------------------------+\n"
        f"|  RANK     : {rank:<24} |\n"
        f"|  SCORE    : {score:<24} |\n"
        f"|  LEVEL    : {level:<24} |\n"
        f"|  ACCURACY : {accuracy:>5.1f}%{'':<18} |\n"
        f"|  COMBO    : x{combo_max:<23} |\n"
        f"|  TIME     : {play_time:>5.1f}s ({diff}/{mode}){'':<4} |\n"
        "+--------------------------------------+\n"
        "```"
    )


class SaveManager:
    def __init__(self, data_dir=None):
        self.save_dir = get_save_dir(data_dir)
        self.save_file = os.path.join(self.save_dir, "data.json")
        self.data = copy.deepcopy(DEFAULT_DATA)
        self._load()

    def _load(self):
        try:
            with open(self.save_file, encoding="utf-8") as f:
                loaded = json.load(f)
            if not isinstance(loaded, dict):
                return
            for k in DEFAULT_DATA:
                if k in loaded:
                    if isinstance(DEFAULT_DATA[k], dict) and isinstance(loaded[k], dict):
                        merged = copy.deepcopy(DEFAULT_DATA[k])
                        merged.update(loaded[k])
                        self.data[k] = merged
                    elif isinstance(DEFAULT_DATA[k], list) and isinstance(loaded[k], list):
                        self.data[k] = loaded[k]
                    elif not isinstance(DEFAULT_DATA[k], (dict, list)):
                        self.data[k] = loaded[k]
        except Exception:
            pass
        old = os.path.join(os.path.expanduser("~"), ".meltdown_highscore.json")
        if os.path.exists(old):
            try:
                with open(old, encoding="utf-8") as f:
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
            os.makedirs(self.save_dir, exist_ok=True)
            with open(self.save_file, "w", encoding="utf-8") as f:
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

    def set_weekly(self, score, level, mutator="none"):
        key = date.today().strftime("%G-W%V")
        cur = self.data.setdefault("weekly", {}).get(key, {})
        if score > cur.get("score", 0):
            self.data["weekly"][key] = {"score": score, "level": level, "mutator": mutator}
            self.save()

    def get_weekly(self):
        key = date.today().strftime("%G-W%V")
        return self.data.get("weekly", {}).get(key)

    def save_replay(self, events, score, level, rank):
        """Save full run replay events to ~/.meltdown/replays/last_run.json."""
        try:
            rdir = os.path.join(self.save_dir, "replays")
            os.makedirs(rdir, exist_ok=True)
            path = os.path.join(rdir, "last_run.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"score": score, "level": level, "rank": rank, "events": events[:500]}, f)
            return path
        except Exception:
            return ""

    def load_replay(self):
        try:
            path = os.path.join(self.save_dir, "replays", "last_run.json")
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def export_animated_svg(self, events, score, rank, out_path=None):
        """Export an animated SVG terminal replay of the run."""
        if not out_path:
            out_path = os.path.join(self.save_dir, "last_run.svg")
        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="420" viewBox="0 0 760 420" '
            f'font-family="Consolas, Menlo, monospace" font-size="14">',
            '<rect width="760" height="420" rx="12" fill="#0d1117" stroke="#30363d"/>',
            '<rect width="760" height="34" rx="12" fill="#161b22"/>',
            '<circle cx="20" cy="17" r="5" fill="#f85149"/>'
            '<circle cx="38" cy="17" r="5" fill="#d29922"/>'
            '<circle cx="56" cy="17" r="5" fill="#3fb950"/>',
            f'<text x="380" y="21" text-anchor="middle" fill="#8b949e">MELTDOWN REPLAY :: SCORE {score} :: RANK {rank}</text>',
        ]
        y = 64
        for idx, ev in enumerate(events[:14]):
            t_sec = ev.get("t", 0.0)
            msg = str(ev.get("msg", "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            col = ev.get("col", "#3fb950")
            lines.append(
                f'<text x="24" y="{y}" fill="{col}" opacity="0">'
                f'[{t_sec:5.1f}s] {msg}'
                f'<animate attributeName="opacity" from="0" to="1" begin="{idx * 0.35:.2f}s" dur="0.2s" fill="freeze"/>'
                f'</text>'
            )
            y += 24
        lines.append("</svg>")
        try:
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return out_path
        except Exception:
            return ""

    def save_state(self, state):
        self.data["save_state"] = state
        self.save()

    def load_state(self):
        return self.data["save_state"]

    def clear_state(self):
        self.data["save_state"] = None
        self.save()

    def save_ghost(self, score, timeline):
        """Save personal-best ghost replay timeline [(elapsed_sec, score), ...]."""
        cur = self.data.get("ghost_best")
        if cur is None or score > cur.get("score", 0):
            self.data["ghost_best"] = {"score": score, "timeline": timeline[:300]}
            self.save()

    def get_ghost_score_at(self, elapsed_sec: float) -> int:
        """Return the ghost's score at elapsed_sec, or 0 if no ghost exists."""
        cur = self.data.get("ghost_best")
        if not cur:
            return 0
        best_s = 0
        for t, s in cur.get("timeline", []):
            if t <= elapsed_sec:
                best_s = s
            else:
                break
        return best_s

    def export_run_card(self, card_text: str) -> str:
        """Write the latest shareable run card to ~/.meltdown/last_run_card.md."""
        try:
            os.makedirs(self.save_dir, exist_ok=True)
            path = os.path.join(self.save_dir, "last_run_card.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(card_text + "\n")
            return path
        except Exception:
            return ""

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
