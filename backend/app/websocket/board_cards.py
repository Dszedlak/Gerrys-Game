"""
Card decks for the board: Scenario cards, Assignment slips, Collectables,
and the deck cards dealt straight into a hand - Job Opportunities, Promotion
cards and Hospital items (bandages).

The cards themselves belong to a game version (see app/game_versions.py
and app/card_import.py); each room plays the version it was created with.
A card can
carry `effects`, which the server applies when the card is drawn (scenario),
played (collectable), or - as `reward` - when an assignment is completed.
Anything the engine can't do by itself is a `note` effect: it is shown on the
card for the table to resolve by hand.

Like board_rules.py this module is pure: no database, no sockets. Effects are
computed against a plain dict of players and returned as a list of changes
for board.py to persist.
"""
import random

DECK_NAMES = ("scenario", "assignment", "collectable", "job", "promotion", "hospital", "shortcut", "oppression")
# Decks whose cards go into a player's hand
HAND_DECKS = ("collectable", "job", "promotion", "hospital", "shortcut")
# Hand cards that count towards the "5 collectables" hand limit: every card in your hand
HAND_LIMIT_DECKS = HAND_DECKS
# Decks shuffled into another deck's pile: Promotion cards are part of the Collectables deck
# (their entries in that pile carry their deck: "promotion:<id>#<n>")
MERGED_DECKS = {"promotion": "collectable"}

STARTING_HAND = 2
MAX_ASSIGNMENTS = 6
MAX_PER_TARGET = 3
MAX_EQUIPPED = 2

BLEED_MAX = 64
HEAT_MAX = 10

DECK_LABELS = {
    "scenario": "scenario card", "assignment": "assignment slip", "collectable": "collectable",
    "job": "job opportunity", "promotion": "promotion card", "hospital": "hospital item",
    "shortcut": "shortcut card", "oppression": "government oppression",
}

# Government oppressions: at most this many in play; introduced at the Senate
MAX_OPPRESSIONS = 4
OPPRESSION_COST = 120
# Uses per turn by government (Republic: one per state enemy, against state enemies only)
OPPRESSION_USES = {"Communism": 2, "Dictatorship": 3, "Republic": 1}
OPPRESSION_LEADER_ROLES = {"Communism": {"politburo"}, "Dictatorship": {"dictator"}, "Republic": {"head_of_state"}}

SELECTORS = ("self", "all", "others", "choose", "random", "richest", "poorest")

NAMED_TILES = {
    "start": 0,
    "job_centre": 5,
    "senate": 9,
    "hospital": 14,
    "black_market": 19,
}


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def parse_cards(raw: dict) -> dict:
    """{deck: {card_id: card}} from a version's JSON ({deck: [card, ...]})."""
    out = {}
    for deck in DECK_NAMES:
        cards = {}
        for c in raw.get(deck, []) or []:
            if not isinstance(c, dict) or "id" not in c:
                continue
            cid = str(c["id"])
            effects = c.get("effects") or []
            reward = c.get("reward") or []
            cards[cid] = {
                "id": cid,
                "deck": deck,
                "title": str(c.get("title", "")),
                "text": str(c.get("text", "")),
                "copies": max(1, int(c.get("copies", 1) or 1)),
                "effects": effects,
                "reward": reward,
                "equip": bool(c.get("equip", False)),
                "example": bool(c.get("example", False)),
                # e.g. the Revolution Token, which starts the game on the discard pile
                "start_in_discard": bool(c.get("start_in_discard", False)),
                # Red-named cards (the Contraband scenario card hunts for them)
                "contraband": bool(c.get("contraband", False)),
                # "Not a one-use item": using it doesn't discard it
                "reusable": bool(c.get("reusable", False)),
                # e.g. "Court", "All players", "War" (War rolls: Hell Bent adds dice)
                "kind": str(c.get("kind") or ""),
                # Always-on equipped collectables: "charm", "hell_bent", "efficiency"
                "passive": c.get("passive") or None,
                # A scenario script to run instead of the generic effects (board_events.py)
                "script": c.get("script") or None,
            }
        out[deck] = cards
    return out


# --------------------------------------------------------------------------
# Piles
# --------------------------------------------------------------------------
# A pile holds card *instances*: "<card id>#<copy>", so that several copies
# of one card can be told apart in hands and on the discard pile.

