"""
Pure rules for the Gerry's Game board.

Nothing in here touches the database or sockets, so it can be tested on its
own (see backend/tests/test_board_rules.py). The socket handlers in board.py
load the room, call these, and persist the result.

The track is the 20-tile loop from the physical board, numbered clockwise
from Start in the bottom-left corner:

    5  6  7  8  9 10        Job Centre ......... Senate
    4              11
    3              12
    2              13
    1              14
    0 19 18 17 16 15        Start ............. Hospital
"""
import random

BOARD_SIZE = 20

START = 0
JOB_CENTRE = 5
GO_TO_JOB_CENTRE = 17
BLACK_MARKET = 19
# Off-track position used while a player sits in the centre Jail tile.
JAIL = -1

TILES = [
    {"index": 0,  "kind": "start",            "label": "Start",                "sub": "-1 heat"},
    {"index": 1,  "kind": "collectables",     "label": "Collectables",         "sub": "& Promotions"},
    {"index": 2,  "kind": "assignment",       "label": "Assignment Slip",      "sub": ""},
    {"index": 3,  "kind": "scenario",         "label": "Scenario Card",        "sub": ""},
    {"index": 4,  "kind": "promotion",        "label": "Promotion Card",       "sub": "Job Centre",  "building": "job_centre"},
    {"index": 5,  "kind": "job_centre",       "label": "Job Centre",           "sub": "",            "building": "job_centre"},
    {"index": 6,  "kind": "time_virus",       "label": "Time Virus",           "sub": ""},
    {"index": 7,  "kind": "collectables",     "label": "Collectables",         "sub": "& Promotions"},
    {"index": 8,  "kind": "scenario",         "label": "Scenario Card",        "sub": ""},
    {"index": 9,  "kind": "senate",           "label": "Senate",               "sub": "Own vote: free\nOpponent: 1h\nOppression: 2h", "building": "senate"},
    {"index": 10, "kind": "senate",           "label": "Senate",               "sub": "",            "building": "senate"},
    {"index": 11, "kind": "senate_virus",     "label": "Time Virus",           "sub": "Senate",      "building": "senate"},
    {"index": 12, "kind": "assignment",       "label": "Assignment Slip",      "sub": ""},
    {"index": 13, "kind": "collectables",     "label": "Collectables",         "sub": "& Promotions"},
    {"index": 14, "kind": "hospital",         "label": "Hospital",             "sub": "30 min per item", "building": "hospital"},
    {"index": 15, "kind": "hospital",         "label": "Hospital",             "sub": "",            "building": "hospital"},
    {"index": 16, "kind": "collectables",     "label": "Collectables",         "sub": "& Promotions"},
    {"index": 17, "kind": "go_to_job_centre", "label": "Go to the Job Centre", "sub": ""},
    {"index": 18, "kind": "scenario",         "label": "Scenario Card",        "sub": ""},
    {"index": 19, "kind": "black_market",     "label": "Black Market",         "sub": "2.5h for a\nused collectable"},
]

COLLECTABLE_TILES = {t["index"] for t in TILES if t["kind"] == "collectables"}
HOSPITAL_TILES = {t["index"] for t in TILES if t.get("building") == "hospital"}
TIME_VIRUS_TILES = {t["index"] for t in TILES if t["kind"] in ("time_virus", "senate_virus")}
ASSIGNMENT_TILES = {t["index"] for t in TILES if t["kind"] == "assignment"}

# Pawn colours, handed out in join order. Names only; the client owns the hex.
PAWN_COLORS = ["red", "blue", "green", "yellow", "purple", "orange", "teal", "pink", "white", "black"]


def tile(index: int) -> dict:
    return TILES[index % BOARD_SIZE]


def tile_label(index: int) -> str:
    if index == JAIL:
        return "Jail"
    return tile(index)["label"]


# --------------------------------------------------------------------------
# Movement
# --------------------------------------------------------------------------

