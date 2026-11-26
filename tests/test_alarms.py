"""Tests for Alarm generation, level configs, bosses, power-ups, and daily seeds."""

import time

from meltdown.game import (
    ALL_KINDS,
    DIFFICULTY,
    LEVELS,
    MORSE,
    POWERUP_TYPES,
    WORDS,
    Alarm,
    daily_seed,
    level_cfg,
)


def test_all_alarm_types_generate_valid_prompts_and_answers():
    now = time.time()
    for kind in ALL_KINDS:
        alarm = Alarm(kind, 10.0, now)
        assert alarm.kind == kind
        assert alarm.label
        assert alarm.text
        assert alarm.answer
        assert alarm.shown(now) == alarm.text


def test_memory_and_seqlock_hide_after_delay():
    now = 1000.0
    mem = Alarm("memory", 10.0, now)
    assert mem.shown(now + 0.5) == mem.text
    assert mem.shown(now + 2.5) == "*" * len(mem.text)

    seq = Alarm("seqlock", 10.0, now)
    assert seq.shown(now + 0.5) == seq.text
    assert seq.shown(now + 3.0) == "*" * len(seq.text)


def test_reverse_math_binary_sequence_morse_decode_answers():
    now = time.time()

    rev = Alarm("reverse", 10.0, now)
    assert rev.answer == rev.text.lower()[::-1]

    math_alarm = Alarm("math", 10.0, now)
    a, op, b = math_alarm.text.split()
    expected = {"+": int(a) + int(b), "-": int(a) - int(b), "*": int(a) * int(b)}[op]
    assert math_alarm.answer == str(expected)

    binary = Alarm("binary", 10.0, now)
    assert int(binary.text, 2) == int(binary.answer)

    seq = Alarm("sequence", 10.0, now)
    parts = [int(x.strip()) for x in seq.text.split(",")[:-1]]
    step = parts[1] - parts[0]
    assert int(seq.answer) == parts[-1] + step

    morse = Alarm("morse", 10.0, now)
    decoded = "".join(
        next(ch for ch, code in MORSE.items() if code == token).lower()
        for token in morse.text.split("  ")
    )
    assert decoded == morse.answer

    dec = Alarm("decode", 10.0, now)
    assert "|" in dec.text
    assert dec.answer in WORDS


def test_boss_code_and_powerup_factories():
    now = time.time()
    boss = Alarm.make_boss_code(8, 20.0, now)
    assert boss.is_boss is True
    assert boss.is_powerup is False
    assert boss.label == "BOSS CODE"
    assert len(boss.answer) == 8
    assert boss.text == boss.answer.upper()

    for pt in POWERUP_TYPES:
        pup = Alarm.make_powerup(pt, 8.0, now)
        assert pup.is_powerup is True
        assert pup.is_boss is False
        assert pup.answer == pt[1]


def test_level_cfg_handcrafted_and_endless_scaling():
    for i in range(len(LEVELS)):
        assert level_cfg(i) == LEVELS[i]

    e1 = level_cfg(len(LEVELS))
    e5 = level_cfg(len(LEVELS) + 4)
    assert "ENDLESS DREAD 1" in e1[0]
    assert "ENDLESS DREAD 5" in e5[0]
    assert e5[2] > e1[2]  # quota increases
    assert e5[3] <= e1[3]  # spawn interval decreases or hits floor
    assert e5[4] <= e1[4]  # ttl decreases or hits floor


def test_difficulty_presets_exist():
    assert set(DIFFICULTY.keys()) == {"casual", "operator", "nightmare"}


def test_daily_seed_is_deterministic():
    assert daily_seed() == daily_seed()
    assert isinstance(daily_seed(), int)