def card_id(instance: str) -> str:
    return str(instance).split("#", 1)[0]


def card_of(cards: dict, deck: str, instance: str):
    head = str(instance).split("#", 1)[0]
    if ":" in head:   # a merged deck's card inside another pile ("promotion:<id>#<n>")
        deck, instance = str(instance).split(":", 1)
    return (cards.get(deck) or {}).get(card_id(instance))


def build_pile(deck_cards: dict, rng=random) -> list:
    pile = [f"{cid}#{n}" for cid, c in deck_cards.items() if not c.get("start_in_discard")
            for n in range(1, c["copies"] + 1)]
    rng.shuffle(pile)
    return pile


def starting_discard(deck_cards: dict) -> list:
    return [f"{cid}#{n}" for cid, c in deck_cards.items() if c.get("start_in_discard")
            for n in range(1, c["copies"] + 1)]


def new_deck(deck_cards: dict, rng=random) -> dict:
    return {"draw": build_pile(deck_cards, rng), "discard": starting_discard(deck_cards)}


def new_decks(cards: dict, rng=random) -> dict:
    decks = {d: new_deck(cards.get(d, {}), rng) for d in DECK_NAMES}
    for merged, into in MERGED_DECKS.items():
        extra = decks[merged]
        decks[into]["draw"] += [f"{merged}:{i}" for i in extra["draw"]]
        decks[into]["discard"] += [f"{merged}:{i}" for i in extra["discard"]]
        rng.shuffle(decks[into]["draw"])
        decks[merged] = {"draw": [], "discard": []}
    return decks


def available(decks: dict, deck: str) -> int:
    """How many cards of `deck` could still be drawn (draw + discard piles)."""
    pile = decks.get(deck) or {"draw": [], "discard": []}
    n = len(pile["draw"]) + len(pile["discard"])
    into = MERGED_DECKS.get(deck)
    if into:
        host = decks.get(into) or {"draw": [], "discard": []}
        n += sum(1 for e in host["draw"] + host["discard"] if str(e).startswith(deck + ":"))
    return n


def shuffle_deck(decks: dict, deck: str, rng=random) -> int:
    """Shuffle the discard pile back into the draw pile. Returns the new deck size."""
    pile = decks.setdefault(deck, {"draw": [], "discard": []})
    pile["draw"] = pile["draw"] + pile["discard"]
    pile["discard"] = []
    rng.shuffle(pile["draw"])
    return len(pile["draw"])


# Hands mix several decks, so a hand entry carries its deck: collectables are
# stored as plain instances ("co-knife#2"), everything else as "job:job-opportunity#3".

def hand_entry(deck: str, instance: str) -> str:
    return instance if deck == "collectable" else f"{deck}:{instance}"


def split_entry(entry: str):
    """(deck, instance) for a hand entry."""
    head = str(entry).split("#", 1)[0]
    if ":" in head:
        deck, rest = str(entry).split(":", 1)
        if deck in HAND_DECKS:
            return deck, rest
    return "collectable", str(entry)


def draw(decks: dict, deck: str, cards: dict, rng=random):
    """
    Take the top card of `deck`, shuffling the discard pile back in when the
    draw pile runs out. Returns (instance or None, reshuffled).
    Instances whose card has since been removed from cards.json are skipped.
    """
    pile = decks.setdefault(deck, {"draw": [], "discard": []})
    into = MERGED_DECKS.get(deck)
    if into and not pile["draw"] and not pile["discard"]:
        # e.g. a Promotion card: the first one in the Collectables deck (or its discard pile)
        host = decks.setdefault(into, {"draw": [], "discard": []})
        prefix = deck + ":"
        for src in ("draw", "discard"):
            for i in range(len(host[src]) - 1, -1, -1):
                entry = host[src][i]
                if str(entry).startswith(prefix) and card_of(cards, deck, entry[len(prefix):]):
                    host[src].pop(i)
                    return entry[len(prefix):], False
        return None, False
    reshuffled = False
    while True:
        if not pile["draw"]:
            if not pile["discard"] or reshuffled:
                return None, reshuffled
            pile["draw"], pile["discard"] = pile["discard"], []
            rng.shuffle(pile["draw"])
            reshuffled = True
        instance = pile["draw"].pop()
        if card_of(cards, deck, instance):
            return instance, reshuffled


