"""
Tests for the board rules in app/websocket/board_rules.py.

board_rules has no database or socket dependencies, so these run without the
app. Run with:  python backend/tests/test_board_rules.py
"""
import importlib.util
import os
import random

_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "websocket", "board_rules.py")
_spec = importlib.util.spec_from_file_location("board_rules", _PATH)
rules = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rules)


def test_track_matches_the_physical_board():
    assert len(rules.TILES) == rules.BOARD_SIZE == 20
    assert [t["index"] for t in rules.TILES] == list(range(20))
    assert rules.TILES[rules.START]["kind"] == "start"
    assert rules.TILES[rules.JOB_CENTRE]["kind"] == "job_centre"
    assert rules.TILES[rules.GO_TO_JOB_CENTRE]["kind"] == "go_to_job_centre"
    assert rules.TILES[rules.BLACK_MARKET]["kind"] == "black_market"
    # Job Centre is two tiles, the Senate three, the Hospital two
    assert [t["index"] for t in rules.TILES if t.get("building") == "job_centre"] == [4, 5]
    assert [t["index"] for t in rules.TILES if t.get("building") == "senate"] == [9, 10, 11]
    assert [t["index"] for t in rules.TILES if t.get("building") == "hospital"] == [14, 15]
    # The third Senate tile is also a Time Virus
    assert rules.TIME_VIRUS_TILES == {6, 11}
    assert rules.COLLECTABLE_TILES == {1, 7, 13, 16}
    print("PASS: track layout")


def test_simple_move():
    move = rules.compute_move(0, 4)
    assert move["path"] == [1, 2, 3, 4]
    assert move["to"] == 4
    assert move["passed_start"] is False
    assert move["jumped_from"] is None
    print("PASS: simple move")


def test_passing_and_landing_on_start():
    move = rules.compute_move(18, 4)
    assert move["path"] == [19, 0, 1, 2]
    assert move["passed_start"] is True

    move = rules.compute_move(16, 4)
    assert move["to"] == 0
    assert move["passed_start"] is True, "landing on Start also removes heat"
    print("PASS: passing / landing on Start")


def test_go_to_job_centre_jumps_and_counts_as_passing_start():
    move = rules.compute_move(14, 3)
    assert move["path"][-1] == 17
    assert move["jumped_from"] == 17
    assert move["to"] == rules.JOB_CENTRE
    assert move["passed_start"] is True
    print("PASS: Go to the Job Centre")


def test_moving_out_of_jail_starts_from_start():
    move = rules.compute_move(rules.JAIL, 2)
    assert move["path"] == [1, 2]
    print("PASS: jail -> start")


def test_second_tile_of_a_building_gives_no_access():
    assert rules.same_building(14, 15) is True       # Hospital -> Hospital
    assert rules.same_building(9, 11) is True        # Senate -> Senate
    assert rules.same_building(4, 5) is True         # Job Centre -> Job Centre
    assert rules.same_building(13, 14) is False      # arrived from outside
    assert rules.same_building(3, 3) is False        # not a building
    assert rules.same_building(rules.JAIL, 5) is False
    print("PASS: building access")


def test_turn_order_wraps_into_a_new_round_and_skips_leavers():
    order = [10, 20, 30]
    present = {10, 20, 30}
    assert rules.next_turn_index(order, 0, present.__contains__) == (1, False)
    assert rules.next_turn_index(order, 2, present.__contains__) == (0, True)

    present = {10, 30}  # 20 left the room
    assert rules.next_turn_index(order, 0, present.__contains__) == (2, False)

    present = {20}
    assert rules.next_turn_index(order, 1, present.__contains__) == (1, True)
    assert rules.next_turn_index(order, 0, set().__contains__) == (None, False)
    assert rules.next_turn_index([], None, present.__contains__) == (None, False)
    print("PASS: turn order")


def test_horsemen_ranges():
    assert rules.horseman_for(0) is None
    assert rules.horseman_for(1) == "Pestilence"
    assert rules.horseman_for(25) == "Pestilence"
    assert rules.horseman_for(26) == "War"
    assert rules.horseman_for(50) == "War"
    assert rules.horseman_for(51) == "Famine"
    assert rules.horseman_for(76) == "Death"
    assert rules.horseman_for(100) == "Death"
    print("PASS: horsemen")