def compute_move(start: int, steps: int) -> dict:
    """
    Walk `steps` tiles clockwise from `start`.

    Returns the tiles stepped on (excluding `start`, including the end), where
    the move ended, and whether the player landed on or passed Start - which
    passively removes one heat.

    Landing on "Go to the Job Centre" jumps straight to the Job Centre and
    counts as passing Start, per the rules.
    """
    if start == JAIL:
        start = START
    path = [(start + i) % BOARD_SIZE for i in range(1, steps + 1)]
    end = path[-1] if path else start
    passed_start = START in path

    jumped_from = None
    if end == GO_TO_JOB_CENTRE:
        jumped_from = end
        end = JOB_CENTRE
        passed_start = True

    return {
        "from": start,
        "path": path,
        "to": end,
        "jumped_from": jumped_from,
        "passed_start": passed_start,
    }


def same_building(previous: int, current: int) -> bool:
    """
    "If the player lands on the second square on their next turn, they do not
    get access" - true when both tiles belong to the same multi-tile building
    (Job Centre, Senate or Hospital).
    """
    if previous in (None, JAIL) or current in (None, JAIL):
        return False
    a = tile(previous).get("building")
    return a is not None and a == tile(current).get("building")


def time_virus_minutes(roll: int) -> int:
    """1 = 30 minutes, 2 = 1 hour ... 6 = 3 hours."""
    return int(roll) * 30


def heat_threshold(perk) -> int:
    """Three heat sends you to Jail; four for a Senior or Executive."""
    return 4 if perk in ("Senior", "Executive") else 3


# --------------------------------------------------------------------------
# Turn order
# --------------------------------------------------------------------------

def next_turn_index(order: list, current_index: int, is_active) -> tuple:
    """
    Index of the next player in `order` for whom `is_active(user_id)` holds.

    Returns (index, wrapped) where `wrapped` is True when the turn passed the
    end of the order, i.e. a new round has started. Returns (None, False) when
    nobody is left to play.
    """
    n = len(order)
    if n == 0:
        return None, False
    if current_index is None or current_index < 0:
        current_index = -1
    for k in range(1, n + 1):
        raw = current_index + k
        idx = raw % n
        if is_active(order[idx]):
            return idx, raw >= n
    return None, False


def draw_turn_order(user_ids, rng=random) -> list:
    """The starting player is chosen at random; we shuffle the whole order."""
    order = list(user_ids)
    rng.shuffle(order)
    return order


# --------------------------------------------------------------------------
# The Reaper and the Four Horsemen
# --------------------------------------------------------------------------

REAPER_DELAY_SECONDS = 2 * 60 * 60
COUNTER_MAX = 100

HORSEMEN = [
    (25, "Pestilence", "Every alive player takes 20 minutes of bleeding effect."),
    (50, "War", "Reaper rolls the red d8 +1; each alive player rolls to beat it. Win +1 hour, lose two items."),
    (75, "Famine", "No job or title income. Every player removes 1.5 hours (returned when Famine ends)."),
    (100, "Death", "Every alive player removes the black die's value in hours."),
]


def horseman_for(counter: int):
    """The horseman for a counter value, or None before the counter starts."""
    if counter <= 0:
        return None
    for upper, name, _ in HORSEMEN:
        if counter <= upper:
            return name
    return HORSEMEN[-1][1]


def horseman_effect(name: str) -> str:
    for _, n, effect in HORSEMEN:
        if n == name:
            return effect
    return ""