def discard(decks: dict, deck: str, instance: str):
    into = MERGED_DECKS.get(deck)
    if into and ":" not in str(instance).split("#", 1)[0]:
        decks.setdefault(into, {"draw": [], "discard": []})["discard"].append(f"{deck}:{instance}")
        return
    decks.setdefault(deck, {"draw": [], "discard": []})["discard"].append(instance)


def public_card(card: dict, instance: str = None) -> dict:
    """What clients are told about a card (never the deck order)."""
    if not card:
        return None
    effects = card["effects"] if card["deck"] != "assignment" else card["reward"]
    return {
        "uid": instance,
        "id": card["id"],
        "deck": card["deck"],
        "title": card["title"],
        "text": card["text"],
        "equip": card["equip"],
        "example": card["example"],
        "needs_target": needs_choice(effects),
        "contraband": card.get("contraband", False),
        "reusable": card.get("reusable", False),
        "kind": card.get("kind", ""),
        "notes": [e.get("text", "") for e in effects if isinstance(e, dict) and e.get("type") == "note"],
    }


# --------------------------------------------------------------------------
# Assignments
# --------------------------------------------------------------------------

def assignments_against(assignments: list, user_id) -> int:
    return sum(1 for a in assignments if a.get("target") == user_id)


def black_bag(alive_ids, assignments: list, rng=random):
    """Draw a target counter: any alive player with fewer than MAX_PER_TARGET assignments on them."""
    pool = [u for u in alive_ids if assignments_against(assignments, u) < MAX_PER_TARGET]
    return rng.choice(pool) if pool else None


def replaceable(assignments: list, drawer) -> list:
    """With the board full, the drawer may replace any slip not aimed at themselves."""
    return [a for a in assignments if a.get("target") != drawer]


# --------------------------------------------------------------------------
# Effects
# --------------------------------------------------------------------------

def needs_choice(effects) -> bool:
    """Does any effect (including those inside rolls) target a chosen player?"""
    for e in effects or []:
        if not isinstance(e, dict):
            continue
        if e.get("who") == "choose":
            return True
        nested = list(e.get("success") or []) + list(e.get("failure") or [])
        for outcome in (e.get("outcomes") or {}).values():
            nested += list(outcome or [])
        if nested and needs_choice(nested):
            return True
    return False


def _fmt(minutes: int) -> str:
    sign = "+" if minutes >= 0 else "−"
    minutes = abs(int(minutes))
    h, m = divmod(minutes, 60)
    if h and m:
        body = f"{h}h {m}m"
    elif h:
        body = f"{h}h"
    else:
        body = f"{m}m"
    return f"{sign}{body}"


EFFECT_TYPES = {"time", "time_roll", "time_percent", "steal", "give", "bleed", "heat", "move", "jail",
                "fire", "demote", "draw", "take_discard", "skip_turn", "roll_check", "roll_table", "roll_until", "note"}


def walk_effects(effects):
    """Every effect, including those nested inside rolls."""
    for e in effects or []:
        if not isinstance(e, dict):
            continue
        yield e
        yield from walk_effects(e.get("success"))
        yield from walk_effects(e.get("failure"))
        for outcome in (e.get("outcomes") or {}).values():
            yield from walk_effects(outcome)


def is_selector(who) -> bool:
    """self/all/others/..., "leaders", or "faction:<Faction>[:tier<N>|:titled]"."""
    if who in SELECTORS or who == "leaders":
        return True
    if isinstance(who, str) and who.startswith("faction:"):
        parts = who.split(":")
        return len(parts) in (2, 3) and bool(parts[1]) and (
            len(parts) == 2 or parts[2] == "titled" or (parts[2].startswith("tier") and parts[2][4:].isdigit()))
    return False


