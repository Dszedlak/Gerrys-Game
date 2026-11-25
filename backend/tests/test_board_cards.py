"""
Tests for the card engine in app/websocket/board_cards.py and the bundled
game versions. No database or sockets needed. Run with:
    python backend/tests/test_board_cards.py
"""
import importlib.util
import os
import random

_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "websocket")
_spec = importlib.util.spec_from_file_location("board_cards", os.path.join(_DIR, "board_cards.py"))
cards_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cards_mod)


def players():
    return {
        1: {"name": "Ann", "minutes": 300, "bleed": 0, "heat": 0, "alive": True},
        2: {"name": "Bob", "minutes": 20, "bleed": 1, "heat": 2, "alive": True},
        3: {"name": "Cat", "minutes": 600, "bleed": 0, "heat": 0, "alive": True},
        4: {"name": "Dee", "minutes": 0, "bleed": 0, "heat": 0, "alive": False},
    }


def test_bundled_versions_are_valid():
    """Every card in every shipped version parses and uses known effect types and selectors."""
    import glob
    import json
    known = cards_mod.EFFECT_TYPES
    paths = glob.glob(os.path.join(_DIR, "..", "data_collections", "game_versions", "*.json"))
    assert paths, "no bundled versions"
    for path in paths:
        with open(path, encoding="utf-8") as f:
            cards = cards_mod.parse_cards(json.load(f))
        for deck in cards_mod.DECK_NAMES:
            for c in cards[deck].values():
                for e in cards_mod.walk_effects(c["effects"] + c["reward"]):
                    assert e["type"] in known, (path, c["id"], e)
                    assert cards_mod.is_selector(e.get("who", "self")), (path, c["id"], e)
    print("PASS: bundled versions are valid")


def test_draw_reshuffles_the_discard_pile():
    cards = {"scenario": {"a": {"id": "a", "copies": 2}, "b": {"id": "b", "copies": 1}},
             "assignment": {}, "collectable": {}}
    decks = cards_mod.new_decks(cards, rng=random.Random(1))
    assert sorted(decks["scenario"]["draw"]) == ["a#1", "a#2", "b#1"]
    drawn = [cards_mod.draw(decks, "scenario", cards)[0] for _ in range(3)]
    assert sorted(drawn) == ["a#1", "a#2", "b#1"]
    assert cards_mod.draw(decks, "scenario", cards) == (None, False)
    for d in drawn:
        cards_mod.discard(decks, "scenario", d)
    inst, reshuffled = cards_mod.draw(decks, "scenario", cards)
    assert reshuffled and inst in drawn
    print("PASS: draw & reshuffle")


def test_time_effects_floor_at_zero_and_only_hit_the_living():
    out = cards_mod.apply_effects([{"type": "time", "who": "all", "minutes": -30}], 1, players())
    assert out["players"][1]["minutes"] == 270
    assert out["players"][2]["minutes"] == 0          # had 20
    assert out["players"][4]["minutes"] == 0          # dead, untouched
    assert len(out["lines"]) == 3
    print("PASS: time effects")


def test_steal_takes_only_what_is_there():
    out = cards_mod.apply_effects([{"type": "steal", "who": "choose", "minutes": 60}], 1, players(), chosen=2)
    assert out["players"][2]["minutes"] == 0
    assert out["players"][1]["minutes"] == 320
    print("PASS: steal")


def test_selectors():
    p = players()
    assert cards_mod.resolve_who("others", 1, p) == [2, 3]
    assert cards_mod.resolve_who("richest", 1, p) == [3]
    assert cards_mod.resolve_who("poorest", 1, p) == [2]
    assert cards_mod.resolve_who("choose", 1, p, chosen=4) == []   # can't pick the dead
    assert cards_mod.resolve_who("random", 1, p, rng=random.Random(3)) in ([2], [3])
    print("PASS: selectors")


def test_counters_moves_and_specials():
    effects = [
        {"type": "heat", "who": "self", "amount": 2},
        {"type": "bleed", "who": "others", "amount": -5},
        {"type": "move", "to": "job_centre"},
        {"type": "jail", "who": "richest"},
        {"type": "draw", "deck": "collectable", "count": 2},
        {"type": "skip_turn", "who": "choose"},
        {"type": "note", "text": "Admin: set Anarchy"},
    ]
    out = cards_mod.apply_effects(effects, 1, players(), chosen=2)
    assert out["players"][1]["heat"] == 2
    assert out["players"][2]["bleed"] == 0
    assert out["moves"] == {1: 5}
    assert out["jail"] == [3]
    assert out["draw"] == [(1, "collectable", 2)]
    assert out["skip"] == [2]
    assert out["notes"] == ["Admin: set Anarchy"]
    print("PASS: counters, moves and specials")


def test_time_roll_rolls_once_for_everyone():
    out = cards_mod.apply_effects([{"type": "time_roll", "who": "others", "per_pip": -10}], 1, players(),
                                  rng=random.Random(5))
    (roll,) = out["rolls"]
    assert out["players"][3]["minutes"] == 600 - roll * 10
    print("PASS: time roll")


