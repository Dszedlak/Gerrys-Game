"""
Tests for the spreadsheet importer in app/card_import.py (pure Python).
Run with:  python backend/tests/test_card_import.py
"""
import importlib.util
import json
import os

_DIR = os.path.join(os.path.dirname(__file__), "..", "app")
_spec = importlib.util.spec_from_file_location("card_import", os.path.join(_DIR, "card_import.py"))
ci = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ci)


def test_times():
    assert ci.parse_minutes("30") == 30
    assert ci.parse_minutes("-30m") == -30
    assert ci.parse_minutes("1h") == 60
    assert ci.parse_minutes("+1.5h") == 90
    assert ci.parse_minutes("-2h30") == -150
    print("PASS: times")


def test_effects_syntax():
    effects, warnings = ci.parse_effects(
        "time everyone -30; steal choose 1.5h\nroll others -10; heat self +1; bleed choose 2;"
        " move start; jail richest; skip random; draw 2; note Admin sets Anarchy"
    )
    assert not warnings, warnings
    assert effects == [
        {"who": "all", "type": "time", "minutes": -30},
        {"type": "steal", "who": "choose", "minutes": 90},
        {"who": "others", "type": "time_roll", "per_pip": -10, "dice": 1},
        {"type": "heat", "who": "self", "amount": 1},
        {"type": "bleed", "who": "choose", "amount": 2},
        {"type": "move", "to": "start"},
        {"type": "jail", "who": "richest"},
        {"type": "skip_turn", "who": "random"},
        {"type": "draw", "deck": "collectable", "count": 2},
        {"type": "note", "text": "Admin sets Anarchy"},
    ]
    # Round trip through the export format
    again, _ = ci.parse_effects(ci.format_effects(effects))
    assert again == effects
    print("PASS: effects syntax")


def test_bad_clauses_become_notes_with_a_warning():
    effects, warnings = ci.parse_effects("time nobody -30; explode all")
    assert [e["type"] for e in effects] == ["note", "note"]
    assert len(warnings) == 2
    effects, warnings = ci.parse_effects('[{"type": "time", "who": "self", "minutes": 5}]')
    assert effects == [{"type": "time", "who": "self", "minutes": 5}] and not warnings
    print("PASS: bad clauses")


def test_sheets_with_loose_headers():
    sheets = {
        "Scenario Cards": [
            ["Gerry's Game scenario list"],           # a title row above the header is fine
            ["Card Name", "Description", "Qty", "Automation"],
            ["Tax Audit", "Everyone loses 30 minutes.", "2", "time all -30"],
            ["Tax Audit", "A second card with the same name", "", ""],
            ["", "", "", ""],
        ],
        "assignments": [["Name", "Text", "Reward"], ["Snitch", "Get your target jailed.", "time self 1h"]],
        "Collectables": [["Title", "Text", "Equip", "Effects"], ["Body Armour", "+1 vs War", "yes", ""]],
        "Notes": [["anything"]],
    }
    decks, warnings = ci.sheets_to_cards(sheets)
    assert [c["id"] for c in decks["scenario"]] == ["sc-tax-audit", "sc-tax-audit-2"]
    assert decks["scenario"][0]["copies"] == 2 and decks["scenario"][0]["effects"][0]["minutes"] == -30
    assert "effects" not in decks["scenario"][1]
    assert decks["assignment"][0]["reward"] == [{"who": "self", "type": "time", "minutes": 60}]
    assert decks["collectable"][0]["equip"] is True
    assert any("Notes" in w for w in warnings)
    print("PASS: loose headers")