def resolve_who(who, actor, players: dict, chosen=None, rng=random) -> list:
    """User ids an effect applies to. Only alive players are ever targeted."""
    alive = [u for u, p in players.items() if p.get("alive")]
    if who in (None, "self"):
        return [actor] if actor in players else []
    if who == "all":
        return alive
    if who == "others":
        return [u for u in alive if u != actor]
    if who == "choose":
        return [chosen] if chosen in players and players[chosen].get("alive") else []
    if who == "random":
        pool = [u for u in alive if u != actor]
        return [rng.choice(pool)] if pool else []
    if who in ("richest", "poorest"):
        if not alive:
            return []
        pick = max if who == "richest" else min
        best = pick(players[u]["minutes"] for u in alive)
        return [u for u in alive if players[u]["minutes"] == best]
    if who == "leaders":
        return [u for u in alive if players[u].get("leader")]
    if isinstance(who, str) and who.startswith("faction:"):
        parts = who.split(":")
        faction = parts[1].lower()
        picked = [u for u in alive if (players[u].get("faction") or "").lower() == faction]
        if len(parts) == 3 and parts[2] == "titled":
            picked = [u for u in picked if players[u].get("titled")]
        elif len(parts) == 3:
            tier = int(parts[2][4:])
            picked = [u for u in picked if players[u].get("tier") == tier]
        return picked
    return []


def _face_matches(key, value) -> bool:
    """Roll-table keys are a face ("4"), a range ("5-6") or "else"."""
    key = str(key)
    if "-" in key:
        lo, hi = key.split("-", 1)
        return int(lo) <= value <= int(hi)
    return key.isdigit() and int(key) == value


