"""Tests for MELTDOWN v4.0.0 features (issues #7-#16)."""

import time

from meltdown import cli
from meltdown.alarms import (
    ALARM_MANUAL,
    ALL_KINDS,
    PLUGIN_ALARMS,
    Alarm,
    load_alarm_plugins,
    load_custom_words,
)
from meltdown.game import weekly_mutator, weekly_seed
from meltdown.lan import room_code_to_port
from meltdown.save import SaveManager


def test_custom_word_pack_loading(tmp_path):
    words_file = tmp_path / "words.txt"
    words_file.write_text("# comment\nnebula\nquasar\n123\n", encoding="utf-8")
    loaded = load_custom_words(str(tmp_path))
    assert loaded == ["nebula", "quasar"]
    a = Alarm("type", 10.0, time.time(), custom_words=loaded)
    assert a.answer in loaded


def test_weekly_seed_mutator_and_leaderboard(tmp_path):
    assert weekly_seed() == weekly_seed()
    assert weekly_mutator() in ("glass_cannon", "blindfold", "turbo")
    sm = SaveManager(data_dir=str(tmp_path))
    sm.set_weekly(3500, 5, "turbo")
    assert sm.get_weekly()["score"] == 3500
    assert sm.get_weekly()["mutator"] == "turbo"


def test_five_new_v4_alarm_types_and_matches():
    now = time.time()
    assert len(ALL_KINDS) == 20
    assert len(ALARM_MANUAL) == 20

    reg = Alarm("regex", 10.0, now)
    assert reg.matches(reg.answer) is True
    assert reg.matches("!!!") is False

    sym = Alarm("symbol", 10.0, now)
    assert len(sym.answer) == 4 and sym.answer.isdigit()

    chk = Alarm("checksum", 10.0, now)
    digits = chk.text.split()[0].split("-")[1]
    assert chk.answer == str(sum(int(c) for c in digits))

    cip = Alarm("cipher", 10.0, now)
    assert len(cip.answer) == len(cip.text)

    dual = Alarm("duallock", 10.0, now)
    assert dual.hit_mash() is False
    assert dual.hit_mash() is True


def test_custom_alarm_plugin_api(tmp_path):
    pdir = tmp_path / "plugins"
    pdir.mkdir()
    (pdir / "my_alarm.py").write_text(
        "def register_alarms():\n"
        "    return {'ping': ('CUSTOM PING', lambda lvl: ('PONG?', 'pong'))}\n",
        encoding="utf-8",
    )
    loaded = load_alarm_plugins(str(tmp_path))
    assert "ping" in loaded
    a = Alarm("ping", 10.0, time.time())
    assert a.label == "CUSTOM PING"
    assert a.answer == "pong"
    PLUGIN_ALARMS.pop("ping", None)


def test_room_code_port_and_replay_svg(tmp_path):
    p1 = room_code_to_port("ALPHA1")
    p2 = room_code_to_port("alpha1")
    assert p1 == p2 and 50000 <= p1 < 60000

    sm = SaveManager(data_dir=str(tmp_path))
    events = [{"t": 1.2, "msg": "CLEARED TYPE +120", "col": "#3fb950"}]
    rpath = sm.save_replay(events, 1200, 3, "A")
    assert rpath.endswith("last_run.json")
    assert sm.load_replay()["score"] == 1200

    svg_path = sm.export_animated_svg(events, 1200, "A", out_path=str(tmp_path / "rep.svg"))
    assert svg_path.endswith("rep.svg")
    assert "<svg" in (tmp_path / "rep.svg").read_text(encoding="utf-8")


def test_cli_record_parser_and_setup_shell(tmp_path):
    parser = cli.build_parser()
    args = parser.parse_args(["--record", "out.svg"])
    assert args.record == "out.svg"

    prof = tmp_path / "profile.ps1"
    assert cli.setup_shell(profile_path=str(prof)) == 0
    if prof.exists():
        assert "python -m meltdown" in prof.read_text(encoding="utf-8")