def test_counter_activates_on_each_multiple_of_five():
    new, acts = rules.advance_counter(3, 4)
    assert new == 7 and acts == [{"at": 5, "horseman": "Pestilence"}]

    new, acts = rules.advance_counter(4, 12)  # 4 -> 16 crosses 5, 10, 15
    assert new == 16 and [a["at"] for a in acts] == [5, 10, 15]

    new, acts = rules.advance_counter(24, 2)  # 25 is Pestilence's fifth
    assert [a["horseman"] for a in acts] == ["Pestilence"]

    new, acts = rules.advance_counter(28, 2)
    assert acts == [{"at": 30, "horseman": "War"}]

    new, acts = rules.advance_counter(5, 3)  # already counted 5
    assert acts == []

    new, acts = rules.advance_counter(98, 12)
    assert new == 100 and [a["at"] for a in acts] == [100]
    print("PASS: counter activations")


def test_purchases():
    ok, cost = rules.validate_purchase("collectable", 1, {})
    assert ok and cost == 60
    ok, cost = rules.validate_purchase("promotion", 7, {"collectable": 2})
    assert ok and cost == 120
    ok, _ = rules.validate_purchase("promotion", 7, {"promotion": 1})
    assert not ok, "max one promotion per visit"
    ok, _ = rules.validate_purchase("collectable", 7, {"collectable": 12, "promotion": 1})
    assert ok, "no limit on collectables: the hand limit is checked at the end of the turn"
    ok, _ = rules.validate_purchase("collectable", 2, {})
    assert not ok, "must be on a collectables tile"

    ok, cost = rules.validate_purchase("hospital", 14, {})
    assert ok and cost == 30
    ok, cost = rules.validate_purchase("hospital", 15, {}, doctor_in_play=True)
    assert ok and cost == 60
    ok, _ = rules.validate_purchase("hospital", 15, {}, no_access=True)
    assert not ok
    ok, _ = rules.validate_purchase("hospital", 15, {"hospital": 5})
    assert not ok

    ok, cost = rules.validate_purchase("black_market", 19, {})
    assert ok and cost == 150
    ok, _ = rules.validate_purchase("black_market", 19, {"black_market": 1})
    assert not ok
    ok, _ = rules.validate_purchase("nonsense", 19, {})
    assert not ok
    print("PASS: purchases")


def test_ensure_players_assigns_colours_and_late_joiners_queue():
    state = rules.new_state()
    assert rules.ensure_players(state, [1, 2]) is True
    assert state["positions"] == {"1": 0, "2": 0}
    assert len(set(state["colors"].values())) == 2
    assert rules.ensure_players(state, [1, 2]) is False

    state["started"] = True
    state["turn_order"] = [2, 1]
    rules.ensure_players(state, [1, 2, 3])
    assert state["turn_order"] == [2, 1, 3]
    print("PASS: ensure_players")


def test_log_is_capped():
    state = rules.new_state()
    for i in range(rules.LOG_LIMIT + 10):
        rules.add_log(state, f"entry {i}")
    assert len(state["log"]) == rules.LOG_LIMIT
    assert state["log"][-1]["seq"] == rules.LOG_LIMIT + 10
    print("PASS: log cap")


def test_shuffled_order_is_a_permutation():
    order = rules.draw_turn_order([1, 2, 3, 4], rng=random.Random(7))
    assert sorted(order) == [1, 2, 3, 4]
    print("PASS: turn order draw")


def test_time_virus_and_heat():
    assert [rules.time_virus_minutes(r) for r in range(1, 7)] == [30, 60, 90, 120, 150, 180]
    assert rules.heat_threshold(None) == 3
    assert rules.heat_threshold("Manager") == 3
    assert rules.heat_threshold("Senior") == 4
    assert rules.heat_threshold("Executive") == 4
    print("PASS: time virus & heat")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("\nAll board rule tests passed.")