def test_black_bag_respects_the_three_per_target_limit():
    assert cards_mod.MAX_PER_TARGET == 3
    assignments = [{"target": 2}, {"target": 2}, {"target": 2}, {"target": 3}]
    for seed in range(20):
        assert cards_mod.black_bag([1, 2, 3], assignments, rng=random.Random(seed)) in (1, 3)
    assert cards_mod.black_bag([2], assignments) is None
    assert [a["target"] for a in cards_mod.replaceable(assignments, 2)] == [3]
    print("PASS: black bag")


def test_public_card_hides_nothing_secret_but_flags_targets():
    cards = cards_mod.parse_cards({"collectable": [{"id": "k", "title": "Knife", "effects": [{"type": "bleed", "who": "choose", "amount": 1}]}]})
    some = cards["collectable"]["k"]
    pub = cards_mod.public_card(some, "x#1")
    assert set(pub) == {"uid", "id", "deck", "title", "text", "equip", "example", "needs_target", "notes",
                        "contraband", "reusable", "kind"}
    assert pub["needs_target"] is True
    print("PASS: public card")



def test_shuffle_puts_discards_back():
    cards = {"collectable": {"a": {"id": "a", "copies": 3}}}
    decks = cards_mod.new_decks(cards, rng=random.Random(2))
    used = [cards_mod.draw(decks, "collectable", cards)[0] for _ in range(2)]
    for u in used:
        cards_mod.discard(decks, "collectable", u)
    assert len(decks["collectable"]["discard"]) == 2
    assert cards_mod.shuffle_deck(decks, "collectable", rng=random.Random(3)) == 3
    assert decks["collectable"]["discard"] == []
    print("PASS: shuffle")


def test_start_in_discard_and_hand_entries():
    cards = cards_mod.parse_cards({"collectable": [
        {"id": "rev", "title": "Revolution Token", "start_in_discard": True},
        {"id": "k", "title": "Knife", "copies": 2},
    ]})
    decks = cards_mod.new_decks(cards)
    assert decks["collectable"]["discard"] == ["rev#1"]
    assert sorted(decks["collectable"]["draw"]) == ["k#1", "k#2"]
    assert decks["job"] == {"draw": [], "discard": []}
    assert cards_mod.hand_entry("collectable", "k#1") == "k#1"
    assert cards_mod.hand_entry("hospital", "bandage#4") == "hospital:bandage#4"
    assert cards_mod.split_entry("hospital:bandage#4") == ("hospital", "bandage#4")
    assert cards_mod.split_entry("k#1") == ("collectable", "k#1")
    # A collectable whose id happens to contain a colon stays a collectable
    assert cards_mod.split_entry("odd:id#1") == ("collectable", "odd:id#1")
    print("PASS: start in discard & hand entries")


def test_take_discard_and_draw_other_decks():
    out = cards_mod.apply_effects([{"type": "take_discard", "count": 1},
                                   {"type": "draw", "deck": "hospital", "count": 2}], 1, players())
    assert out["take_discard"] == [(1, 1)]
    assert out["draw"] == [(1, "hospital", 2)]
    assert "discard pile" in out["lines"][0] and "hospital items" in out["lines"][1]
    print("PASS: take discard & draw other decks")


def table_players():
    return {
        1: {"name": "Ann", "minutes": 600, "bleed": 0, "heat": 0, "alive": True, "faction": "Finance", "tier": 3, "titled": True, "leader": True},
        2: {"name": "Bob", "minutes": 300, "bleed": 2, "heat": 1, "alive": True, "faction": "Finance", "tier": 1, "titled": False, "leader": False},
        3: {"name": "Cat", "minutes": 900, "bleed": 0, "heat": 0, "alive": True, "faction": "Illicit", "tier": 2, "titled": False, "leader": False},
        4: {"name": "Dee", "minutes": 0, "bleed": 0, "heat": 0, "alive": False, "faction": "Finance", "tier": 1, "titled": False, "leader": False},
    }


class FixedRng:
    """Deterministic dice: hands out the given rolls in order."""
    def __init__(self, rolls):
        self.rolls = list(rolls)

    def randint(self, lo, hi):
        return self.rolls.pop(0)

    def choice(self, seq):
        return seq[0]


def test_faction_and_leader_selectors():
    p = table_players()
    assert cards_mod.resolve_who("faction:Finance", 3, p) == [1, 2]          # Dee is dead
    assert cards_mod.resolve_who("faction:Finance:tier1", 3, p) == [2]
    assert cards_mod.resolve_who("faction:Finance:titled", 3, p) == [1]
    assert cards_mod.resolve_who("faction:public service", 3, p) == []
    assert cards_mod.resolve_who("leaders", 3, p) == [1]
    assert cards_mod.is_selector("faction:Finance:tier3") and not cards_mod.is_selector("faction:")
    print("PASS: faction & leader selectors")


