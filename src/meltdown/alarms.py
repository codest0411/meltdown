"""Alarm generation, word pools, power-ups, hazards, and Field Manual data."""

import random

WORDS_EASY = [
    "core", "warp", "fuel", "hull", "beam", "dock", "scan", "flux",
    "cryo", "orbit", "valve", "eject", "hatch", "flare", "pulse", "laser",
    "solar", "spark", "relay", "gauge", "cable", "rotor", "nodes", "alarm",
]

WORDS_MED = [
    "reactor", "coolant", "plasma", "airlock", "oxygen", "gravity", "quantum",
    "fusion", "vacuum", "shield", "circuit", "turbine", "nebula", "meteor",
    "ignite", "breach", "sensor", "uplink", "photon", "isotope", "helium",
    "piston", "beacon", "carbon", "dynamo", "impulse",
]

WORDS_HARD = [
    "thruster", "pressure", "containment", "overdrive", "radiation",
    "antimatter", "telemetry", "navigation", "propulsion", "stabilizer",
    "supernova", "magnetic", "ventilation", "hyperdrive", "singularity",
    "capacitor", "oscillator", "emergency", "cryogenic", "trajectory",
    "diagnostics", "quarantine", "subroutine", "atmosphere", "wavelength",
]

WORDS = WORDS_EASY + WORDS_MED + WORDS_HARD

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

ALL_KINDS = [
    "type", "reverse", "math", "scramble", "memory",
    "morse", "sequence", "binary", "decode", "seqlock",
    "hex", "logic", "port", "typo", "mash",
]

POWERUP_TYPES = [
    ("FREEZE", "freeze", "Timers frozen for 5s"),
    ("REPAIR", "repair", "+20 hull integrity"),
    ("CALM",   "calm",   "-30 stress"),
    ("CLEAR",  "clear",  "All alarms cleared"),
]

ALARM_MANUAL = [
    ("TYPE",       "Type the exact word shown",                 "REACTOR -> reactor"),
    ("REVERSE",    "Type the word backwards",                   "CORE -> eroc"),
    ("SOLVE",      "Solve the arithmetic expression",           "14 * 8 -> 112"),
    ("UNSCRAMBLE", "Unscramble the jumbled letters",            "TCRAOER -> reactor"),
    ("MEMORIZE",   "Remember the digits before ***** hides it", "48213 -> 48213"),
    ("SEQUENCE",   "Find the next number in the pattern",       "4, 7, 10, 13, ? -> 16"),
    ("BINARY",     "Convert binary to decimal",                 "10110 -> 22"),
    ("MORSE",      "Decode the Morse code word",                ".- .-. -.-. -> arc"),
    ("DECODE",     "Find the word from two corrupted versions", "R#CT$R | RE$CT#R -> reactor"),
    ("SEQ LOCK",   "Remember U/D/L/R keys before it hides",     "UDLRU -> udlru"),
    ("HEX/OCTAL",  "Convert hex (0x..) or octal (0o..) to dec", "0x2F -> 47"),
    ("LOGIC GATE", "Evaluate boolean gate (0 or 1)",            "1 XOR 0 -> 1"),
    ("PING/PORT",  "Type the target port shown in the log",     "ERR@NODE -> PORT:8080 -> 8080"),
    ("TYPO HUNT",  "Type the ONE misspelled word in the pair",  "ORBIT | ORBXT -> orbxt"),
    ("VENT MASH",  "Submit the short key 3 times to vent",      "VENT x3 -> vent (3 times)"),
]


def _pick_unique(pool, recent=None):
    """Pick a random item from pool, avoiding items in recent when possible."""
    if recent:
        fresh = [x for x in pool if x not in recent]
        if fresh:
            choice = random.choice(fresh)
            recent.append(choice)
            return choice
    choice = random.choice(pool)
    if recent is not None:
        recent.append(choice)
    return choice


def _word_pool_for_level(level):
    """Return progressively harder word pools as level increases."""
    if level <= 1:
        return WORDS_EASY + WORDS_MED
    if level <= 4:
        return WORDS_MED + WORDS_HARD
    return WORDS_HARD + (WORDS_MED if level < 7 else [])


def _make_typo(word):
    """Create a 1-character typo of word."""
    idx = random.randrange(len(word))
    repl = random.choice([c for c in "xzqkv" if c != word[idx]])
    return word[:idx] + repl + word[idx + 1:]


