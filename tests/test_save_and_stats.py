"""Tests for SaveManager persistence, isolation, and Stats tracking."""

import os

from meltdown.game import SaveManager, Stats


def test_save_manager_uses_temp_dir_and_is_isolated(tmp_path):
    dir1 = tmp_path / "u1"
    dir2 = tmp_path / "u2"
    sm1 = SaveManager(data_dir=str(dir1))
    sm2 = SaveManager(data_dir=str(dir2))

    sm1.add_score("AAA", 1500, 3, "operator", 45.2)
    assert len(sm1.scores) == 1
    assert len(sm2.scores) == 0


def test_save_manager_respects_env_var(tmp_path, monkeypatch):
    monkeypatch.setenv("MELTDOWN_DATA_DIR", str(tmp_path))
    sm = SaveManager()
    sm.add_score("ENV", 2000, 4, "casual", 60.0)
    assert os.path.exists(tmp_path / "data.json")

    sm_reloaded = SaveManager()
    assert sm_reloaded.best_score() == 2000


def test_save_manager_handles_corrupt_json(tmp_path):
    data_file = tmp_path / "data.json"
    data_file.write_text("{not valid json!!!", encoding="utf-8")

    sm = SaveManager(data_dir=str(tmp_path))
    assert sm.best_score() == 0
    assert sm.scores == []
    assert sm.settings["sound"] is True


def test_leaderboard_top_10_sorting_and_qualifies(tmp_path):
    sm = SaveManager(data_dir=str(tmp_path))
    for i in range(12):
        sm.add_score(f"P{i:02d}", (i + 1) * 100, 1, "operator", 10.0)

    assert len(sm.scores) == 10
    assert sm.scores[0]["score"] == 1200
    assert sm.scores[-1]["score"] == 300
    assert sm.qualifies(301) is True
    assert sm.qualifies(200) is False


def test_achievements_daily_and_save_state(tmp_path):
    sm = SaveManager(data_dir=str(tmp_path))
    assert sm.unlock("first_clear") is True
    assert sm.unlock("first_clear") is False
    assert sm.has_ach("first_clear") is True

    sm.set_daily(4200, 5)
    assert sm.get_daily() == {"score": 4200, "level": 5}
    sm.set_daily(3000, 3)  # lower score should not overwrite
    assert sm.get_daily()["score"] == 4200

    state = {"level": 3, "score": 1234, "hull": 85.0, "stress": 20.0}
    sm.save_state(state)
    assert sm.load_state() == state
    sm.clear_state()
    assert sm.load_state() is None


def test_stats_and_lifetime_aggregation(tmp_path):
    st = Stats()
    st.begin_level()
    st.hit("type", 0.5)
    st.hit("binary", 1.5)
    st.wrong_answer()
    st.miss("morse")

    assert st.correct == 2
    assert st.wrong == 1
    assert st.missed == 1
    assert st.fastest == 0.5
    assert st.avg_resp == 1.0
    assert abs(st.accuracy - 66.666) < 0.1
    assert st.worst_type == "morse"
    assert st.level_no_mistakes is False
    assert st.level_no_hull_dmg is False

    sm = SaveManager(data_dir=str(tmp_path))
    d = st.to_dict()
    d["score"] = 900
    sm.update_lifetime(d)
    assert sm.lifetime["total_games"] == 1
    assert sm.lifetime["total_score"] == 900
    assert sm.lifetime["fastest_ever"] == 0.5
