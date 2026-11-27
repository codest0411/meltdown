"""Tests for MELTDOWN v3.0.0 roadmap features."""

import time
from unittest.mock import MagicMock, patch

from meltdown.alarms import ALARM_MANUAL, ALL_KINDS, Alarm
from meltdown.audio import _synth_wav_bytes
from meltdown.game import Game, decode_sandbox_code, encode_sandbox_code
from meltdown.save import SaveManager, compute_rank, format_run_card
from meltdown.themes import SKINS, THEMES


def test_new_v3_alarm_types_and_mash():
    now = time.time()
    hex_a = Alarm("hex", 10.0, now, level=4)
    if hex_a.text.startswith("0x"):
        assert int(hex_a.text, 16) == int(hex_a.answer)
    else:
        assert int(hex_a.text, 8) == int(hex_a.answer)

    logic_a = Alarm("logic", 10.0, now)
    assert logic_a.answer in ("0", "1")

    port_a = Alarm("port", 10.0, now)
    assert port_a.answer in port_a.text

    typo_a = Alarm("typo", 10.0, now)
    assert "|" in typo_a.text
    assert typo_a.answer.upper() in typo_a.text

    mash_a = Alarm("mash", 10.0, now)
    assert mash_a.hits_left == 3
    assert mash_a.hit_mash() is False
    assert mash_a.hit_mash() is False
    assert mash_a.hit_mash() is True


def test_hazard_alarms_and_blindfold():
    now = 1000.0
    rad = Alarm.make_hazard("radiation", 12.0, now)
    assert rad.is_hazard and rad.answer == "purge"

    oxy = Alarm.make_hazard("oxygen", 12.0, now)
    assert oxy.is_hazard and oxy.answer == "oxygen"

    blind = Alarm("type", 10.0, now, blindfold=True)
    assert blind.shown(now + 2.0) == "*" * len(blind.text)


def test_rank_run_card_and_ghost_replay(tmp_path):
    assert compute_rank(15000, 96.0, 8) == "S+"
    assert compute_rank(100, 30.0, 1) == "D"

    card = format_run_card(8420, 7, 91.4, 14, 184.2, "operator", "solo")
    assert "MELTDOWN :: OPERATOR MISSION CARD" in card
    assert "RANK" in card

    sm = SaveManager(data_dir=str(tmp_path))
    sm.save_ghost(5000, [(1.0, 100), (5.0, 800), (10.0, 2200)])
    assert sm.get_ghost_score_at(0.5) == 0
    assert sm.get_ghost_score_at(6.0) == 800
    assert sm.get_ghost_score_at(15.0) == 2200
    path = sm.export_run_card(card)
    assert path.endswith("last_run_card.md")


def test_sandbox_code_roundtrip():
    code = encode_sandbox_code(48291, 2, "turbo")
    assert code == "SBX-48291-L3-T"
    assert decode_sandbox_code(code) == (48291, 2, "turbo")
    assert decode_sandbox_code("INVALID") is None


def test_audio_themes_skins_and_manual():
    wav = _synth_wav_bytes(440, 50)
    assert wav[:4] == b"RIFF"
    assert len(ALL_KINDS) >= 20
    assert len(ALARM_MANUAL) == len(ALL_KINDS)
    assert {"cyber_cyan", "classic_amber", "red_alert", "mono_hc"} <= set(THEMES.keys())
    assert {"default", "sentinel", "singularity", "nightmare"} <= set(SKINS.keys())


def test_check_min_size_and_manual_with_mocked_stdscr(tmp_path):
    stdscr = MagicMock()
    with patch("meltdown.game.curses.curs_set"), patch(
        "meltdown.game.curses.color_pair", return_value=0
    ):
        sm = SaveManager(data_dir=str(tmp_path))
        stdscr.getmaxyx.return_value = (15, 50)
        g = Game(stdscr, sm)
        assert g._check_min_size() is False

        stdscr.getmaxyx.return_value = (30, 100)
        assert g._check_min_size() is True
        stdscr.getch.return_value = 10
        g.show_manual()