def advance_counter(old: int, add: int) -> tuple:
    """
    Add a roll to the central counter.

    A horseman is unleashed every time the counter reaches or passes a
    multiple of 5, so a single roll can trigger more than one activation.
    Returns (new_value, [{"at": multiple, "horseman": name}, ...]).
    """
    new = min(COUNTER_MAX, max(0, old) + max(0, add))
    activations = []
    first = (old // 5 + 1) * 5
    for multiple in range(first, new + 1, 5):
        activations.append({"at": multiple, "horseman": horseman_for(multiple)})
    return new, activations


# --------------------------------------------------------------------------
# Purchases made while standing on a tile
# --------------------------------------------------------------------------

COLLECTABLE_COST = 60
PROMOTION_COST = 120
HOSPITAL_ITEM_COST = 30
BLACK_MARKET_COST = 150
PURCHASE_LIMIT = 5


def validate_purchase(kind: str, position: int, counts: dict, *, no_access=False, doctor_in_play=False):
    """
    Can a player standing on `position` buy one more `kind` this visit?

    `counts` is what they have already bought this turn. Returns
    (True, cost_in_minutes) or (False, reason).
    """
    counts = counts or {}
    bought_collectables = counts.get("collectable", 0) + counts.get("promotion", 0)

    if kind in ("collectable", "promotion"):
        if position not in COLLECTABLE_TILES:
            return False, "You need to be on a Collectables tile to buy collectables."
        # As many collectables as you like (you can buy them for other players);
        # your hand limit is checked when you end your turn.
        if kind == "promotion":
            if counts.get("promotion", 0) >= 1:
                return False, "Only one Promotion card can be bought per visit."
            return True, PROMOTION_COST
        return True, COLLECTABLE_COST

    if kind == "hospital":
        if position not in HOSPITAL_TILES:
            return False, "You need to be at the Hospital to buy hospital items."
        if no_access:
            return False, "You haven't left the Hospital since last turn, so you don't get treatment."
        if counts.get("hospital", 0) >= PURCHASE_LIMIT:
            return False, "Purchase limit of 5 hospital items reached for this visit."
        # A Doctor in the game doubles hospital prices for everyone.
        return True, HOSPITAL_ITEM_COST * (2 if doctor_in_play else 1)

    if kind == "black_market":
        if position != BLACK_MARKET:
            return False, "You need to be on the Black Market to buy from it."
        if counts.get("black_market", 0) >= 1:
            return False, "Only one used collectable per visit to the Black Market."
        return True, BLACK_MARKET_COST

    return False, "Unknown purchase."


# --------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------

def new_turn(user_id) -> dict:
    return {
        "user_id": user_id,
        "rolled": False,
        "paid": False,
        "purchases": {},
        "virus_used": False,
        "target_drawn": False,
        "no_access": False,
    }


def new_state() -> dict:
    return {
        "version": 1,
        # lobby (ready up) -> initiative (roll for the first turn) -> playing
        "phase": "lobby",
        "ready": {},
        "initiative": None,
        "started": False,
        "started_at": None,
        "turn_order": [],
        "turn_index": None,
        "round": 0,
        "positions": {},
        "colors": {},
        "turn": None,
        "last_roll": None,
        "reaper": {"counter": 0, "arrives_at": None, "announced": False},
        "log": [],
        "seq": 0,
    }


def ensure_players(state: dict, user_ids) -> bool:
    """
    Give every player in the room a pawn colour and a position. Players who
    join after the game has started go to the back of the turn order.
    Returns True if anything changed.
    """
    changed = False
    positions = state.setdefault("positions", {})
    colors = state.setdefault("colors", {})
    for uid in user_ids:
        key = str(uid)
        if key not in positions:
            positions[key] = START
            changed = True
        if key not in colors:
            used = set(colors.values())
            free = [c for c in PAWN_COLORS if c not in used]
            colors[key] = free[0] if free else PAWN_COLORS[len(colors) % len(PAWN_COLORS)]
            changed = True
        if state.get("started") and uid not in state.get("turn_order", []):
            state["turn_order"].append(uid)
            changed = True
    return changed


LOG_LIMIT = 60


def add_log(state: dict, text: str, kind: str = "info", user_id=None, announce=False, ts=None) -> dict:
    state["seq"] = state.get("seq", 0) + 1
    entry = {"seq": state["seq"], "text": text, "kind": kind, "user_id": user_id, "announce": announce, "ts": ts}
    log = state.setdefault("log", [])
    log.append(entry)
    del log[:-LOG_LIMIT]
    return entry
