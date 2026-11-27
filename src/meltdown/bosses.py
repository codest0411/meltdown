"""Boss fight definitions for MELTDOWN."""

BOSSES = [
    {"name": "THE SENTINEL", "sub": "Defense system online. Break through.",
     "phases": 3, "codes": 2, "code_len": (5, 7), "reg_spawn": 4.0,
     "reg_kinds": ["type", "reverse", "logic"], "stress_atk": 0, "total_hp": 100},
    {"name": "THE GUARDIAN", "sub": "It knows you are here. Fight back.",
     "phases": 4, "codes": 2, "code_len": (6, 8), "reg_spawn": 3.0,
     "reg_kinds": ["type", "reverse", "math", "hex"], "stress_atk": 5, "total_hp": 150},
    {"name": "THE CORE",     "sub": "The core awakens. This ends now.",
     "phases": 5, "codes": 3, "code_len": (7, 10), "reg_spawn": 2.5,
     "reg_kinds": ["type", "reverse", "math", "scramble", "port"], "stress_atk": 8,
     "total_hp": 200},
]

BOSS_AFTER_LEVEL = {2: 0, 4: 1, 6: 2}
