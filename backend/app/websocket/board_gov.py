"""
Government on the board, beyond the Senate and oppressions (board.py):

- approvals go back to "approve" whenever the government changes;
- when a change of approval tips the table into a REJECT majority, the player
  who tipped it chooses a new government and everyone votes on it;
- Peasant's Revolt: a peasant sharing a tile with a government leader steals
  1 hour from them and throws a free Throwing Knife (once per leader per turn,
  on anyone's turn).
"""
from flask_jwt_extended import jwt_required
from flask_socketio import emit

from app import socketio
from app.models import db, GovernmentMember
from app.websocket import board as B
from app.websocket import board_cards as cards_mod
from app.websocket import board_rules as rules

# Who a Peasant's Revolt can be aimed at
LEADER_ROLES = {"dictator", "head_of_state", "politburo"}
REVOLT_STEAL = 60
REVOLT_BLEED = 2   # a Throwing Knife: 20 minutes of bleeding


# --------------------------------------------------------------------------
# Approvals
# --------------------------------------------------------------------------

def reset_approvals(room):
    """Everyone approves of a new government."""
    changed = False
    for p in room.participants:
        if p.approval_status != "approve":
            p.approval_status = "approve"
            changed = True
    if changed:
        db.session.commit()
    return changed


def reject_majority(room) -> bool:
    alive = [p for p in room.participants if B._alive(p)]
    rejects = sum(1 for p in alive if p.approval_status == "reject")
    return bool(alive) and rejects * 2 > len(alive)


def approval_changed(room, actor_id, was_majority):
    """
    Call after someone's approval changed (outside the board lock). If that
    tipped the table into a REJECT majority, `actor_id` chooses a new
    government and everyone votes on it.
    """
    if was_majority or not reject_majority(room):
        return
    with B._room_locks[room.id]:
        state = B._load(room)
        if not state.get("started"):
            return
        rp = B._participants(room).get(actor_id)
        B._log(state, f"👎 The majority now rejects the government: {B._name(rp)} calls a vote on a new one.",
               kind="admin", announce=True)
        if B.board_events.active(state):
            # After the card being played
            state["gov_vote_pending"] = actor_id
        else:
            B.board_events.start_government_vote(room, state, actor_id)
        B._save(room, state)
    B._broadcast(room, state)
    B._emit_room_state(room)


# --------------------------------------------------------------------------
# Peasant's Revolt
# --------------------------------------------------------------------------

def _roles(room) -> dict:
    gov = room.government
    if not gov or gov.type == "Democracy":
        return {}
    return {m.user_id: m.role for m in GovernmentMember.query.filter_by(government_id=gov.id).all()}


def revolt_targets(room, state, user_id) -> list:
    """The government leaders this peasant can revolt against right now."""
    roles = _roles(room)
    if not roles or user_id in roles or not state.get("started"):
        return []
    parts = B._participants(room)
    me = parts.get(user_id)
    if not me or not B._alive(me) or me.is_in_jail:
        return []
    pos = state["positions"].get(str(user_id))
    used = _revolts(state)["pairs"]
    out = []
    for uid, role in roles.items():
        leader = parts.get(uid)
        if role not in LEADER_ROLES or not leader or not B._alive(leader) or leader.is_in_jail:
            continue
        if state["positions"].get(str(uid)) != pos or pos is None or pos == rules.JAIL:
            continue
        if f"{user_id}:{uid}" in used:
            continue
        out.append(uid)
    return out


def _revolts(state):
    """This turn's revolts, reset whenever the turn moves on."""
    r = state.get("revolts") or {}
    if r.get("turn_seq") != state.get("turn_seq"):
        r = {"turn_seq": state.get("turn_seq"), "pairs": []}
        state["revolts"] = r
    return r


@socketio.on("boardPeasantRevolt")
@jwt_required()
def board_peasant_revolt(data=None):
    ctx = B._context()
    if not ctx:
        return
    user_id, rp, room = ctx
    target_id = B._int_or_none(B._parse(data).get("target_user_id"))
    with B._room_locks[room.id]:
        state = B._load(room)
        if not B._require_started(state):
            return
        if target_id not in revolt_targets(room, state, user_id):
            emit("error", {"message": "Peasant's Revolt needs you (a peasant) on the same tile as a government "
                                      "leader, once per leader per turn."})
            return
        effects = [{"type": "steal", "who": "choose", "minutes": REVOLT_STEAL},
                   {"type": "bleed", "who": "choose", "amount": REVOLT_BLEED}]
        result = cards_mod.apply_effects(effects, user_id, B._card_players(room), chosen=target_id,
                                         context={"judge": False})
        B._apply_result(room, state, result)
        _revolts(state)["pairs"].append(f"{user_id}:{target_id}")
        target = B._participants(room).get(target_id)
        B._log(state, f"✊ Peasant's Revolt! {B._name(rp)} rises up against {B._name(target)}: steals "
                      f"{B._fmt(REVOLT_STEAL)} and throws a free Throwing Knife (20 minutes of bleeding).",
               kind="card", user_id=user_id, announce=True)
        B._save(room, state)
    B._emit_clock(room, rp)
    if target:
        B._emit_clock(room, target)
    B._emit_room_state(room)
    B._broadcast(room, state)
