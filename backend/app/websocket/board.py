"""
Socket handlers for the board view.

The board is server-authoritative: dice are rolled here, pawns are moved
here, cards are drawn here, and every client renders the `boardState`
payload it is sent. State is kept as JSON on Room.board_state so a server
restart doesn't lose the game.

The rules live in board_rules.py and the card engine in board_cards.py;
neither has database or socket dependencies and both are tested on their own.

Hands of collectables are private: they are stripped from the public payload
and each player is sent their own hand as `boardHand`.
"""
import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock

from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit

from app import socketio
from app.models import db, Room, RoomParticipants, GovernmentMember, Job, serialize_room
from app.websocket import board_rules as rules
from app.websocket import board_cards as cards_mod
from app import game_versions
from app.websocket.sockets import timeFormat, apply_income, _has_job_in_room, _user_room

# One lock per room: every handler is load -> mutate -> save.
_room_locks = defaultdict(Lock)

UNEMPLOYED_JOB_ID = 0
TITLE_DEMOTION = {"Executive": "Senior", "Senior": "Manager", "Manager": None}
DOCTOR_JOB = "Doctor"

DECK_LABEL = {"scenario": "Scenario", "assignment": "Assignment Slip", "collectable": "Collectable",
              "job": "Job Opportunity", "promotion": "Promotion card", "hospital": "Hospital item",
              "shortcut": "Shortcut card", "oppression": "Government Oppression"}
JUDGE_JOB = "Judge"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _now():
    return datetime.utcnow()


def _iso(dt):
    return dt.isoformat() + "Z" if dt else None


def _parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).rstrip("Z"))
    except ValueError:
        return None