def test_court_case_rolls_unless_a_judge_decides():
    case = [{"type": "roll_check", "who": "self", "threshold": 5, "court": True,
             "success": [{"type": "time", "who": "self", "minutes": 360}],
             "failure": [{"type": "time", "who": "self", "minutes": -240}, {"type": "heat", "who": "self", "amount": 2}]}]
    won = cards_mod.apply_effects(case, 2, table_players(), rng=FixedRng([5]))
    assert won["players"][2]["minutes"] == 660 and won["rolls"] == [5]
    lost = cards_mod.apply_effects(case, 2, table_players(), rng=FixedRng([4]))
    assert lost["players"][2]["minutes"] == 60 and lost["players"][2]["heat"] == 3
    judged = cards_mod.apply_effects(case, 2, table_players(), rng=FixedRng([]), context={"judge": True})
    assert judged["players"][2]["minutes"] == 300 and "Judge" in judged["notes"][0]
    print("PASS: court case")


def test_everyone_rolls_with_a_lower_target_for_leaders():
    curfew = [{"type": "roll_check", "who": "all", "threshold": 5, "leader_threshold": 3,
               "failure": [{"type": "bleed", "who": "self", "amount": 3}, {"type": "heat", "who": "self", "amount": 1}]}]
    out = cards_mod.apply_effects(curfew, 2, table_players(), rng=FixedRng([3, 4, 6]))   # Ann(leader) 3, Bob 4, Cat 6
    assert out["players"][1]["bleed"] == 0      # leader needs only 3
    assert out["players"][2]["bleed"] == 5 and out["players"][2]["heat"] == 2
    assert out["players"][3]["bleed"] == 0
    print("PASS: everyone rolls")


def test_roll_table_and_nested_choice():
    drug = [{"type": "roll_table", "who": "self", "outcomes": {
        "1": [{"type": "bleed", "who": "self", "amount": 2}], "3-4": [{"type": "bleed", "who": "self", "amount": -2}],
        "6": [{"type": "bleed", "who": "self", "amount": -64}]}}]
    assert cards_mod.apply_effects(drug, 2, table_players(), rng=FixedRng([4]))["players"][2]["bleed"] == 0
    assert cards_mod.apply_effects(drug, 2, table_players(), rng=FixedRng([1]))["players"][2]["bleed"] == 4
    assert cards_mod.apply_effects(drug, 2, table_players(), rng=FixedRng([2]))["players"][2]["bleed"] == 2  # no entry
    strike = [{"type": "steal", "who": "choose", "minutes": 90},
              {"type": "roll_check", "who": "self", "threshold": 5, "success": [{"type": "steal", "who": "choose", "minutes": 90}]}]
    assert cards_mod.needs_choice(strike) and cards_mod.needs_choice(strike[1:])
    twice = cards_mod.apply_effects(strike, 1, table_players(), chosen=3, rng=FixedRng([6]))
    assert twice["players"][3]["minutes"] == 720 and twice["players"][1]["minutes"] == 780
    print("PASS: roll table & nested choice")


def test_fire_percent_and_mafia():
    out = cards_mod.apply_effects([{"type": "fire", "who": "faction:Finance"}], 3, table_players())
    assert out["fire"] == [1, 2]
    divorce = cards_mod.apply_effects([{"type": "time_percent", "who": "self", "percent": -50, "cap": 480}], 3, table_players())
    assert divorce["players"][3]["minutes"] == 900 - 450
    capped = cards_mod.apply_effects([{"type": "time_percent", "who": "self", "percent": -50, "cap": 60}], 3, table_players())
    assert capped["players"][3]["minutes"] == 840
    mafia = cards_mod.apply_effects([{"type": "roll_until", "who": "all", "face": 6, "per_roll": -30}], 1, table_players(),
                                    rng=FixedRng([6, 2, 3, 6, 1, 6]))
    assert [mafia["players"][u]["minutes"] for u in (1, 2, 3)] == [600, 240, 870]
    print("PASS: fire, percent & mafia")


def test_charms_lower_the_target():
    strike_again = [{"type": "roll_check", "who": "self", "threshold": 5,
                     "success": [{"type": "time", "who": "self", "minutes": 60}]}]
    plain = cards_mod.apply_effects(strike_again, 1, table_players(), rng=FixedRng([3]))
    assert plain["players"][1]["minutes"] == table_players()[1]["minutes"]
    two_charms = cards_mod.apply_effects(strike_again, 1, table_players(), rng=FixedRng([3]),
                                         context={"charms": {1: 2}})
    assert two_charms["players"][1]["minutes"] == table_players()[1]["minutes"] + 60, "two charms: 5 -> 3"
    mafia_style = [{**strike_again[0], "no_charm": True}]
    assert cards_mod.apply_effects(mafia_style, 1, table_players(), rng=FixedRng([3]),
                                   context={"charms": {1: 2}})["players"][1]["minutes"] == table_players()[1]["minutes"]
    print("PASS: charms")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("\nAll card tests passed.")