def test_xlsx_round_trip():
    path = os.path.join(_DIR, "data_collections", "game_versions", "4.27-example.json")
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    data = ci.write_xlsx(ci.version_to_sheets(doc))
    sheets = ci.read_xlsx(data)
    assert set(sheets) == set(ci.SHEET_TITLES.values())
    back, warnings = ci.build_version(sheets, key="4.27-copy")
    assert not [w for w in warnings if "row" in w], warnings
    for deck in ci.DECKS:
        assert [c["title"] for c in back[deck]] == [c["title"] for c in doc.get(deck, [])]
        for a, b in zip(back[deck], doc.get(deck, [])):
            key = "reward" if deck == "assignment" else "effects"
            # Example flags aren't exported, everything that drives the game is
            assert a.get(key, []) == b.get(key, []), (a, b)
            assert a.get("copies", 1) == b.get("copies", 1)
            assert bool(a.get("equip")) == bool(b.get("equip"))
            assert bool(a.get("start_in_discard")) == bool(b.get("start_in_discard"))
    print("PASS: xlsx round trip")


def test_version_key_is_checked():
    for bad in ("", "has space", "x" * 40):
        try:
            ci.build_version({"Scenario": [["Title"], ["A"]]}, key=bad)
        except ci.ImportError_:
            continue
        raise AssertionError(f"accepted key {bad!r}")
    try:
        ci.sheets_to_cards({"Random": [["Title"], ["A"]]})
    except ci.ImportError_:
        pass
    else:
        raise AssertionError("an upload with no decks should fail")
    print("PASS: key and empty upload checks")



def test_hand_deck_sheets_and_new_effects():
    assert ci.deck_for_sheet("Hospital Items") == "hospital"
    assert ci.deck_for_sheet("Bandages") == "hospital"
    assert ci.deck_for_sheet("Job Opportunities") == "job"
    assert ci.deck_for_sheet("Promotion Cards") == "promotion"
    assert ci.deck_for_sheet("Collectables") == "collectable"
    effects, warnings = ci.parse_effects("takediscard 1; draw 2 bandages; draw 1")
    assert not warnings
    assert effects == [{"type": "take_discard", "count": 1},
                       {"type": "draw", "deck": "hospital", "count": 2},
                       {"type": "draw", "deck": "collectable", "count": 1}]
    assert ci.parse_effects(ci.format_effects(effects))[0] == effects
    _, warnings = ci.parse_effects("draw 1 scenario")
    assert warnings, "scenario cards can't be drawn into a hand"
    decks, _ = ci.sheets_to_cards({"Collectables": [["Title", "Start in discard"], ["Revolution Token", "yes"]]})
    assert decks["collectable"][0]["start_in_discard"] is True
    print("PASS: hand decks and new effects")


def test_the_card_workbook():
    """The real Gerrys_Game_Cards.xlsx: every deck, quantities, flags and automation."""
    path = os.path.join(_DIR, "data_collections", "game_versions", "spreadsheets", "Gerrys_Game_Cards.xlsx")
    if not os.path.exists(path):
        print("SKIP: card workbook not present")
        return
    with open(path, "rb") as f:
        sheets = ci.read_xlsx(f.read())
    assert ci.is_card_workbook(sheets)
    doc, warnings = ci.build_version(sheets, key="4.27")
    count = {d: sum(c["copies"] for c in doc[d]) for d in ci.DECKS}
    assert len(doc["scenario"]) == 30 and count["assignment"] == 31 and count["promotion"] == 15
    by_title = {c["title"]: c for d in ci.DECKS for c in doc[d]}
    assert by_title["Throwing Knife"]["contraband"] and by_title["Throwing Knife"]["effects"][0]["type"] == "bleed"
    assert by_title["Charm"]["reusable"] and by_title["Charm"]["equip"]
    assert by_title["Bandages"]["effects"] == [{"type": "bleed", "who": "self", "amount": -1}]
    revolution = [c for c in doc["collectable"] if c["title"] == "Revolution Token"]
    assert sorted((c["copies"], bool(c.get("start_in_discard"))) for c in revolution) == [(1, False), (1, True)]
    assert by_title["Inflict 3 bleed (one turn) on"]["reward"] == [{"type": "time", "who": "self", "minutes": 180}]
    assert {"jobs", "titles", "governments", "oppressions"} <= set(doc["reference"])
    assert all(c.get("effects") for c in doc["scenario"]), "every scenario card has automation or a note"
    print("PASS: card workbook")

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("\nAll import tests passed.")