class Alarm:
    def __init__(self, kind, ttl, now, level=0, recent=None, blindfold=False):
        self.kind = kind
        self.ttl = ttl
        self.born = now
        self.hide_after = (now + 1.5) if blindfold else None
        self.is_boss = False
        self.is_powerup = False
        self.is_hazard = False
        self.hazard_kind = None
        self.hits_left = 1

        word_pool = _word_pool_for_level(level)

        if kind == "type":
            w = _pick_unique(word_pool, recent)
            self.label, self.text, self.answer = "TYPE", w.upper(), w
        elif kind == "reverse":
            w = _pick_unique(word_pool, recent)
            self.label, self.text, self.answer = "REVERSE", w.upper(), w[::-1]
        elif kind == "scramble":
            w = _pick_unique(word_pool, recent)
            letters = list(w)
            for _ in range(20):
                random.shuffle(letters)
                if "".join(letters) != w:
                    break
            self.label, self.text, self.answer = "UNSCRAMBLE", "".join(letters).upper(), w
        elif kind == "math":
            lo = 3 + level * 3
            hi = 15 + level * 7
            b_lo = 2 + level * 2
            b_hi = 12 + level * 4
            expr = None
            for _ in range(15):
                op = random.choice("+-*")
                if op == "*":
                    a = random.randint(max(3, 3 + level), max(12, 10 + level * 2))
                    b = random.randint(max(2, 2 + level // 2), max(9, 8 + level * 2))
                else:
                    a = random.randint(lo, hi)
                    b = random.randint(b_lo, b_hi)
                cand = f"{a} {op} {b}"
                if not recent or cand not in recent:
                    expr = (a, op, b, cand)
                    break
            if expr is None:
                a, op, b = random.randint(lo, hi), random.choice("+-*"), random.randint(b_lo, b_hi)
                expr = (a, op, b, f"{a} {op} {b}")
            a, op, b, cand = expr
            if recent is not None:
                recent.append(cand)
            res = {"+": a + b, "-": a - b, "*": a * b}[op]
            self.label, self.text, self.answer = "SOLVE", cand, str(res)
        elif kind == "memory":
            length = min(8, random.randint(4 + level // 3, 6 + level // 3))
            code = "".join(random.choice("0123456789") for _ in range(length))
            self.label, self.text, self.answer = "MEMORIZE", code, code
            self.hide_after = now + (1.5 if blindfold else 2.0)
        elif kind == "sequence":
            step_lo = 2 + level
            step_hi = 5 + level * 2
            step = random.randint(step_lo, step_hi)
            if level >= 4 and random.random() < 0.35:
                step = -step
                start = random.randint(abs(step) * 4 + 2, abs(step) * 4 + 20 + level * 4)
            else:
                start = random.randint(1 + level * 2, 10 + level * 5)
            seq = [start + step * i for i in range(4)]
            nxt = start + step * 4
            self.label = "SEQUENCE"
            self.text = ", ".join(str(x) for x in seq) + ", ?"
            self.answer = str(nxt)
        elif kind == "binary":
            lo = 3 if level <= 3 else (16 if level <= 5 else 32)
            hi = 31 if level <= 3 else (63 if level <= 5 else min(255, 63 + level * 12))
            num = random.randint(lo, hi)
            self.label, self.text, self.answer = "BINARY", bin(num)[2:], str(num)
        elif kind == "morse":
            pool = SHORT_WORDS if level <= 4 else (SHORT_WORDS + WORDS_EASY)
            w = _pick_unique(pool, recent)
            m = "  ".join(MORSE.get(c.upper(), "?") for c in w)
            self.label, self.text, self.answer = "MORSE", m, w
        elif kind == "decode":
            w = _pick_unique(word_pool, recent)
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
            length = min(8, random.randint(4 + level // 3, 6 + level // 3))
            dirs = "".join(random.choice("udlr") for _ in range(length))
            self.label, self.text, self.answer = "SEQ LOCK", dirs.upper(), dirs
            self.hide_after = now + (1.5 if blindfold else 2.5)
        elif kind == "hex":
            num = random.randint(10, 63 + level * 16)
            if random.random() < 0.65:
                self.label, self.text, self.answer = "HEX", f"0x{num:X}", str(num)
            else:
                self.label, self.text, self.answer = "OCTAL", f"0o{num:o}", str(num)
        elif kind == "logic":
            a, b = random.randint(0, 1), random.randint(0, 1)
            gate = random.choice(["AND", "OR", "XOR", "NAND"])
            val = {
                "AND": a & b,
                "OR": a | b,
                "XOR": a ^ b,
                "NAND": int(not (a & b)),
            }[gate]
            self.label, self.text, self.answer = "LOGIC", f"{a} {gate} {b}", str(val)
        elif kind == "port":
            port = random.choice([22, 80, 443, 3000, 5432, 6379, 8080, 8443, 9000])
            node = random.choice(["CORE", "SYS", "AUX", "NET"])
            self.label = "PING/PORT"
            self.text = f"ERR@{node}::PORT:{port}"
            self.answer = str(port)
        elif kind == "typo":
            w = _pick_unique(WORDS_EASY + WORDS_MED, recent)
            bad = _make_typo(w)
            pair = [w.upper(), bad.upper()]
            random.shuffle(pair)
            self.label = "TYPO HUNT"
            self.text = f"{pair[0]} | {pair[1]}"
            self.answer = bad
        elif kind == "mash":
            w = random.choice(["vent", "dump", "cool", "hold"])
            self.hits_left = 3
            self.label = "VENT x3"
            self.text = f"{w.upper()} (3 left)"
            self.answer = w
        else:
            w = _pick_unique(word_pool, recent)
            self.label, self.text, self.answer = "TYPE", w.upper(), w

    def hit_mash(self):
        """Decrement multi-hit counter; return True if alarm is now cleared."""
        self.hits_left -= 1
        if self.hits_left > 0:
            self.label = f"VENT x{self.hits_left}"
            self.text = f"{self.answer.upper()} ({self.hits_left} left)"
            return False
        return True

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
        a.is_hazard = False
        a.hazard_kind = None
        a.hits_left = 1
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
        a.is_hazard = False
        a.hazard_kind = None
        a.hits_left = 1
        a.label = f">> {name} <<"
        a.text = keyword.upper()
        a.answer = keyword
        a.pup_name = name
        a.pup_desc = desc
        return a

    @staticmethod
    def make_hazard(hazard_kind, ttl, now):
        """Create a hazard-clearing alarm ('purge' for radiation, 'oxygen' for low O2)."""
        a = Alarm.__new__(Alarm)
        a.kind = hazard_kind
        a.ttl = ttl
        a.born = now
        a.hide_after = None
        a.is_boss = False
        a.is_powerup = False
        a.is_hazard = True
        a.hazard_kind = hazard_kind
        a.hits_left = 1
        if hazard_kind == "radiation":
            a.label = "!RADIATION!"
            a.text = "PURGE"
            a.answer = "purge"
        else:
            a.label = "!LOW O2!"
            a.text = "OXYGEN"
            a.answer = "oxygen"
        return a