def _parse(data):
    if isinstance(data, (str, bytes)):
        try:
            data = json.loads(data)
        except Exception:
            return {}
    return data if isinstance(data, dict) else {}


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _minutes_left(rp) -> int:
    return max(0, int((rp.clock - datetime.min).total_seconds() // 60))


def _alive(rp) -> bool:
    return _minutes_left(rp) > 0


def _set_minutes(rp, minutes: int):
    rp.clock = datetime.min + timedelta(minutes=max(0, int(minutes)))


def _fmt(minutes: int) -> str:
    minutes = abs(int(minutes))
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def _name(rp) -> str:
    return (rp.user.username if rp and rp.user else None) or "Someone"


def _context():
    """(user_id, participant, room) for the caller, or None after emitting an error."""
    user_id = int(get_jwt_identity())
    rp = RoomParticipants.query.filter_by(userId=user_id).first()
    if not rp:
        emit("error", {"message": "You're not in a room."})
        return None
    room = Room.query.get(rp.roomId)
    if not room:
        emit("error", {"message": "Room not found."})
        return None
    return user_id, rp, room


def _is_admin(room, user_id) -> bool:
    # room.id is the creator's user id (see RoomListResource.post)
    return int(room.id) == int(user_id)


def _slug_id(text) -> str:
    import re
    return "job-" + re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def _participants(room) -> dict:
    return {p.userId: p for p in room.participants}


def _cards(state) -> dict:
    """This game's card definitions, from the version the room was created with."""
    return game_versions.get_cards(state.get("game_version"))


def _ensure_card_state(state, room):
    """Pin the room's game version, and give games saved before the decks existed their decks."""
    if not state.get("game_version"):
        state["game_version"] = room.game_version or game_versions.default_key()
    if not isinstance(state.get("decks"), dict):
        state["decks"] = cards_mod.new_decks(_cards(state))
    # Decks added since this game started (job opportunities, promotions, hospital items)
    for d in cards_mod.DECK_NAMES:
        if not isinstance(state["decks"].get(d), dict):
            state["decks"][d] = cards_mod.new_deck(_cards(state).get(d, {}))
    for key in ("hands", "equipped", "slips", "skips", "claims", "discard_picks"):
        if not isinstance(state.get(key), dict):
            state[key] = {}
    if not isinstance(state.get("assignments"), list):
        state["assignments"] = []
    if not isinstance(state.get("oppressions"), list):
        state["oppressions"] = []
    state.setdefault("reveal", None)
    state.setdefault("pending", None)
    # Games saved before the lobby existed
    state.setdefault("phase", "playing" if state.get("started") else "lobby")
    if not isinstance(state.get("ready"), dict):
        state["ready"] = {}


def _load(room) -> dict:
    state = None
    if room.board_state:
        try:
            state = json.loads(room.board_state)
        except Exception:
            state = None
    if not isinstance(state, dict):
        state = rules.new_state()
    rules.ensure_players(state, [p.userId for p in room.participants])
    _ensure_card_state(state, room)
    _check_government(room, state)
    board_jobs.tidy_secondary(room, state)
    return state


def _save(room, state):
    _check_winner(room, state)
    # Note job changes made by this request (a new Tier 3 ability waits a turn)
    board_jobs.track_jobs(state, _participants(room))
    room.board_state = json.dumps(state)
    db.session.commit()


def _check_winner(room, state):
    """The last player standing wins: the game is over (no more turns)."""
    if not state.get("started") or state.get("finished"):
        return
    parts = list(room.participants)
    alive = [p for p in parts if _alive(p)]
    if len(parts) < 2 or len(alive) != 1:
        return
    w = alive[0]
    state["finished"] = {"winner": w.userId, "at": _iso(_now())}
    state["turn"] = None
    if board_events.active(state):
        board_events.cancel(state, "game over")
    _log(state, f"🏆 {_name(w)} is the last player standing and wins the game!", kind="round",
         user_id=w.userId, announce=True)


def _pc(state, deck, instance):
    return cards_mod.public_card(cards_mod.card_of(_cards(state), deck, instance), instance)


def _pc_entry(state, entry):
    """A hand card (which can come from any hand deck), with its hand entry as uid."""
    deck, inst = cards_mod.split_entry(entry)
    card = _pc(state, deck, inst)
    if card:
        card["uid"] = entry
    return card


# Discard piles shown face up to everyone
PUBLIC_DISCARDS = ("collectable", "scenario", "assignment")


def _public_cards(state) -> dict:
    """Everything about the cards that every player may see."""
    decks = {}
    for d in cards_mod.DECK_NAMES:
        pile = state["decks"].get(d) or {"draw": [], "discard": []}
        top = pile["discard"][-1] if pile["discard"] else None
        decks[d] = {
            "draw": len(pile["draw"]),
            "discard": len(pile["discard"]),
            "top": _pc(state, d, top) if top else None,
        }
    return {
        "decks": decks,
        "assignments": [{**a, "card": _pc(state, "assignment", a["card"])} for a in state["assignments"]],
        "equipped": {uid: [c for c in (_pc(state, "collectable", i) for i in lst) if c]
                     for uid, lst in state["equipped"].items()},
        "slips": {uid: [c for c in (_pc(state, "assignment", i) for i in lst) if c]
                  for uid, lst in state["slips"].items()},
        "hand_counts": {uid: len(lst) for uid, lst in state["hands"].items()},
        "oppressions": [{**o, "card": _pc(state, "oppression", o["card"]),
                         "new": o.get("turn_seq") == state.get("turn_seq")} for o in state["oppressions"]],
        "discards": {d: [c for c in (_pc(state, d, i) for i in reversed(state["decks"][d]["discard"])) if c]
                     for d in PUBLIC_DISCARDS},
    }


def _version_name(state):
    v = game_versions.get_version(state.get("game_version"))
    return v.name if v else None


def _payload(state) -> dict:
    reaper = dict(state.get("reaper") or {})
    arrives_at = _parse_iso(reaper.get("arrives_at"))
    counter = reaper.get("counter", 0)
    reaper.update({
        "arrived": bool(arrives_at and _now() >= arrives_at),
        "horseman": rules.horseman_for(counter),
        "effect": rules.horseman_effect(rules.horseman_for(counter) or ""),
    })
    hidden = ("decks", "hands", "equipped", "slips", "assignments", "oppressions", "event_secret")
    return {
        **{k: v for k, v in state.items() if k not in hidden},
        **_public_cards(state),
        "reaper": reaper,
        "tiles": rules.TILES,
        "jail": rules.JAIL,
        "game_version_name": _version_name(state),
        "max_assignments": cards_mod.MAX_ASSIGNMENTS,
        "max_equipped": cards_mod.MAX_EQUIPPED,
        "max_oppressions": cards_mod.MAX_OPPRESSIONS,
        "oppression_cost": cards_mod.OPPRESSION_COST,
        "reference": board_jobs.reference(state),
        "server_now": _iso(_now()),
    }


def _hand_payload(state, user_id) -> dict:
    hand = state["hands"].get(str(user_id), [])
    return {"hand": [c for c in (_pc_entry(state, e) for e in hand) if c]}


def _emit_hands(room, state):
    for p in room.participants:
        socketio.emit("boardHand", _hand_payload(state, p.userId), to=_user_room(p.userId))


def _broadcast(room, state):
    socketio.emit("boardState", _payload(state), to=str(room.id))
    _emit_hands(room, state)


def _log(state, text, kind="info", user_id=None, announce=False):
    return rules.add_log(state, text, kind=kind, user_id=user_id, announce=announce, ts=_iso(_now()))


def _emit_clock(room, rp):
    socketio.emit("userClockUpdate", {
        "user_id": rp.userId,
        "clock": timeFormat(rp.clock),
    }, to=str(room.id))


def _emit_room_state(room):
    socketio.emit("room_state", serialize_room(room), to=str(room.id))


def _next_roll_id(state) -> int:
    state["roll_id"] = state.get("roll_id", 0) + 1
    return state["roll_id"]


def _current_turn_user(state):
    turn = state.get("turn") or {}
    return turn.get("user_id")


def _require_started(state) -> bool:
    if not state.get("started"):
        emit("error", {"message": "The board hasn't started yet."})
        return False
    return True


def _require_own_turn(state, user_id) -> bool:
    if not _require_started(state):
        return False
    if _current_turn_user(state) != user_id:
        emit("error", {"message": "It's not your turn."})
        return False
    return True


def _position(state, user_id):
    return state["positions"].get(str(user_id), rules.START)


def _apply_counter(state, add, names_text):
    """Add to the Reaper's counter and log any horsemen it unleashes."""
    reaper = state.setdefault("reaper", {"counter": 0})
    old = reaper.get("counter", 0)
    new, activations = rules.advance_counter(old, add)
    reaper["counter"] = new
    _log(state, f"{names_text} — the counter is now {new}.", kind="reaper")
    for a in activations:
        _log(
            state,
            f"🐎 {a['horseman']} rides (counter reached {a['at']}): {rules.horseman_effect(a['horseman'])}",
            kind="horseman",
            announce=True,
        )


def _reaper_round_end(state):
    """The Reaper rolls twice after the last player in each round, once it has arrived."""
    reaper = state.setdefault("reaper", {"counter": 0})
    arrives_at = _parse_iso(reaper.get("arrives_at"))
    if not arrives_at or _now() < arrives_at:
        return
    if not reaper.get("announced"):
        reaper["announced"] = True
        _log(state, "☠️ The Reaper has arrived. The 60-minute bleeding cap is lifted for everyone.",
             kind="reaper", announce=True)
    rolls = [random.randint(1, 6), random.randint(1, 6)]
    state["last_roll"] = {"id": _next_roll_id(state), "kind": "reaper", "user_id": None, "values": rolls}
    _apply_counter(state, sum(rolls), f"☠️ The Reaper rolls {rolls[0]} + {rolls[1]}")


def _drop_pending(state):
    """Abandon an unresolved card choice (the card goes to its discard pile)."""
    pending = state.get("pending")
    if pending:
        cards_mod.discard(state["decks"], pending["deck"], pending["card"])
        state["pending"] = None


def _advance_turn(room, state):
    participants = _participants(room)
    ev = state.get("event")
    if ev and ev.get("done"):
        state["event"] = None
    order = state.get("turn_order", [])
    skips = state.setdefault("skips", {})
    _drop_pending(state)
    idx = state.get("turn_index")
    for _ in range(len(order) + 1):
        idx, wrapped = rules.next_turn_index(order, idx, lambda uid: uid in participants)
        if idx is None:
            state["turn"] = None
            state["turn_index"] = None
            return
        if wrapped:
            _reaper_round_end(state)
            state["round"] = state.get("round", 0) + 1
            _log(state, f"Round {state['round']} begins.", kind="round")
        uid = order[idx]
        if skips.get(str(uid), 0) > 0:
            skips[str(uid)] -= 1
            _log(state, f"⏭ {_name(participants.get(uid))} misses this turn.", kind="turn", user_id=uid)
            continue
        break
    state["turn_index"] = idx
    uid = order[idx]
    state["turn"] = rules.new_turn(uid)
    state["turn_seq"] = state.get("turn_seq", 0) + 1
    rp = participants.get(uid)
    suffix = ""
    if rp and not _alive(rp):
        suffix = " (servant of the Reaper)"
    elif rp and rp.is_in_jail:
        suffix = " (in Jail)"
    _log(state, f"▶ {_name(rp)}'s turn{suffix}.", kind="turn", user_id=uid)
    _turn_income(room, state)


def _turn_income(room, state):
    """Income is paid automatically at the very start of a turn (then any RNLI repayment)."""
    turn = state.get("turn") or {}
    uid = turn.get("user_id")
    rp = _participants(room).get(uid)
    if not rp or turn.get("paid"):
        return
    turn["paid"] = True
    if not _alive(rp):
        return
    net, _ = apply_income(rp)
    sign = "+" if net >= 0 else "-"
    _log(state, f"💰 {_name(rp)} received their income: {sign}{_fmt(abs(net))}.", kind="money", user_id=uid)
    repay_debt(state, rp)
    _emit_clock(room, rp)


def _jail(room, state, target) -> str:
    """
    Send a player to the centre Jail tile: heat resets to zero, they lose
    their job and drop one title rank, and it ends their turn.
    """
    target.is_in_jail = True
    target.heat = 0
    lost_job = target.job_id not in (None, UNEMPLOYED_JOB_ID)
    target.job_id = UNEMPLOYED_JOB_ID
    old_title = target.perk
    target.perk = TITLE_DEMOTION.get(old_title) if old_title else None
    db.session.commit()

    state["positions"][str(target.userId)] = rules.JAIL
    consequences = ["heat reset"]
    if lost_job:
        consequences.append("lost their job")
    if old_title:
        consequences.append(f"{old_title} → {target.perk or 'no title'}")
    text = f"🚔 {_name(target)} was sent to Jail ({', '.join(consequences)})."
    _log(state, text, kind="jail", user_id=target.userId, announce=True)

    if _current_turn_user(state) == target.userId:
        _advance_turn(room, state)
    return text


# --------------------------------------------------------------------------
# Cards
# --------------------------------------------------------------------------

def _leader_ids(room) -> set:
    """Government leaders (dictator, politburo, head of state, advisors). None under Democracy."""
    gov = room.government
    if not gov or gov.type == "Democracy":
        return set()
    return {m.user_id for m in GovernmentMember.query.filter_by(government_id=gov.id).all()}


def _card_players(room) -> dict:
    leaders = _leader_ids(room)
    return {
        p.userId: {
            "name": _name(p),
            "minutes": _minutes_left(p),
            "bleed": p.bleed or 0,
            "heat": p.heat or 0,
            "alive": _alive(p),
            "faction": p.job.type if p.job and p.job.tier else None,
            "tier": p.job.tier if p.job else 0,
            "titled": bool(p.perk),
            "leader": p.userId in leaders,
        }
        for p in room.participants
    }


def _card_context(room) -> dict:
    return {"judge": _has_job_in_room(room.id, JUDGE_JOB)}


def _give_cards(state, user_id, count=1, deck="collectable") -> list:
    """Draw cards from a hand deck into a player's (private) hand. Returns the cards drawn."""
    cards = _cards(state)
    hand = state["hands"].setdefault(str(user_id), [])
    drawn = []
    for _ in range(count):
        inst, reshuffled = cards_mod.draw(state["decks"], deck, cards)
        if reshuffled:
            _log(state, f"🔀 The {DECK_LABEL[deck].lower()} discard pile was shuffled back into the deck.", kind="info")
        if not inst:
            break
        entry = cards_mod.hand_entry(deck, inst)
        hand.append(entry)
        drawn.append(_pc_entry(state, entry))
    return drawn


# What landing on a tile deals straight into your hand
LANDING_DEALS = {
    "collectables": ("collectable",),
    "promotion": ("promotion", "job"),   # the first Job Centre tile, "Promotion Card"
    "job_centre": ("job",),
    "hospital": ("hospital",),
    "senate": ("shortcut",),
    "senate_virus": ("shortcut",),
}


def _deal_landing_cards(room, state, rp, tile):
    """Deal the free cards for the tile a player rolled onto. Returns the log text, or None."""
    decks = LANDING_DEALS.get(tile["kind"])
    if not decks:
        return None
    # What the player whose turn it is was dealt, for the turn panel and the action pop-up
    turn = state.get("turn") or {}
    mine = turn.get("user_id") == rp.userId
    if tile.get("building") and turn.get("no_access"):
        if mine:
            turn["dealt_note"] = "No free card: you haven't left this building since your last turn."
        return None
    gov = room.government.type if room.government else None
    if tile["kind"] == "collectables" and gov == "Republic":
        _log(state, f"{_name(rp)} gets no free collectable under the Republic.", kind="info", user_id=rp.userId)
        if mine:
            turn["dealt_note"] = "No free collectable under the Republic."
        return None
    got = []
    for deck in decks:
        if _give_cards(state, rp.userId, 1, deck):
            got.append(DECK_LABEL[deck])
    if mine:
        turn["dealt"] = got
        if not got:
            turn["dealt_note"] = "The deck is empty, so there was nothing to deal."
    if not got:
        return None
    return f"🎴 {_name(rp)} receives a {' and a '.join(g.lower() for g in got)}."


def _apply_result(room, state, result):
    """Persist what a card did (see board_cards.apply_effects)."""
    participants = _participants(room)
    for uid, p in result["players"].items():
        rp = participants.get(uid)
        if not rp:
            continue
        if _minutes_left(rp) != p["minutes"]:
            _set_minutes(rp, p["minutes"])
        rp.bleed = p["bleed"]
        rp.heat = p["heat"]
    db.session.commit()

    for uid, tile in result["moves"].items():
        rp = participants.get(uid)
        if rp and not rp.is_in_jail:
            state["positions"][str(uid)] = tile
    for uid, deck, count in result["draw"]:
        if deck in cards_mod.HAND_DECKS:
            _give_cards(state, uid, count, deck)
    for uid, count in result.get("take_discard", []):
        picks = state.setdefault("discard_picks", {})
        picks[str(uid)] = picks.get(str(uid), 0) + count
    for uid in result["skip"]:
        state["skips"][str(uid)] = state["skips"].get(str(uid), 0) + 1
    for uid in result.get("demote", []):
        rp = participants.get(uid)
        if rp and rp.perk:
            rp.perk = TITLE_DEMOTION.get(rp.perk)
    if result.get("demote"):
        db.session.commit()
    if result.get("fire"):
        for uid in result["fire"]:
            rp = participants.get(uid)
            if rp:
                rp.job_id = UNEMPLOYED_JOB_ID
        db.session.commit()
    for uid in result["jail"]:
        rp = participants.get(uid)
        if rp and not rp.is_in_jail:
            _jail(room, state, rp)


def _reveal(state, deck, instance, user_id, action, *, lines=None, notes=None, rolls=None,
            after_roll=None, target_user_id=None, pending=False):
    """Show a card to the whole table. Clients pop it up when `id` changes."""
    state["reveal_id"] = state.get("reveal_id", 0) + 1
    state["reveal"] = {
        "id": state["reveal_id"],
        "deck": deck,
        "action": action,
        "card": _pc(state, deck, instance),
        "user_id": user_id,
        "target_user_id": target_user_id,
        "lines": lines or [],
        "notes": notes or [],
        "rolls": rolls or [],
        "after_roll": after_roll,
        "pending": pending,
    }


def _efficient(effects, n):
    """Efficiency: knives thrown and healing used are 10 minutes (1 bleed) more effective, per card."""
    out = []
    for e in effects or []:
        if isinstance(e, dict) and e.get("type") == "bleed" and n:
            amount = int(e.get("amount", 0))
            if amount < 0:
                e = {**e, "amount": amount - n}
            elif amount > 0 and e.get("who") not in (None, "self"):
                e = {**e, "amount": amount + n}
        out.append(e)
    return out


def _resolve_card(room, state, deck, instance, actor_id, *, action, chosen=None, after_roll=None,
                  effects_key="effects"):
    """Run a card's effects, reveal it with the outcome, and log it."""
    cards = _cards(state)
    card = cards_mod.card_of(cards, deck, instance)
    participants = _participants(room)
    actor = participants.get(actor_id)
    effects = card.get(effects_key, [])
    context = {**_card_context(room), "charms": board_events.charm_counts(state, room)}
    if action == "played" and deck in ("collectable", "hospital"):
        effects = _efficient(effects, board_events.passive_count(state, actor_id, "efficiency"))
    result = cards_mod.apply_effects(effects, actor_id, _card_players(room), chosen=chosen, context=context)
    _reveal(state, deck, instance, actor_id, action,
            lines=result["lines"], notes=result["notes"], rolls=result["rolls"],
            after_roll=after_roll, target_user_id=chosen)
    verb = {"drawn": "drew", "played": "played", "claimed": "completed", "oppressed": "used"}.get(action, action)
    text = f"🃏 {_name(actor)} {verb} {DECK_LABEL[deck]} “{card['title']}”"
    if result["lines"]:
        text += f": {'; '.join(result['lines'])}"
    _log(state, text + ".", kind="card", user_id=actor_id)
    for note in result["notes"]:
        _log(state, f"✍️ {note}", kind="card", user_id=actor_id)
    _apply_result(room, state, result)
    return result


def _card_move(room, state, rp, *, steps=None, to=None, action=False, why=""):
    """
    Move a pawn with a card: `steps` forward (Shortcut) or straight `to` a tile
    ahead (Advance). With `action`, the tile acts as if landed on: its card is
    dealt (a scenario is drawn once the card in play finishes), Income Tax is
    paid, and its shop / Senate / Time Virus are open for a fresh visit.
    Returns the log text.
    """
    user_id = rp.userId
    previous = _position(state, user_id)
    if steps is not None:
        move = rules.compute_move(previous, steps)
    else:
        start = rules.START if previous == rules.JAIL else previous
        dist = (to - start) % rules.BOARD_SIZE
        path = [(start + i) % rules.BOARD_SIZE for i in range(1, dist + 1)]
        move = {"from": start, "path": path, "to": to, "jumped_from": None, "passed_start": rules.START in path}
    state["positions"][str(user_id)] = move["to"]
    notes = []
    if move["jumped_from"] is not None:
        notes.append("jumped to the Job Centre")
    if move["passed_start"] and rp.heat > 0:
        rp.heat -= 1
        db.session.commit()
        notes.append("passed Start, -1 heat")
    roll_id = _next_roll_id(state)
    # Clients animate the hops (no die): see GameBoard.vue
    state["last_roll"] = {"id": roll_id, "kind": "card_move", "user_id": user_id, "values": [], **move}
    landed = rules.tile_label(move["jumped_from"] if move["jumped_from"] is not None else move["to"])
    text = f"{_name(rp)} {why or 'moves to'} {landed}" + (f" ({'; '.join(notes)})" if notes else "")
    _log(state, f"🏃 {text}.", kind="roll", user_id=user_id)

    turn = state.get("turn") or {}
    if action and turn.get("user_id") == user_id:
        # A new visit: fresh purchases and Senate / Time Virus actions
        turn.update({"no_access": rules.same_building(previous, move["to"]), "purchases": {},
                     "senate_used": False, "virus_used": False, "landed": True, "dealt": [], "dealt_note": None})
        tile = rules.tile(move["to"])
        if tile["kind"] == "scenario":
            ev = state.get("event")
            if ev and not ev.get("done"):
                ev["chain"] = True  # drawn as soon as the card being played finishes
            else:
                _land_scenario(room, state, user_id, roll_id)
        elif tile["kind"] == "assignment":
            _land_assignment(room, state, user_id, roll_id)
        else:
            dealt = _deal_landing_cards(room, state, rp, tile)
            if dealt:
                _log(state, dealt, kind="card", user_id=user_id)
        if tile["kind"] == "collectables" and state.get("income_tax"):
            tax = min(board_events.income_tax_for(rp), _minutes_left(rp))
            _set_minutes(rp, _minutes_left(rp) - tax)
            db.session.commit()
            _log(state, f"💷 {_name(rp)} pays {_fmt(tax)} Income Tax.", kind="money", user_id=user_id)
        if not turn.get("no_access"):
            board_jobs.real_estate_fee(room, state, rp, tile)
    return text


def _land_scenario(room, state, user_id, after_roll):
    """Draw a scenario card: everyone sees it and it plays out (see board_events.py)."""
    cards = _cards(state)
    inst, reshuffled = cards_mod.draw(state["decks"], "scenario", cards)
    if reshuffled:
        _log(state, "🔀 The scenario discard pile was shuffled back into the deck.", kind="info")
    if not inst:
        _log(state, "The scenario deck is empty — draw from the physical deck.", kind="info")
        return None
    card = cards_mod.card_of(cards, "scenario", inst)
    if state.get("turn") is not None:
        # Remember it, so it can be discarded for another (see boardRedrawScenario)
        state["turn"]["scenario"] = inst
    _log(state, f"🃏 {_name(_participants(room).get(user_id))} drew Scenario “{card['title']}”.",
         kind="card", user_id=user_id, announce=True)
    return board_events.start(room, state, inst, user_id, after_roll=after_roll)


def _place_assignment(room, state, instance, drawer_id, target_id, after_roll=None, replaced=None):
    participants = _participants(room)
    card = cards_mod.card_of(_cards(state), "assignment", instance)
    state["assignment_seq"] = state.get("assignment_seq", 0) + 1
    entry = {"id": state["assignment_seq"], "card": instance, "target": target_id, "by": drawer_id,
             "round": state.get("round", 0)}
    if replaced is not None:
        idx = next(i for i, a in enumerate(state["assignments"]) if a["id"] == replaced["id"])
        state["assignments"][idx] = entry
        cards_mod.discard(state["decks"], "assignment", replaced["card"])
    else:
        state["assignments"].append(entry)
    target_name = _name(participants.get(target_id))
    lines = [f"Target: {target_name}"]
    if replaced is not None:
        old = cards_mod.card_of(_cards(state), "assignment", replaced["card"])
        lines.append(f"Replaces “{old['title'] if old else 'an old slip'}”")
    _reveal(state, "assignment", instance, drawer_id, "assignment", lines=lines,
            after_roll=after_roll, target_user_id=target_id)
    _log(state, f"📋 {_name(participants.get(drawer_id))} drew Assignment “{card['title']}” — target: {target_name}.",
         kind="assignment", user_id=drawer_id)


def _land_assignment(room, state, user_id, after_roll):
    cards = _cards(state)
    inst, _ = cards_mod.draw(state["decks"], "assignment", cards)
    if not inst:
        _log(state, "The assignment deck is empty — draw from the physical deck.", kind="info")
        return
    assignments = state["assignments"]
    if len(assignments) >= cards_mod.MAX_ASSIGNMENTS:
        if not cards_mod.replaceable(assignments, user_id):
            cards_mod.discard(state["decks"], "assignment", inst)
            _log(state, "The assignment board is full and every slip targets you, so the new slip is discarded.",
                 kind="assignment", user_id=user_id)
            return
        state["pending"] = {"kind": "replace", "deck": "assignment", "card": inst, "user_id": user_id}
        _reveal(state, "assignment", inst, user_id, "drawn", after_roll=after_roll, pending=True,
                lines=["The assignment board is full: replace a slip (its target stays) or discard this one."])
        _log(state, f"📋 {_name(_participants(room).get(user_id))} drew an assignment, but the board is full.",
             kind="assignment", user_id=user_id)
        return
    alive = [p.userId for p in room.participants if _alive(p)]
    target = cards_mod.black_bag(alive, assignments)
    if target is None:
        cards_mod.discard(state["decks"], "assignment", inst)
        _log(state, "Nobody can be targeted by another assignment; the slip is discarded.", kind="assignment")
        return
    _place_assignment(room, state, inst, user_id, target, after_roll=after_roll)


def _hand_limit(rp) -> int:
    '''5 in hand; +1 with no bleeding effect; +1 for a Senior (matches the room view).'''
    return 5 + (1 if not (rp.bleed or 0) else 0) + (1 if rp.perk == "Senior" else 0)


def _hand_limit_status(state, rp):
    '''(cards counting towards the hand limit, the limit): every card in the hand.'''
    hand = state["hands"].get(str(rp.userId), [])
    held = sum(1 for e in hand if cards_mod.split_entry(e)[0] in cards_mod.HAND_LIMIT_DECKS)
    return held, _hand_limit(rp)


def _take_card(state, user_id, instance):
    """Remove a card from a player's hand or equipped row. Returns where it came from, or None."""
    for zone in ("hands", "equipped"):
        lst = state[zone].get(str(user_id), [])
        if instance in lst:
            lst.remove(instance)
            return zone
    return None


# --------------------------------------------------------------------------
# Hooks used by sockets.py
# --------------------------------------------------------------------------

def emit_board_state(room, to_requester=False):
    """Send the board to whoever just joined (or to the whole room)."""
    with _room_locks[room.id]:
        state = _load(room)
        _save(room, state)
    if to_requester:
        emit("boardState", _payload(state))
        emit("boardHand", _hand_payload(state, int(get_jwt_identity())))
    else:
        _broadcast(room, state)


def jail_fee_discount(room, user_id, fee):
    """Half the jail fee for players sent there by Jury Corruption."""
    if not room or not room.board_state:
        return fee
    try:
        half = json.loads(room.board_state).get("half_jail") or []
    except Exception:
        return fee
    return fee // 2 if user_id in half else fee


def release_from_jail(room_id, user_id, fee_minutes):
    """Paying the jail fee moves your pawn from the Jail to Start."""
    room = Room.query.get(room_id)
    if not room:
        return
    with _room_locks[room.id]:
        state = _load(room)
        state["positions"][str(user_id)] = rules.START
        if user_id in (state.get("half_jail") or []):
            state["half_jail"].remove(user_id)
        rp = _participants(room).get(user_id)
        _log(state, f"🔓 {_name(rp)} paid {_fmt(fee_minutes)} for their freedom and walks to Start.",
             kind="jail", user_id=user_id)
        _save(room, state)
    _broadcast(room, state)


# --------------------------------------------------------------------------
# Handlers: turns
# --------------------------------------------------------------------------

@socketio.on("boardSync")
@jwt_required()
def board_sync(data=None):
    ctx = _context()
    if not ctx:
        return
    _, _, room = ctx
    emit_board_state(room, to_requester=True)


# --------------------------------------------------------------------------
# Starting: lobby (ready up) -> everyone rolls for the first turn -> play
# --------------------------------------------------------------------------

def _fresh_state(room, old):
    """A clean pre-game board, keeping pawn colours and the event counters."""
    state = rules.new_state()
    state["colors"] = old.get("colors", {})
    state["pieces"] = old.get("pieces", {})
    # Keep these counters rising so clients don't mistake a new roll/card for an old one
    state["reveal_id"] = old.get("reveal_id", 0)
    state["roll_id"] = old.get("roll_id", 0)
    state["seq"] = old.get("seq", 0)
    rules.ensure_players(state, [p.userId for p in room.participants])
    _ensure_card_state(state, room)
    return state


def _begin_initiative(room, state):
    """
    Everyone rolls for the first turn, one at a time in a random order. The
    highest roll starts; anyone tied for the highest has a roll battle (again,
    in a random order) until one of them comes out on top.
    """
    players = [p.userId for p in room.participants]
    random.shuffle(players)
    state["phase"] = "initiative"
    state["initiative"] = {"round": 1, "order": players, "contenders": list(players), "current": 0,
                           "rolls": {}, "first_rolls": {}, "history": [], "winner": None, "done": False}
    _log(state, "🎲 Everyone rolls the die in turn: the highest roll takes the first turn.", kind="round",
         announce=True)
    _announce_next_roller(room, state)


def _initiative_current(room, state):
    """Whose turn it is to roll, skipping anyone who has left the room. None once the round is complete."""
    init = state["initiative"]
    participants = _participants(room)
    order = init["order"]
    while init["current"] < len(order) and order[init["current"]] not in participants:
        init["current"] += 1
    return order[init["current"]] if init["current"] < len(order) else None


def _announce_next_roller(room, state):
    uid = _initiative_current(room, state)
    if uid is not None:
        _log(state, f"🎲 {_name(_participants(room).get(uid))}'s turn to roll.", kind="turn", user_id=uid)


def _roll_initiative(state, rp):
    """The current roller's roll (shown to everyone)."""
    init = state["initiative"]
    value = random.randint(1, 6)
    init["rolls"][str(rp.userId)] = value
    if init["round"] == 1:
        init["first_rolls"][str(rp.userId)] = value
    init["current"] += 1
    state["last_roll"] = {"id": _next_roll_id(state), "kind": "initiative", "user_id": rp.userId,
                          "values": [value], "round": init["round"], "at": _iso(_now())}
    battle = f" (roll battle {init['round'] - 1})" if init["round"] > 1 else ""
    _log(state, f"🎲 {_name(rp)} rolled {value}{battle}.", kind="roll", user_id=rp.userId)


def _settle_initiative(room, state):
    """After each roll: next roller, a roll battle for a tie at the top, or the winner starts."""
    init = state["initiative"]
    participants = _participants(room)
    if _initiative_current(room, state) is not None:
        _announce_next_roller(room, state)
        return
    rolled = [u for u in init["order"] if u in participants and str(u) in init["rolls"]]
    if not rolled:
        return
    init["history"].append({"round": init["round"], "order": init["order"], "rolls": dict(init["rolls"])})
    top = max(init["rolls"][str(u)] for u in rolled)
    tied = [u for u in rolled if init["rolls"][str(u)] == top]
    if len(tied) > 1:
        names = " and ".join(_name(participants[u]) for u in tied)
        random.shuffle(tied)
        init.update({"round": init["round"] + 1, "order": tied, "contenders": list(tied), "current": 0, "rolls": {}})
        both = "both" if len(tied) == 2 else "all"
        _log(state, f"⚔️ Roll battle! {names} {both} rolled {top}.", kind="round", announce=True)
        _announce_next_roller(room, state)
        return
    first = tied[0]
    init.update({"winner": first, "winning_roll": top, "done": True})
    first_rolls = init["first_rolls"]
    others = [u for u in participants if u != first]
    random.shuffle(others)  # random among equal rolls; late joiners (no roll) go last
    others.sort(key=lambda u: -first_rolls.get(str(u), 0))
    _begin_job_pick(room, state, [first] + others, first_roll=top)


# --------------------------------------------------------------------------
# Before the first turn: everyone takes a Tier 1 job
# --------------------------------------------------------------------------

def _tier1_jobs():
    return Job.query.filter_by(tier=1).order_by(Job.id).all()


def _begin_job_pick(room, state, order, first_roll=None):
    """The turn order is settled: now everyone chooses a Tier 1 job, then the game starts."""
    participants = _participants(room)
    state["phase"] = "jobs"
    state["job_pick"] = {"order": order, "first_roll": first_roll, "picked": {}}
    winner = participants.get(order[0]) if order else None
    if winner is not None and first_roll is not None:
        _log(state, f"🏁 {_name(winner)} rolled highest ({first_roll}) and will go first.", kind="round", announce=True)
    _log(state, "💼 Everyone chooses a Tier 1 job before the game starts.", kind="round", announce=True)


def _job_pick_waiting(room, state):
    picked = state["job_pick"]["picked"]
    return [u for u in state["job_pick"]["order"] if u in _participants(room) and str(u) not in picked]


def _finish_job_pick(room, state):
    pick = state.pop("job_pick")
    _begin_game(room, state, pick["order"], first_roll=pick["first_roll"], announce_winner=False)


@socketio.on("boardPickJob")
@jwt_required()
def board_pick_job(data=None):
    """
    Choose your starting Tier 1 job: {job_id}. The admin can choose for a player
    ({job_id, user_id}) or deal random Tier 1 jobs to everyone still choosing ({random: true}).
    """
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    payload = _parse(data)
    admin = _is_admin(room, user_id)
    with _room_locks[room.id]:
        state = _load(room)
        if state.get("phase") != "jobs" or not state.get("job_pick"):
            emit("error", {"message": "It's not time to choose a starting job."})
            return
        jobs = {j.id: j for j in _tier1_jobs()}
        participants = _participants(room)
        picked = state["job_pick"]["picked"]

        if payload.get("random"):
            if not admin:
                emit("error", {"message": "Only the room admin can hand out random jobs."})
                return
            choices = [(uid, random.choice(list(jobs.values()))) for uid in _job_pick_waiting(room, state)]
        else:
            target = _int_or_none(payload.get("user_id"))
            target = user_id if target is None else target
            if target != user_id and not admin:
                emit("error", {"message": "Choose your own job."})
                return
            job = jobs.get(_int_or_none(payload.get("job_id")))
            if not job:
                emit("error", {"message": "Choose one of the Tier 1 jobs."})
                return
            if target not in participants:
                emit("error", {"message": "That player isn't in the room."})
                return
            choices = [(target, job)]

        for uid, job in choices:
            p = participants[uid]
            p.job_id = job.id
            picked[str(uid)] = job.id
            by = " (by the admin)" if uid != user_id else ""
            _log(state, f"💼 {_name(p)} takes the job {job.name} ({job.type}){by}.", kind="money", user_id=uid)
        db.session.commit()

        if not _job_pick_waiting(room, state):
            _finish_job_pick(room, state)
        _save(room, state)
    _emit_room_state(room)
    _broadcast(room, state)


def _initiative_roll_for(room, state, uid):
    """Roll for whoever's turn it is, then move the initiative on."""
    _roll_initiative(state, _participants(room)[uid])
    _settle_initiative(room, state)


def _begin_game(room, state, order, first_roll=None, announce_winner=True):
    """Put every pawn on Start, deal the starting hands, start the Reaper's timer, first turn."""
    participants = _participants(room)
    now = _now()
    state.update({
        "phase": "playing",
        "started": True,
        "started_at": _iso(now),
        "turn_order": order,
        "turn_index": 0,
        "round": 1,
        "turn_seq": 1,
        "turn": rules.new_turn(order[0]) if order else None,
    })
    state["reaper"]["arrives_at"] = _iso(now + timedelta(seconds=rules.REAPER_DELAY_SECONDS))
    for uid, rp in participants.items():
        state["positions"][str(uid)] = rules.JAIL if rp.is_in_jail else rules.START
        _give_cards(state, uid, cards_mod.STARTING_HAND)

    if first_roll is not None and order and announce_winner:
        _log(state, f"🏁 {_name(participants[order[0]])} rolled highest ({first_roll}) and goes first.",
             kind="round", announce=True)
    names = " → ".join(_name(participants[uid]) for uid in order)
    _log(state, f"🎲 Turn order: {names}", kind="round")
    _log(state, f"🎴 Everyone is dealt {cards_mod.STARTING_HAND} collectables.", kind="card")
    _log(state, "⏳ The Reaper arrives in 2 hours.", kind="reaper")
    if order:
        _log(state, f"▶ {_name(participants[order[0]])}'s turn.", kind="turn", user_id=order[0])
        _turn_income(room, state)


# Everyone plays a pawn (players choose its colour); see frontend/src/components/board/pieces.js
PIECES = ("pawn",)


@socketio.on("boardSetLook")
@jwt_required()
def board_set_look(data=None):
    """In the waiting lobby: choose your pawn's colour (no two players share one) and piece."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    payload = _parse(data)
    color = payload.get("color")
    piece = payload.get("piece")
    with _room_locks[room.id]:
        state = _load(room)
        if state.get("phase") != "lobby":
            emit("error", {"message": "Pieces are chosen in the waiting lobby, before the game starts."})
            return
        colors = state.setdefault("colors", {})
        pieces = state.setdefault("pieces", {})
        if color is not None:
            if color not in rules.PAWN_COLORS:
                emit("error", {"message": "Choose one of the colours."})
                return
            owner = next((uid for uid, c in colors.items() if c == color and uid != str(user_id)
                          and int(uid) in _participants(room)), None)
            if owner is not None:
                emit("error", {"message": f"{_name(_participants(room).get(int(owner)))} already has {color}."})
                return
            colors[str(user_id)] = color
        if piece is not None:
            if piece not in PIECES:
                emit("error", {"message": "Choose one of the pieces."})
                return
            pieces[str(user_id)] = piece
        _save(room, state)
    _broadcast(room, state)


@socketio.on("boardSetReady")
@jwt_required()
def board_set_ready(data=None):
    """Lobby: say you're ready (or not) to start."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    ready = bool(_parse(data).get("ready", True))
    with _room_locks[room.id]:
        state = _load(room)
        if state.get("phase") != "lobby":
            emit("error", {"message": "The game has already started."})
            return
        state.setdefault("ready", {})[str(user_id)] = ready
        mark = "✅" if ready else "⏸️"
        _log(state, f"{mark} {_name(rp)} is {'ready' if ready else 'not ready'}.", kind="info", user_id=user_id)
        _save(room, state)
    _broadcast(room, state)


@socketio.on("boardStart")
@jwt_required()
def board_start(data=None):
    """
    Admin: start the game. From the lobby this needs everyone to be ready,
    unless `force` is set. Starting (or restarting) moves to the roll for the
    first turn; the board itself is set up once someone has won that roll.
    """
    ctx = _context()
    if not ctx:
        return
    user_id, _, room = ctx
    if not _is_admin(room, user_id):
        emit("error", {"message": "Only the room admin can start the game."})
        return
    force = bool(_parse(data).get("force"))

    with _room_locks[room.id]:
        old = _load(room)
        if old.get("phase") == "lobby" and not force:
            waiting = [p for p in room.participants if not old.get("ready", {}).get(str(p.userId))]
            if waiting:
                names = ", ".join(_name(p) for p in waiting)
                emit("error", {"message": f"Not everyone is ready yet ({names}). Use Force start to begin anyway."})
                return
        state = _fresh_state(room, old)
        if old.get("phase") != "lobby":
            _log(state, "🔀 The admin restarted the game.", kind="admin")
        elif force:
            _log(state, "⏩ The admin force-started the game.", kind="admin")
        _begin_initiative(room, state)
        _save(room, state)
    _broadcast(room, state)


@socketio.on("boardInitiativeRoll")
@jwt_required()
def board_initiative_roll(data=None):
    """Roll for the first turn, when it's your turn to roll."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    with _room_locks[room.id]:
        state = _load(room)
        if state.get("phase") != "initiative":
            emit("error", {"message": "There's no roll for the first turn right now."})
            return
        current = _initiative_current(room, state)
        if current != user_id:
            who = _name(_participants(room).get(current)) if current is not None else "nobody"
            emit("error", {"message": f"It's {who}'s turn to roll."})
            return
        _initiative_roll_for(room, state, user_id)
        _save(room, state)
    _broadcast(room, state)
    if state.get("phase") == "playing":
        _emit_room_state(room)


@socketio.on("boardInitiativeRollCurrent")
@jwt_required()
def board_initiative_roll_current(data=None):
    """Admin: roll for whoever's turn it is to roll (if they're away from their keyboard)."""
    ctx = _context()
    if not ctx:
        return
    user_id, _, room = ctx
    if not _is_admin(room, user_id):
        emit("error", {"message": "Only the room admin can roll for other players."})
        return
    with _room_locks[room.id]:
        state = _load(room)
        if state.get("phase") != "initiative":
            emit("error", {"message": "There's no roll for the first turn right now."})
            return
        current = _initiative_current(room, state)
        if current is None:
            return
        _initiative_roll_for(room, state, current)
        _save(room, state)
    _broadcast(room, state)
    if state.get("phase") == "playing":
        _emit_room_state(room)


@socketio.on("boardInitiativeRollAll")
@jwt_required()
def board_initiative_roll_all(data=None):
    """Admin: roll for everyone still to roll in this round."""
    ctx = _context()
    if not ctx:
        return
    user_id, _, room = ctx
    if not _is_admin(room, user_id):
        emit("error", {"message": "Only the room admin can roll for other players."})
        return
    with _room_locks[room.id]:
        state = _load(room)
        if state.get("phase") != "initiative":
            emit("error", {"message": "There's no roll for the first turn right now."})
            return
        start_round = state["initiative"]["round"]
        while state.get("phase") == "initiative" and state["initiative"]["round"] == start_round:
            current = _initiative_current(room, state)
            if current is None:
                break
            _initiative_roll_for(room, state, current)
        _save(room, state)
    _broadcast(room, state)
    if state.get("phase") == "playing":
        _emit_room_state(room)


@socketio.on("boardRoll")
@jwt_required()
def board_roll(data=None):
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx

    room_changed = False
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_own_turn(state, user_id):
            return
        turn = state["turn"]
        if turn.get("rolled"):
            emit("error", {"message": "You've already rolled this turn."})
            return

        roll = random.randint(1, 6)

        if not _alive(rp):
            # Servants of the Reaper roll into the central counter instead of moving.
            turn["rolled"] = True
            state["last_roll"] = {"id": _next_roll_id(state), "kind": "servant", "user_id": user_id, "values": [roll]}
            _apply_counter(state, roll, f"💀 {_name(rp)} rolls {roll} for the Reaper")
            _save(room, state)
            _broadcast(room, state)
            return

        if rp.is_in_jail:
            emit("error", {"message": "You're in Jail. Pay for your freedom first, then you'll move to Start."})
            return

        previous = _position(state, user_id)
        move = rules.compute_move(previous, roll)
        state["positions"][str(user_id)] = move["to"]

        notes = []
        if move["jumped_from"] is not None:
            notes.append("jumped to the Job Centre")
        if move["passed_start"] and rp.heat > 0:
            rp.heat -= 1
            room_changed = True
            notes.append("passed Start, -1 heat")

        no_access = rules.same_building(previous, move["to"])
        turn.update({"rolled": True, "landed": True, "no_access": no_access, "move_roll": roll})
        roll_id = _next_roll_id(state)
        state["last_roll"] = {"id": roll_id, "kind": "move", "user_id": user_id, "values": [roll], **move}

        landed = rules.tile_label(move["jumped_from"] if move["jumped_from"] is not None else move["to"])
        text = f"🎲 {_name(rp)} rolled {roll} → {landed}"
        if notes:
            text += f" ({'; '.join(notes)})"
        _log(state, text + ".", kind="roll", user_id=user_id)
        if no_access:
            building = rules.tile(move["to"]).get("building", "").replace("_", " ").title()
            _log(state, f"{_name(rp)} hasn't left the {building}, so gets no access this turn.",
                 kind="info", user_id=user_id)

        # The tile you land on deals its card straight away, for everyone to see.
        kind = rules.tile(move["to"])["kind"]
        if kind == "scenario":
            _land_scenario(room, state, user_id, roll_id)
            room_changed = True
        elif kind == "assignment":
            _land_assignment(room, state, user_id, roll_id)
        else:
            dealt = _deal_landing_cards(room, state, rp, rules.tile(move["to"]))
            if dealt:
                _log(state, dealt, kind="card", user_id=user_id)
        if kind == "collectables" and state.get("income_tax"):
            tax = min(board_events.income_tax_for(rp), _minutes_left(rp))
            _set_minutes(rp, _minutes_left(rp) - tax)
            room_changed = True
            _log(state, f"💷 {_name(rp)} pays {_fmt(tax)} Income Tax.", kind="money", user_id=user_id)
        if not no_access:
            board_jobs.real_estate_fee(room, state, rp, rules.tile(move["to"]))
            room_changed = True
        _save(room, state)

    _broadcast(room, state)
    if room_changed:
        _emit_room_state(room)


@socketio.on("boardEndTurn")
@jwt_required()
def board_end_turn(data=None):
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_started(state):
            return
        current = _current_turn_user(state)
        admin = _is_admin(room, user_id)
        if current != user_id and not admin:
            emit("error", {"message": "It's not your turn."})
            return
        pending = state.get("pending")
        if current == user_id and pending and pending.get("user_id") == user_id:
            emit("error", {"message": "Resolve your card first."})
            return
        if board_events.active(state):
            # Even the admin finishes a card on their own turn; ending someone else's turn stops it
            if current == user_id:
                emit("error", {"message": f"Finish the scenario card “{state['event']['title']}” first."})
                return
            board_events.cancel(state, "turn ended")
            _log(state, f"🛠️ The admin stopped “{state['event']['title']}” and ended the turn.", kind="admin")
        debt = state.get("debts", {}).get(str(current))
        if current == user_id:
            held, limit = _hand_limit_status(state, rp)
            if held > limit:
                emit("error", {"message": f"You have {held} cards but can only keep {limit}. "
                                          "Discard or give some away before ending your turn."})
                return
        if current != user_id:
            target = _participants(room).get(current)
            _log(state, f"⏭ The admin ended {_name(target)}'s turn.", kind="admin")
        holder = _participants(room).get(current)
        if debt and holder and debt.get("paid_seq") != state.get("turn_seq") and _alive(holder):
            # Not repaid from income this turn: take it now
            repay_debt(state, holder)
            debt = state.get("debts", {}).get(str(current))
        if debt:
            # RNLI: "at the end of your turn the debt earns interest of 30 minutes"
            debt["minutes"] += 30
            _log(state, f"🛟 30 minutes interest is added to {_name(_participants(room).get(current))}'s "
                        f"{debt['title']} bill ({_fmt(debt['minutes'])}).", kind="money", user_id=current)
        _advance_turn(room, state)
        _save(room, state)
    _broadcast(room, state)


@socketio.on("boardSetTurn")
@jwt_required()
def board_set_turn(data=None):
    """Admin: make it a given player's turn, from the start (to fix or redo a turn)."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    if not _is_admin(room, user_id):
        emit("error", {"message": "Only the room admin can change whose turn it is."})
        return
    target_id = _int_or_none(_parse(data).get("user_id"))
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_started(state):
            return
        target = _participants(room).get(target_id)
        if not target:
            emit("error", {"message": "That player isn't in the room."})
            return
        order = state.setdefault("turn_order", [])
        if target_id not in order:
            order.append(target_id)
        if board_events.active(state):
            board_events.cancel(state, "turn changed")
            _log(state, f"🛠️ The admin stopped “{state['event']['title']}”.", kind="admin")
        if state.get("event", {}) and state["event"].get("done"):
            state["event"] = None
        _drop_pending(state)
        state["turn_index"] = order.index(target_id)
        state["turn"] = rules.new_turn(target_id)
        state["turn_seq"] = state.get("turn_seq", 0) + 1
        _log(state, f"🛠️ The admin made it {_name(target)}'s turn.", kind="admin", announce=True)
        _log(state, f"▶ {_name(target)}'s turn.", kind="turn", user_id=target_id)
        _turn_income(room, state)
        _save(room, state)
    _emit_room_state(room)
    _broadcast(room, state)


@socketio.on("boardCollectIncome")
@jwt_required()
def board_collect_income(data=None):
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_own_turn(state, user_id):
            return
        if state["turn"].get("paid"):
            emit("error", {"message": "You've already collected income this turn."})
            return
        if not _alive(rp):
            emit("error", {"message": "Servants of the Reaper don't earn income."})
            return
        net, _ = apply_income(rp)
        state["turn"]["paid"] = True
        sign = "+" if net >= 0 else "-"
        _log(state, f"💰 {_name(rp)} collected income: {sign}{_fmt(net)}.", kind="money", user_id=user_id)
        repaid = repay_debt(state, rp)
        _save(room, state)
    _emit_clock(room, rp)
    _broadcast(room, state)
    if repaid:
        _emit_room_state(room)


DEBT_PLANS = (60, 120, 180)  # RNLI: "pay between 1-3 hours inclusive per turn"


def repay_debt(state, rp, minutes=None):
    """
    This turn's repayment of a card debt (RNLI): the player's chosen 1-3 hours,
    or what's left. Made when they collect income. Returns the minutes repaid.
    """
    uid = rp.userId
    debt = (state.get("debts") or {}).get(str(uid))
    if not debt or debt.get("paid_seq") == state.get("turn_seq"):
        return 0
    want = minutes if minutes is not None else debt.get("plan") or DEBT_PLANS[0]
    pay = min(want, debt["minutes"], _minutes_left(rp))
    if pay <= 0:
        return 0
    _set_minutes(rp, _minutes_left(rp) - pay)
    db.session.commit()
    debt["minutes"] -= pay
    debt["paid_seq"] = state.get("turn_seq")
    text = f"🛟 {_name(rp)} repaid {_fmt(pay)} of their {debt['title']} bill"
    if debt["minutes"] <= 0:
        state["debts"].pop(str(uid))
        cards_mod.discard(state["decks"], "scenario", debt["card"])
        text += " — paid in full"
    else:
        text += f" ({_fmt(debt['minutes'])} left)"
    _log(state, text + ".", kind="money", user_id=uid)
    return pay


@socketio.on("boardSetDebtPlan")
@jwt_required()
def board_set_debt_plan(data=None):
    """Choose how much of a card debt (RNLI) to repay each turn: 1, 2 or 3 hours."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    minutes = _int_or_none(_parse(data).get("minutes"))
    with _room_locks[room.id]:
        state = _load(room)
        debt = (state.get("debts") or {}).get(str(user_id))
        if not debt:
            emit("error", {"message": "You don't owe anything."})
            return
        if minutes not in DEBT_PLANS:
            emit("error", {"message": "Repay 1, 2 or 3 hours a turn."})
            return
        debt["plan"] = minutes
        _log(state, f"🛟 {_name(rp)} will repay {_fmt(minutes)} a turn off their {debt['title']} bill.",
             kind="money", user_id=user_id)
        _save(room, state)
    _broadcast(room, state)


# The Democracy card: "All purchases are double in price."
DEMOCRACY_PRICE_MULTIPLIER = 2

PURCHASE_NAMES = {
    "collectable": "a collectable",
    "promotion": "a Promotion card",
    "hospital": "a hospital item",
    "black_market": "a used collectable from the Black Market",
}
PURCHASE_PLURALS = {"collectable": "collectables", "hospital": "hospital items"}


@socketio.on("boardPurchase")
@jwt_required()
def board_purchase(data=None):
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    payload = _parse(data)
    kind = payload.get("kind")
    wanted = str(payload.get("card") or "")
    try:
        count = max(1, min(rules.PURCHASE_LIMIT if kind != "collectable" else 50, int(payload.get("count") or 1)))
    except (TypeError, ValueError):
        count = 1
    if kind not in ("collectable", "hospital"):
        count = 1  # promotions and the Black Market are one per visit
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_own_turn(state, user_id):
            return
        turn = state["turn"]
        if not (turn.get("rolled") or turn.get("landed")):
            emit("error", {"message": "Roll first - you buy from the tile you land on."})
            return
        # Check every one of them against the limits, as if bought one at a time
        counts = dict(turn.get("purchases", {}))
        cost = 0
        for n in range(count):
            ok, result = rules.validate_purchase(
                kind,
                _position(state, user_id),
                counts,
                no_access=turn.get("no_access", False),
                doctor_in_play=_has_job_in_room(room.id, DOCTOR_JOB),
            )
            if not ok:
                if n:
                    result = f"You can only buy {n} more this visit."
                emit("error", {"message": result})
                return
            counts[kind] = counts.get(kind, 0) + 1
            cost += result
        gov = room.government.type if room.government else None
        if gov == "Democracy":
            cost *= DEMOCRACY_PRICE_MULTIPLIER
        if _minutes_left(rp) < cost:
            emit("error", {"message": f"Not enough time: that costs {_fmt(cost)}."})
            return
        market = state["decks"]["collectable"]["discard"]
        if kind == "black_market" and not market:
            emit("error", {"message": "The Black Market is empty: nobody has used a collectable yet."})
            return
        if kind == "black_market" and wanted and wanted not in market:
            emit("error", {"message": "That card is no longer on the discard pile."})
            return
        # Each purchase deals its card into your hand
        deal_deck = {"collectable": "collectable", "promotion": "promotion", "hospital": "hospital"}.get(kind)
        if deal_deck:
            left = cards_mod.available(state["decks"], deal_deck)
            if left < count:
                emit("error", {"message": f"The {DECK_LABEL[deal_deck].lower()} deck is empty." if not left
                               else f"Only {left} left in the {DECK_LABEL[deal_deck].lower()} deck."})
                return

        _set_minutes(rp, _minutes_left(rp) - cost)
        purchases = turn.setdefault("purchases", {})
        purchases[kind] = purchases.get(kind, 0) + count
        what = PURCHASE_NAMES[kind] if count == 1 else f"{count} {PURCHASE_PLURALS[kind]}"
        text = f"🛒 {_name(rp)} bought {what} (-{_fmt(cost)})"
        if deal_deck:
            _give_cards(state, user_id, count, deal_deck)
        elif kind == "black_market":
            # Pick any used collectable (or, with no choice given, the most recent)
            inst = wanted if wanted else market[-1]
            market.remove(inst)
            state["hands"].setdefault(str(user_id), []).append(inst)
            card = _pc(state, "collectable", inst)
            if card:
                text += f": “{card['title']}”"
        _log(state, text + ".", kind="money", user_id=user_id)
        _save(room, state)
    _emit_clock(room, rp)
    _broadcast(room, state)


@socketio.on("boardTimeVirus")
@jwt_required()
def board_time_virus(data=None):
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    target_id = _parse(data).get("target_user_id")
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_own_turn(state, user_id):
            return
        turn = state["turn"]
        position = _position(state, user_id)
        if not (turn.get("rolled") or turn.get("landed")) or position not in rules.TIME_VIRUS_TILES:
            emit("error", {"message": "You need to land on a Time Virus tile to release the virus."})
            return
        if turn.get("virus_used"):
            emit("error", {"message": "You've already released the Time Virus this turn."})
            return
        participants = _participants(room)
        target = participants.get(_int_or_none(target_id))
        if not target or not _alive(target):
            emit("error", {"message": "Choose an alive player to infect."})
            return

        roll = random.randint(1, 6)
        lost = min(rules.time_virus_minutes(roll), _minutes_left(target))
        _set_minutes(target, _minutes_left(target) - lost)
        turn["virus_used"] = True
        state["last_roll"] = {
            "id": _next_roll_id(state), "kind": "virus", "user_id": user_id,
            "target_user_id": target.userId, "values": [roll],
        }
        _log(
            state,
            f"🦠 {_name(rp)} released the Time Virus on {_name(target)}: rolled {roll}, -{_fmt(lost)}.",
            kind="attack", user_id=user_id, announce=True,
        )
        _save(room, state)
    _emit_clock(room, target)
    _broadcast(room, state)


@socketio.on("boardGoToJail")
@jwt_required()
def board_go_to_jail(data=None):
    """Players send themselves; the admin can send anyone."""
    ctx = _context()
    if not ctx:
        return
    user_id, _, room = ctx
    requested = _parse(data).get("user_id")
    target_id = _int_or_none(requested) if requested is not None else user_id
    if target_id != user_id and not _is_admin(room, user_id):
        emit("error", {"message": "Only the admin can send someone else to Jail."})
        return

    with _room_locks[room.id]:
        state = _load(room)
        target = _participants(room).get(target_id)
        if not target:
            emit("error", {"message": "That player isn't in this room."})
            return
        if target.is_in_jail:
            emit("error", {"message": f"{_name(target)} is already in Jail."})
            return
        _jail(room, state, target)
        _save(room, state)

    _emit_room_state(room)
    _broadcast(room, state)


@socketio.on("boardMoveToken")
@jwt_required()
def board_move_token(data=None):
    """
    Move a pawn by hand - for shortcuts, scenario cards and corrections.
    Players can move their own pawn on their turn; the admin can move anyone.
    Every manual move is written to the public log.
    """
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    payload = _parse(data)
    admin = _is_admin(room, user_id)
    target_id = _int_or_none(payload.get("user_id", user_id))
    tile_index = _int_or_none(payload.get("tile"))
    if target_id is None or tile_index is None:
        emit("error", {"message": "Invalid move."})
        return
    if not 0 <= tile_index < rules.BOARD_SIZE:
        emit("error", {"message": "Invalid tile."})
        return

    room_state_changed = False
    with _room_locks[room.id]:
        state = _load(room)
        if not admin:
            if target_id != user_id:
                emit("error", {"message": "You can only move your own pawn."})
                return
            if not _require_own_turn(state, user_id):
                return
        participants = _participants(room)
        target = participants.get(target_id)
        if not target:
            emit("error", {"message": "That player isn't in this room."})
            return
        if target.is_in_jail:
            if not admin:
                emit("error", {"message": "You're in Jail. Pay for your freedom first."})
                return
            target.is_in_jail = False
            db.session.commit()
            room_state_changed = True

        state["positions"][str(target_id)] = tile_index
        who = "their" if target_id == user_id else f"{_name(target)}'s"
        _log(state, f"✋ {_name(rp)} moved {who} pawn to {rules.tile_label(tile_index)}.",
             kind="manual", user_id=user_id)
        _save(room, state)

    if room_state_changed:
        _emit_room_state(room)
    _broadcast(room, state)


# --------------------------------------------------------------------------
# Handlers: cards
# --------------------------------------------------------------------------

@socketio.on("boardResolveCard")
@jwt_required()
def board_resolve_card(data=None):
    """
    Finish a card that needed a decision from the player who drew it:
      choose_target - {target_user_id}
      replace       - {replace: assignment id}, or {replace: null} to discard the new slip
    """
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    payload = _parse(data)
    with _room_locks[room.id]:
        state = _load(room)
        pending = state.get("pending")
        if not pending or pending.get("user_id") != user_id:
            emit("error", {"message": "You have no card waiting for a decision."})
            return
        participants = _participants(room)

        if pending["kind"] == "choose_target":
            target_id = _int_or_none(payload.get("target_user_id"))
            target = participants.get(target_id)
            if not target or not _alive(target) or target_id == user_id:
                emit("error", {"message": "Choose another player who is still alive."})
                return
            state["pending"] = None
            _resolve_card(room, state, pending["deck"], pending["card"], user_id,
                          action="drawn", chosen=target_id)
            cards_mod.discard(state["decks"], pending["deck"], pending["card"])

        elif pending["kind"] == "replace":
            replace_id = _int_or_none(payload.get("replace"))
            state["pending"] = None
            if replace_id is None:
                cards_mod.discard(state["decks"], "assignment", pending["card"])
                _log(state, f"📋 {_name(rp)} discarded the new assignment slip.", kind="assignment", user_id=user_id)
            else:
                old = next((a for a in cards_mod.replaceable(state["assignments"], user_id)
                            if a["id"] == replace_id), None)
                if not old:
                    state["pending"] = pending
                    emit("error", {"message": "You can't replace that slip (it may target you)."})
                    return
                _place_assignment(room, state, pending["card"], user_id, old["target"], replaced=old)
        _save(room, state)
    _emit_room_state(room)
    _broadcast(room, state)


@socketio.on("boardDrawScenario")
@jwt_required()
def board_draw_scenario(data=None):
    """
    Draw the top scenario card and play it, from the scenario deck on the board
    (e.g. a card that says "draw a scenario card"). The player whose turn it is
    draws it; the admin can draw one for them.
    """
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_started(state):
            return
        drawer = _current_turn_user(state)
        admin = _is_admin(room, user_id)
        if user_id != drawer and not admin:
            emit("error", {"message": "Only the player whose turn it is can draw a scenario card."})
            return
        if state.get("pending") or board_events.active(state):
            emit("error", {"message": "A card is still being played. Finish it first."})
            return
        who = _name(_participants(room).get(drawer))
        by = "" if user_id == drawer else " (by the admin)"
        _log(state, f"🃏 {who} draws a scenario card from the deck{by}.", kind="card", user_id=drawer)
        _land_scenario(room, state, drawer, None)
        _save(room, state)
    _emit_room_state(room)
    _broadcast(room, state)


@socketio.on("boardRedrawScenario")
@jwt_required()
def board_redraw_scenario(data=None):
    """
    Discard this turn's scenario card and draw another (e.g. "If no Judge is in
    play, discard this scenario card"). The player who drew it, or the admin.
    Effects the first card already applied are not undone.
    """
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_started(state):
            return
        turn = state.get("turn") or {}
        drawer = turn.get("user_id")
        old = turn.get("scenario")
        if not old:
            emit("error", {"message": "No scenario card has been drawn this turn."})
            return
        if user_id != drawer and not _is_admin(room, user_id):
            emit("error", {"message": "Only the player who drew it (or the admin) can discard it."})
            return
        pending = state.get("pending")
        if pending and pending.get("deck") == "scenario" and pending.get("card") == old:
            _drop_pending(state)  # it hadn't been resolved yet: straight to the discard pile
        ev = state.get("event")
        if ev and ev.get("inst") == old:
            board_events.cancel(state, "redrawn")
        card = _pc(state, "scenario", old)
        who = _name(_participants(room).get(drawer))
        by = "" if user_id == drawer else " (by the admin)"
        _log(state, f"🔁 {who} discarded “{card['title'] if card else 'a scenario card'}” and draws another{by}.",
             kind="card", user_id=drawer)
        _land_scenario(room, state, drawer, None)
        _save(room, state)
    _emit_room_state(room)
    _broadcast(room, state)


@socketio.on("boardClaimAssignment")
@jwt_required()
def board_claim_assignment(data=None):
    """Complete an assignment on the board: run its reward and keep the slip."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    payload = _parse(data)
    assignment_id = _int_or_none(payload.get("assignment_id"))
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_started(state):
            return
        a = next((x for x in state["assignments"] if x["id"] == assignment_id), None)
        if not a:
            emit("error", {"message": "That assignment is no longer on the board."})
            return
        if a["target"] == user_id and _int_or_none(payload.get("against")) in (None, user_id):
            emit("error", {"message": "You can't complete an assignment against yourself."})
            return
        if not _alive(rp):
            emit("error", {"message": "Servants of the Reaper can't complete assignments."})
            return
        if state["claims"].get(str(user_id)) == state.get("turn_seq"):
            emit("error", {"message": "You can only complete one assignment per turn."})
            return
        card = cards_mod.card_of(_cards(state), "assignment", a["card"])
        chosen = _int_or_none(payload.get("target_user_id"))
        if card and cards_mod.needs_choice(card["reward"]) and chosen is None:
            emit("error", {"message": "This reward needs a target."})
            return
        # Bounty Board: the next two can be completed against anyone with a title
        bounty = state.get("bounty")
        against = _int_or_none(payload.get("against"))
        target_id = a["target"]
        if against is not None and against != a["target"]:
            victim = _participants(room).get(against)
            if not bounty or not victim or not victim.perk or against == user_id:
                emit("error", {"message": "Only the Bounty Board lets you complete it against someone else "
                                          "(and they must have a title)."})
                return
            target_id = against

        state["assignments"].remove(a)
        state["claims"][str(user_id)] = state.get("turn_seq")
        state["slips"].setdefault(str(user_id), []).append(a["card"])
        if card:
            result = _resolve_card(room, state, "assignment", a["card"], user_id, action="claimed",
                                   chosen=chosen, effects_key="reward")
            lines = list(result["lines"])
            target = _participants(room).get(target_id)
            if bounty:
                # Double reward, and a titled target is demoted
                again = cards_mod.apply_effects(card.get("reward", []), user_id, _card_players(room), chosen=chosen)
                _apply_result(room, state, again)
                lines += [f"{line} (bounty: double)" for line in again["lines"]]
                if target and target.perk:
                    old = target.perk
                    target.perk = TITLE_DEMOTION.get(old)
                    db.session.commit()
                    lines.append(f"{_name(target)} is demoted: {old} → {target.perk or 'no title'}")
                bounty["left"] -= 1
                if bounty["left"] <= 0:
                    state.pop("bounty")
                    cards_mod.discard(state["decks"], "scenario", bounty["card"])
                    _log(state, "📜 Two bounties have been completed: the Bounty Board comes down.", kind="card")
                _log(state, f"🎯 Bounty: {'; '.join(lines)}.", kind="assignment", user_id=user_id)
            state["reveal"]["lines"] = [f"Against {_name(target)}"] + lines
            state["reveal"]["target_user_id"] = target_id
        _save(room, state)
    _emit_room_state(room)
    _broadcast(room, state)


@socketio.on("boardPlayCard")
@jwt_required()
def board_play_card(data=None):
    """Use a card from your hand (or a collectable you have equipped)."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    payload = _parse(data)
    instance = str(payload.get("card") or "")
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_started(state):
            return
        if not _alive(rp):
            emit("error", {"message": "Servants of the Reaper can't use collectables."})
            return
        deck, inst = cards_mod.split_entry(instance)
        card = cards_mod.card_of(_cards(state), deck, inst)
        if not card:
            emit("error", {"message": "Unknown card."})
            return
        if board_events.card_script(card):
            # Advance, Shortcut, Mission Objective, job cards...: played out for everyone to see
            if board_events.active(state):
                emit("error", {"message": f"Finish “{state['event']['title']}” first."})
                return
            error = board_events.card_check(room, state, user_id, card)
            if error:
                emit("error", {"message": error})
                return
            if instance not in state["hands"].get(str(user_id), []) + state["equipped"].get(str(user_id), []):
                emit("error", {"message": "That card isn't in your hand."})
                return
            _log(state, f"🎴 {_name(rp)} plays “{card['title']}”.", kind="card", user_id=user_id)
            # It leaves the hand once its action has happened (board_events.finish)
            board_events.start_card(room, state, deck, inst, user_id, entry=instance)
            _save(room, state)
            _emit_room_state(room)
            _broadcast(room, state)
            return
        chosen = _int_or_none(payload.get("target_user_id"))
        if cards_mod.needs_choice(card["effects"]):
            target = _participants(room).get(chosen)
            if not target or not _alive(target) or chosen == user_id:
                emit("error", {"message": "Choose another player who is still alive."})
                return
        zone = _take_card(state, user_id, instance)
        if not zone:
            emit("error", {"message": "That card isn't in your hand."})
            return
        _resolve_card(room, state, deck, inst, user_id, action="played", chosen=chosen)
        if card.get("reusable"):
            # "Not a one-use item": it stays where it was
            state[zone].setdefault(str(user_id), []).append(instance)
        else:
            cards_mod.discard(state["decks"], deck, inst)
        _save(room, state)
    _emit_room_state(room)
    _broadcast(room, state)


@socketio.on("boardEquipCard")
@jwt_required()
def board_equip_card(data=None):
    """Put a collectable on the table next to your name (max 2)."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    instance = str(_parse(data).get("card") or "")
    with _room_locks[room.id]:
        state = _load(room)
        hand = state["hands"].get(str(user_id), [])
        equipped = state["equipped"].setdefault(str(user_id), [])
        if instance not in hand:
            emit("error", {"message": "That card isn't in your hand."})
            return
        if cards_mod.split_entry(instance)[0] != "collectable":
            emit("error", {"message": "Only collectables can be equipped."})
            return
        if len(equipped) >= cards_mod.MAX_EQUIPPED:
            emit("error", {"message": f"You can only have {cards_mod.MAX_EQUIPPED} collectables equipped."})
            return
        hand.remove(instance)
        equipped.append(instance)
        card = _pc(state, "collectable", instance)
        _log(state, f"🛡️ {_name(rp)} equipped “{card['title'] if card else 'a collectable'}”.",
             kind="card", user_id=user_id)
        _save(room, state)
    _broadcast(room, state)


@socketio.on("boardUnequipCard")
@jwt_required()
def board_unequip_card(data=None):
    """Take an equipped collectable back into your hand."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    instance = str(_parse(data).get("card") or "")
    with _room_locks[room.id]:
        state = _load(room)
        equipped = state["equipped"].get(str(user_id), [])
        if instance not in equipped:
            emit("error", {"message": "That card isn't equipped."})
            return
        equipped.remove(instance)
        state["hands"].setdefault(str(user_id), []).append(instance)
        card = _pc(state, "collectable", instance)
        _log(state, f"🛡️ {_name(rp)} took “{card['title'] if card else 'a collectable'}” back into their hand.",
             kind="card", user_id=user_id)
        _save(room, state)
    _broadcast(room, state)


@socketio.on("boardDiscardCard")
@jwt_required()
def board_discard_card(data=None):
    """Discard a card from your hand or equipped row onto its discard pile (collectables feed the Black Market)."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    instance = str(_parse(data).get("card") or "")
    with _room_locks[room.id]:
        state = _load(room)
        if not _take_card(state, user_id, instance):
            emit("error", {"message": "That card isn't yours."})
            return
        deck, inst = cards_mod.split_entry(instance)
        cards_mod.discard(state["decks"], deck, inst)
        card = _pc(state, deck, inst)
        _log(state, f"🗑️ {_name(rp)} discarded “{card['title'] if card else 'a card'}”.",
             kind="card", user_id=user_id)
        _save(room, state)
    _broadcast(room, state)


@socketio.on("boardGiveCard")
@jwt_required()
def board_give_card(data=None):
    """Trade: hand a card from your hand to another player."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    payload = _parse(data)
    instance = str(payload.get("card") or "")
    to_id = _int_or_none(payload.get("to_user_id"))
    with _room_locks[room.id]:
        state = _load(room)
        target = _participants(room).get(to_id)
        if not target or to_id == user_id:
            emit("error", {"message": "Choose another player to give it to."})
            return
        hand = state["hands"].get(str(user_id), [])
        if instance not in hand:
            emit("error", {"message": "That card isn't in your hand."})
            return
        hand.remove(instance)
        state["hands"].setdefault(str(to_id), []).append(instance)
        _log(state, f"🤝 {_name(rp)} gave a card to {_name(target)}.", kind="card", user_id=user_id)
        _save(room, state)
    _broadcast(room, state)


@socketio.on("boardTakeFromDiscard")
@jwt_required()
def board_take_from_discard(data=None):
    """
    Take a used collectable off the discard pile into a hand. Players need a
    discard pick (from a card such as "take a card from the discard pile");
    the admin can move any card to anyone, for resolving cards by hand.
    """
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    payload = _parse(data)
    instance = str(payload.get("card") or "")
    admin = _is_admin(room, user_id)
    to_id = _int_or_none(payload.get("to_user_id")) or user_id
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_started(state):
            return
        pile = state["decks"]["collectable"]["discard"]
        if instance not in pile:
            emit("error", {"message": "That card is no longer on the discard pile."})
            return
        picks = state.setdefault("discard_picks", {})
        if to_id != user_id and not admin:
            emit("error", {"message": "You can only take a card for yourself."})
            return
        using_pick = picks.get(str(user_id), 0) > 0 and to_id == user_id
        if not using_pick and not admin:
            emit("error", {"message": "You need a card that lets you take from the discard pile."})
            return
        target = _participants(room).get(to_id)
        if not target:
            emit("error", {"message": "That player isn't in this room."})
            return
        pile.remove(instance)
        state["hands"].setdefault(str(to_id), []).append(instance)
        if using_pick:
            picks[str(user_id)] -= 1
        card = _pc(state, "collectable", instance)
        title = card["title"] if card else "a card"
        if to_id == user_id:
            _log(state, f"♻️ {_name(rp)} took “{title}” from the discard pile.", kind="card", user_id=user_id)
        else:
            _log(state, f"♻️ The admin gave “{title}” from the discard pile to {_name(target)}.", kind="admin")
        _save(room, state)
    _broadcast(room, state)


# --------------------------------------------------------------------------
# Handlers: admin
# --------------------------------------------------------------------------

@socketio.on("boardShuffleDeck")
@jwt_required()
def board_shuffle_deck(data=None):
    """Admin: shuffle a deck, putting its discard pile back in first."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    deck = _parse(data).get("deck")
    admin = _is_admin(room, user_id)
    if not admin and deck not in ("scenario", "collectable"):
        emit("error", {"message": "Only the room admin can shuffle the decks."})
        return
    decks = list(cards_mod.DECK_NAMES) if deck == "all" else [deck]
    if not all(d in cards_mod.DECK_NAMES for d in decks):
        emit("error", {"message": "Unknown deck."})
        return
    with _room_locks[room.id]:
        state = _load(room)
        if not admin and (not state.get("started") or _current_turn_user(state) != user_id):
            emit("error", {"message": "You can shuffle this deck on your turn."})
            return
        sizes = [f"{DECK_LABEL[d]}s ({cards_mod.shuffle_deck(state['decks'], d)})" for d in decks]
        what = "every deck" if deck == "all" else sizes[0]
        who = "The admin" if admin else _name(rp)
        _log(state, f"🔀 {who} shuffled {what}, with the discards back in.",
             kind="admin" if admin else "card", announce=True)
        _save(room, state)
    _broadcast(room, state)


WHEEL_SPIN_MS = 5000


def wheel_spin_for(entries, rng=random, weights=None):
    """
    Pick a winner and the wheel rotation that lands the pointer on them.
    Slice i covers [start_i, start_i + size_i) clockwise from the top (sizes in
    proportion to `weights`, equal by default); rotating the wheel by R degrees
    puts the slice holding angle (360 - R % 360) % 360 under the pointer.
    Returns (landed slice index, rotation).
    """
    n = len(entries)
    weights = weights or [1] * n
    total = float(sum(weights))
    sizes = [360 * w / total for w in weights]
    # The pointer lands on a slice in proportion to its size, like a real wheel
    pick = rng.uniform(0, 360)
    start = 0.0
    landed = n - 1
    for i, size in enumerate(sizes):
        if pick < start + size:
            landed = i
            break
        start += size
    start = sum(sizes[:landed])
    landing = start + sizes[landed] * rng.uniform(0.15, 0.85)
    rotation = rng.randint(5, 7) * 360 + (360 - landing)
    return landed, round(rotation, 3)


def chaos_wheel(entries, rng=random):
    """
    With a Chaos Creator in the game the wheel is wild: slices are random sizes,
    and wherever it lands, the real winner is drawn separately.
    Returns (weights, landed index, winner index, rotation).
    """
    weights = [round(rng.uniform(0.25, 3.0), 3) for _ in entries]
    landed, rotation = wheel_spin_for(entries, rng, weights)
    return weights, landed, rng.randrange(len(entries)), rotation


@socketio.on("roomWheelSpin")
@jwt_required()
def room_wheel_spin(data=None):
    """
    Admin: spin the room's wheel. The server picks the result and sends the
    spin to everyone, so every screen shows the same wheel landing on the
    same player.
    """
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    if not _is_admin(room, user_id):
        emit("error", {"message": "Only the room admin can spin the wheel."})
        return
    players = [p for p in room.participants if _alive(p)] or list(room.participants)
    if not players:
        emit("error", {"message": "Nobody to spin for."})
        return
    entries = [{"user_id": p.userId, "username": _name(p)} for p in players]

    with _room_locks[room.id]:
        state = _load(room)
        state["wheel_id"] = state.get("wheel_id", 0) + 1
        spin_id = state["wheel_id"]
        chaos = bool(board_jobs.holders(room, state, "Chaos Creator"))
        _save(room, state)

    if chaos:
        weights, landed, winner, rotation = chaos_wheel(entries)
    else:
        weights = None
        landed, rotation = wheel_spin_for(entries)
        winner = landed

    socketio.emit("roomWheelSpin", {
        "id": spin_id,
        "entries": entries,
        "winner_index": winner,
        # Where the pointer stops (with a Chaos Creator in the game, not necessarily the winner)
        "landed_index": landed,
        "weights": weights,
        "chaos": chaos,
        "rotation": rotation,
        "duration_ms": WHEEL_SPIN_MS,
        "by": _name(rp),
    }, to=str(room.id))

    # Written to the board log once the wheel has stopped, so it doesn't spoil the spin
    def log_result():
        with app_ref.app_context():
            r = Room.query.get(room.id)
            if not r:
                return
            with _room_locks[r.id]:
                st = _load(r)
                if chaos and landed != winner:
                    _log(st, f"🌀 Chaos! The wheel landed on {entries[landed]['username']}, but the real winner is "
                             f"{entries[winner]['username']}.", kind="admin", announce=True)
                else:
                    _log(st, f"🎡 The wheel picked {entries[winner]['username']}.", kind="admin", announce=True)
                _save(r, st)
            _broadcast(r, st)
    app_ref = _current_app()
    socketio.start_background_task(_after, WHEEL_SPIN_MS / 1000 + 0.3, log_result)


def _current_app():
    from flask import current_app
    return current_app._get_current_object()


def _after(seconds, fn):
    socketio.sleep(seconds)
    fn()


@socketio.on("boardSummonReaper")
@jwt_required()
def board_summon_reaper(data=None):
    """Admin: start the Reaper now instead of waiting out the 2-hour timer."""
    ctx = _context()
    if not ctx:
        return
    user_id, _, room = ctx
    if not _is_admin(room, user_id):
        emit("error", {"message": "Only the room admin can summon the Reaper."})
        return
    with _room_locks[room.id]:
        state = _load(room)
        state.setdefault("reaper", {"counter": 0})["arrives_at"] = _iso(_now())
        _log(state, "☠️ The admin summoned the Reaper early. It rolls at the end of this round.",
             kind="reaper", announce=True)
        _save(room, state)
    _broadcast(room, state)


@socketio.on("boardReset")
@jwt_required()
def board_reset(data=None):
    """Admin: put the board back to its pre-game state (clocks are untouched)."""
    ctx = _context()
    if not ctx:
        return
    user_id, _, room = ctx
    if not _is_admin(room, user_id):
        emit("error", {"message": "Only the room admin can reset the board."})
        return
    with _room_locks[room.id]:
        old = _load(room)
        state = _fresh_state(room, old)
        _log(state, "The admin reset the board. Back to the lobby: everyone ready up again.", kind="admin")
        _save(room, state)
    _broadcast(room, state)


# --------------------------------------------------------------------------
# Government oppressions
# --------------------------------------------------------------------------
# Any player can introduce one at the Senate (2 hours, a Senate action), up to
# four in play. Government leaders use them on their turn against a player of
# their choice: Politburo 2 each, Dictator 3, Head of State 1 per state enemy
# (state enemies only). Each card works once per turn, and not on the turn it
# was introduced. No oppressions under Democracy; a change of government
# removes them all.

def _government_type(room):
    return room.government.type if room.government else "Democracy"


def _clear_oppressions(state, reason):
    """Discard every oppression in play."""
    if not state.get("oppressions"):
        return False
    for o in state["oppressions"]:
        cards_mod.discard(state["decks"], "oppression", o["card"])
    state["oppressions"] = []
    _log(state, f"⚖️ {reason}: all government oppressions are removed.", kind="admin", announce=True)
    return True


def _check_government(room, state):
    """Oppressions belong to the government that was in power when they were introduced."""
    gov = _government_type(room)
    if state.get("oppressions") and state.get("oppression_gov") not in (None, gov):
        _clear_oppressions(state, f"The government changed to {gov}")
    state["oppression_gov"] = gov


def government_changed(room):
    """Called by sockets.py whenever the government changes."""
    room = Room.query.get(room.id)
    # A new government starts with everyone's approval
    board_gov.reset_approvals(room)
    with _room_locks[room.id]:
        state = _load(room)
        _save(room, state)
    _broadcast(room, state)
    _emit_room_state(room)


def _oppression_uses(state):
    """This turn's oppression use, reset whenever the turn moves on."""
    uses = state.get("oppression_uses") or {}
    if uses.get("turn_seq") != state.get("turn_seq"):
        uses = {"turn_seq": state.get("turn_seq"), "by": {}, "cards": [], "pairs": []}
        state["oppression_uses"] = uses
    return uses


SENATE_VOTE_COST = 60  # changing another player's approval at the Senate (a Senate fee: never doubled)


def _in_government(room, user_id) -> bool:
    gov = room.government
    if not gov:
        return False
    return GovernmentMember.query.filter_by(government_id=gov.id, user_id=user_id).first() is not None


def _remote_surcharge(state, user_id):
    """The Chancellor's remote Senate access costs 30 minutes more (not when actually at the Senate)."""
    turn = state.get("turn") or {}
    at_senate = rules.tile(_position(state, user_id))["kind"] in ("senate", "senate_virus")
    return int(turn.get("remote_surcharge") or 0) if turn.get("remote_senate") and not at_senate else 0


def _senate_ready(state, user_id):
    """An error message, or None if the player may take their Senate action now."""
    turn = state["turn"]
    remote = bool(turn.get("remote_senate"))  # Remote Access
    if not remote and (not (turn.get("rolled") or turn.get("landed")) or
                       rules.tile(_position(state, user_id))["kind"] not in ("senate", "senate_virus")):
        return "Land on a Senate tile first."
    if turn.get("no_access") and not remote:
        return "You haven't left the Senate, so you can't use it this turn."
    if turn.get("senate_used"):
        return "You've already taken your Senate action this turn."
    return None


@socketio.on("boardSenateVote")
@jwt_required()
def board_senate_vote(data=None):
    """At the Senate: pay 1 hour to change another player's approval (your Senate action)."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    payload = _parse(data)
    target_id = _int_or_none(payload.get("target_user_id"))
    status = payload.get("status")
    was_majority = board_gov.reject_majority(room)
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_own_turn(state, user_id):
            return
        error = _senate_ready(state, user_id)
        if error:
            emit("error", {"message": error})
            return
        target = _participants(room).get(target_id)
        if not target or target_id == user_id or not _alive(target):
            emit("error", {"message": "Choose another player who is still alive."})
            return
        if status not in ("approve", "reject"):
            emit("error", {"message": "Choose approve or reject."})
            return
        if target.approval_status == status:
            emit("error", {"message": f"{_name(target)} already {'approves' if status == 'approve' else 'rejects'}."})
            return
        cost = SENATE_VOTE_COST + _remote_surcharge(state, user_id)
        if _minutes_left(rp) < cost:
            emit("error", {"message": f"Not enough time: that costs {_fmt(cost)}."})
            return
        _set_minutes(rp, _minutes_left(rp) - cost)
        target.approval_status = status
        db.session.commit()
        state["turn"]["senate_used"] = True
        verdict = "✓ approve" if status == "approve" else "✗ reject"
        _log(state, f"🏛️ {_name(rp)} paid {_fmt(cost)} at the Senate to change {_name(target)}'s vote to "
                    f"{verdict}.", kind="money", user_id=user_id, announce=True)
        _save(room, state)
    socketio.emit("approvalStatusUpdated", {"user_id": target_id, "username": _name(target), "status": status},
                  to=str(room.id))
    _emit_clock(room, rp)
    _emit_room_state(room)
    _broadcast(room, state)
    # Tipping the table into a REJECT majority calls a vote on a new government
    board_gov.approval_changed(room, user_id, was_majority)


@socketio.on("boardIntroduceOppression")
@jwt_required()
def board_introduce_oppression(data=None):
    """At the Senate: pay 2 hours to put the top oppression card into play."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_own_turn(state, user_id):
            return
        turn = state["turn"]
        gov = _government_type(room)
        position = _position(state, user_id)
        remote = bool(turn.get("remote_senate"))  # Remote Access
        if not remote and (not (turn.get("rolled") or turn.get("landed")) or
                           rules.tile(position)["kind"] not in ("senate", "senate_virus")):
            emit("error", {"message": "Land on a Senate tile to introduce an oppression."})
            return
        if turn.get("no_access") and not remote:
            emit("error", {"message": "You haven't left the Senate, so you can't use it this turn."})
            return
        if gov not in cards_mod.OPPRESSION_USES:
            emit("error", {"message": f"No government oppressions can be introduced under {gov}."})
            return
        if turn.get("senate_used"):
            emit("error", {"message": "You've already taken your Senate action this turn."})
            return
        if not _in_government(room, user_id):
            emit("error", {"message": f"Only members of the {gov} government can introduce an oppression."})
            return
        if len(state["oppressions"]) >= cards_mod.MAX_OPPRESSIONS:
            emit("error", {"message": f"There are already {cards_mod.MAX_OPPRESSIONS} oppressions in play."})
            return
        cost = cards_mod.OPPRESSION_COST + _remote_surcharge(state, user_id)  # Senate costs aren't purchases
        if _minutes_left(rp) < cost:
            emit("error", {"message": f"Not enough time: that costs {_fmt(cost)}."})
            return
        inst, reshuffled = cards_mod.draw(state["decks"], "oppression", _cards(state))
        if not inst:
            emit("error", {"message": "The oppression deck is empty."})
            return
        _set_minutes(rp, _minutes_left(rp) - cost)
        state["oppression_seq"] = state.get("oppression_seq", 0) + 1
        state["oppressions"].append({"id": state["oppression_seq"], "card": inst, "by": user_id,
                                     "turn_seq": state.get("turn_seq")})
        state["oppression_gov"] = gov
        turn["senate_used"] = True
        card = _pc(state, "oppression", inst)
        _reveal(state, "oppression", inst, user_id, "introduced",
                lines=[f"{_name(rp)} paid {_fmt(cost)}", "Leaders can use it from next turn"])
        _log(state, f"⛓️ {_name(rp)} introduced a government oppression: “{card['title']}” (-{_fmt(cost)}).",
             kind="attack", user_id=user_id)
        _save(room, state)
    _emit_clock(room, rp)
    _broadcast(room, state)


@socketio.on("boardUseOppression")
@jwt_required()
def board_use_oppression(data=None):
    """A government leader uses an oppression in play on a player of their choice."""
    ctx = _context()
    if not ctx:
        return
    user_id, rp, room = ctx
    payload = _parse(data)
    oppression_id = _int_or_none(payload.get("oppression_id"))
    target_id = _int_or_none(payload.get("target_user_id"))
    with _room_locks[room.id]:
        state = _load(room)
        if not _require_own_turn(state, user_id):
            return
        gov = _government_type(room)
        limit = cards_mod.OPPRESSION_USES.get(gov)
        roles = cards_mod.OPPRESSION_LEADER_ROLES.get(gov, set())
        member = GovernmentMember.query.filter_by(government_id=room.government.id, user_id=user_id).first() \
            if room.government else None
        if not limit or not member or member.role not in roles:
            emit("error", {"message": "Only government leaders can use oppressions."})
            return
        o = next((x for x in state["oppressions"] if x["id"] == oppression_id), None)
        if not o:
            emit("error", {"message": "That oppression is no longer in play."})
            return
        if o.get("turn_seq") == state.get("turn_seq"):
            emit("error", {"message": "An oppression can't be used on the turn it was introduced."})
            return
        target = _participants(room).get(target_id)
        if not target or not _alive(target) or target_id == user_id:
            emit("error", {"message": "Choose another player who is still alive."})
            return
        uses = _oppression_uses(state)
        if o["id"] in uses["cards"]:
            emit("error", {"message": "That oppression has already been used this turn."})
            return
        if gov == "Republic":
            from app.websocket.sockets import republic_prev_enemies
            if target_id not in republic_prev_enemies.get(room.id, set()):
                emit("error", {"message": "Under the Republic, oppressions can only be used on enemies of the state."})
                return
            if [user_id, target_id] in uses["pairs"]:
                emit("error", {"message": "You've already oppressed that enemy of the state this turn."})
                return
        elif uses["by"].get(str(user_id), 0) >= limit:
            emit("error", {"message": f"You can use {limit} oppressions a turn under {gov}."})
            return

        uses["cards"].append(o["id"])
        uses["pairs"].append([user_id, target_id])
        uses["by"][str(user_id)] = uses["by"].get(str(user_id), 0) + 1
        _resolve_card(room, state, "oppression", o["card"], user_id, action="oppressed", chosen=target_id)
        _save(room, state)
    _emit_room_state(room)
    _broadcast(room, state)


@socketio.on("boardRemoveOppression")
@jwt_required()
def board_remove_oppression(data=None):
    """Admin: remove an oppression from play (e.g. the Chief Justice card)."""
    ctx = _context()
    if not ctx:
        return
    user_id, _, room = ctx
    if not _is_admin(room, user_id):
        emit("error", {"message": "Only the room admin can remove an oppression."})
        return
    oppression_id = _int_or_none(_parse(data).get("oppression_id"))
    with _room_locks[room.id]:
        state = _load(room)
        o = next((x for x in state["oppressions"] if x["id"] == oppression_id), None)
        if not o:
            emit("error", {"message": "That oppression is no longer in play."})
            return
        state["oppressions"].remove(o)
        cards_mod.discard(state["decks"], "oppression", o["card"])
        card = _pc(state, "oppression", o["card"])
        _log(state, f"⚖️ The admin removed the oppression “{card['title'] if card else '?'}”.", kind="admin")
        _save(room, state)
    _broadcast(room, state)


# Scenario cards as live events (imports this module, so it comes last)
from app.websocket import board_events  # noqa: E402
from app.websocket import board_jobs  # noqa: E402
from app.websocket import board_gov  # noqa: E402