def apply_effects(effects, actor, players: dict, *, chosen=None, rng=random, context=None) -> dict:
    """
    Work out what a card does.

    `players` is {user_id: {"name", "minutes", "bleed", "heat", "alive",
    "faction", "tier", "titled", "leader"}}; it is not modified. Effects apply
    in order against a working copy, so a steal after a loss only takes what
    is left. Rolls (court cases, roll tables, everyone-rolls checks) contain
    further effects, which apply with the roller as "self".

    `context` carries table facts: {"judge": True} when a Judge is in play
    (court cases are then left to the Judge instead of rolled).

    Returns {
      "players": the working copy after every effect (minutes/bleed/heat),
      "moves": {uid: tile}, "jail": [uid], "draw": [(uid, deck, count)],
      "skip": [uid], "fire": [uid], "take_discard": [(uid, n)],
      "rolls": [int], "lines": [str], "notes": [str],
    }
    """
    context = context or {}
    work = {u: dict(p) for u, p in players.items()}
    out = {"players": work, "moves": {}, "jail": [], "draw": [], "skip": [], "take_discard": [], "fire": [],
           "demote": [], "rolls": [], "lines": [], "notes": []}

    def name(u):
        return work[u].get("name") or "Someone"

    def add_minutes(u, delta):
        before = work[u]["minutes"]
        work[u]["minutes"] = max(0, before + int(delta))
        return work[u]["minutes"] - before

    def roll():
        value = rng.randint(1, 6)
        out["rolls"].append(value)
        return value

    def run(effect_list, me):
        for e in effect_list or []:
            if isinstance(e, dict):
                apply_one(e, me)

    def apply_one(e, me):
        kind = e.get("type")
        targets = resolve_who(e.get("who", "self"), me, work, chosen, rng)

        if kind == "time":
            for u in targets:
                d = add_minutes(u, e.get("minutes", 0))
                out["lines"].append(f"{name(u)} {_fmt(d)}")

        elif kind == "time_roll":
            dice = [roll() for _ in range(max(1, int(e.get("dice", 1))))]
            total = sum(dice) * int(e.get("per_pip", 0))
            out["lines"].append(f"Rolled {' + '.join(map(str, dice))}")
            for u in targets:
                d = add_minutes(u, total)
                out["lines"].append(f"{name(u)} {_fmt(d)}")

        elif kind == "time_percent":
            # e.g. lose half your time, at most 8 hours
            pct = float(e.get("percent", 0))
            cap = e.get("cap")
            for u in targets:
                delta = int(round(work[u]["minutes"] * pct / 100))
                if cap is not None:
                    delta = max(-int(cap), min(int(cap), delta))
                d = add_minutes(u, delta)
                out["lines"].append(f"{name(u)} {_fmt(d)}")

        elif kind in ("steal", "give"):
            amount = max(0, int(e.get("minutes", 0)))
            for u in targets:
                if u == me or me not in work:
                    continue
                src, dst = (u, me) if kind == "steal" else (me, u)
                moved = min(amount, work[src]["minutes"])
                add_minutes(src, -moved)
                add_minutes(dst, moved)
                verb = "took" if kind == "steal" else "gave"
                out["lines"].append(f"{name(me)} {verb} {_fmt(moved)[1:]} {'from' if kind == 'steal' else 'to'} {name(u)}")

        elif kind in ("bleed", "heat"):
            cap = BLEED_MAX if kind == "bleed" else HEAT_MAX
            for u in targets:
                before = work[u].get(kind, 0)
                work[u][kind] = min(cap, max(0, before + int(e.get("amount", 0))))
                d = work[u][kind] - before
                label = "bleeding" if kind == "bleed" else "heat"
                out["lines"].append(f"{name(u)} {'+' if d >= 0 else '−'}{abs(d)} {label}")

        elif kind == "move":
            to = e.get("to")
            tile = NAMED_TILES.get(to) if isinstance(to, str) else to
            if isinstance(tile, int) and 0 <= tile < 20:
                for u in (targets if "who" in e else [me]):
                    out["moves"][u] = tile
                    out["lines"].append(f"{name(u)} moves to tile {tile}" if not isinstance(to, str)
                                        else f"{name(u)} moves to {to.replace('_', ' ').title()}")

        elif kind == "jail":
            for u in targets:
                if u not in out["jail"]:
                    out["jail"].append(u)
                    out["lines"].append(f"{name(u)} goes to Jail")

        elif kind == "fire":
            for u in targets:
                if u not in out["fire"] and work[u].get("tier"):
                    out["fire"].append(u)
                    work[u]["tier"] = 0
                    out["lines"].append(f"{name(u)} loses their job")

        elif kind == "demote":
            for u in targets:
                if u not in out["demote"] and work[u].get("titled"):
                    out["demote"].append(u)
                    out["lines"].append(f"{name(u)} is demoted one title level")
                elif not work[u].get("titled"):
                    out["lines"].append(f"{name(u)} has no title to lose")

        elif kind == "draw":
            deck = e.get("deck", "collectable")
            count = max(1, int(e.get("count", 1)))
            label = DECK_LABELS.get(deck, deck)
            for u in (targets if "who" in e else [me]):
                out["draw"].append((u, deck, count))
                out["lines"].append(f"{name(u)} draws {count} {label}{'s' if count > 1 else ''}")

        elif kind == "take_discard":
            count = max(1, int(e.get("count", 1)))
            for u in (targets if "who" in e else [me]):
                out["take_discard"].append((u, count))
                out["lines"].append(f"{name(u)} may take {count} card{'s' if count > 1 else ''} from the discard pile")

        elif kind == "skip_turn":
            for u in targets:
                out["skip"].append(u)
                out["lines"].append(f"{name(u)} misses their next turn")

        elif kind == "roll_check":
            # Each target rolls: threshold or higher succeeds. Court cases go
            # to the Judge instead when one is in play.
            if e.get("court") and context.get("judge"):
                out["notes"].append("A Judge is in play, so the Judge decides this case (A or B) instead of a roll.")
                return
            for u in targets:
                need = int(e.get("leader_threshold", e.get("threshold", 5))) if work[u].get("leader") \
                    else int(e.get("threshold", 5))
                if not e.get("no_charm"):
                    need = max(1, need - int((context.get("charms") or {}).get(u, 0)))
                value = roll()
                ok = value >= need
                label = e.get("label") or ("Court" if e.get("court") else "Roll")
                out["lines"].append(f"{label}: {name(u)} rolled {value} — {'success' if ok else 'failed'}")
                run(e.get("success" if ok else "failure"), u)

        elif kind == "roll_table":
            for u in targets:
                value = roll()
                out["lines"].append(f"{name(u)} rolled {value}")
                outcomes = e.get("outcomes") or {}
                match = next((k for k in outcomes if _face_matches(k, value)), None)
                run(outcomes.get(match if match is not None else "else"), u)

        elif kind == "roll_until":
            # Roll until a face comes up, paying for every roll before it (Mafia)
            face = int(e.get("face", 6))
            per = int(e.get("per_roll", 0))
            for u in targets:
                misses = 0
                while rng.randint(1, 6) != face and misses < 50:
                    misses += 1
                d = add_minutes(u, per * misses)
                out["lines"].append(f"{name(u)} rolled {misses + 1} time{'s' if misses else ''}: {_fmt(d)}")

        elif kind == "note":
            if e.get("text"):
                out["notes"].append(str(e["text"]))

    run(effects, actor)
    return out
