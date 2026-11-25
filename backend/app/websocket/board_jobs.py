"""
Jobs and titles on the board.

Titles (from the rules, v4.24-4.27): you need a Tier 3 job to apply, and you
go up one level at a time, on your turn:
  Manager   - trade in a completed assignment slip
  Senior    - use a Promotion card; no bleeding
  Executive - no bleeding, no heat, and at least one equipped collectable
There are only so many of each title (Manager 6, Senior 4, Executive 2).
An Executive also gets the ability of another, unheld Tier 3 job, chosen
once ("attached to the executive"), and lost with the title.

Tier 3 job abilities: most are used on your turn, once per turn, and play out
in the live card panel (see board_events.ABILITIES). A few are automatic:
the Real Estate Officer's fee, the Charity Commissioner's levy and the
Judge's court cases (board_events.Ctx.judge).
"""
import json

from flask_jwt_extended import jwt_required
from flask_socketio import emit

from app import socketio
from app.models import db, Job
from app import game_versions
from app.websocket import board as B

TITLES = ["Manager", "Senior", "Executive"]
TITLE_QUANTITY = {"Manager": 6, "Senior": 4, "Executive": 2}
TITLE_REQUIREMENTS = {
    "Manager": "Trade in a completed assignment slip.",
    "Senior": "Use a Promotion card, and have no bleeding.",
    "Executive": "No bleeding, no heat, and at least one equipped collectable.",
}
# Abilities that work by themselves (no button)
AUTOMATIC = {
    "Real Estate Officer": "Automatic: anyone who visits the Job Centre, Hospital or Senate pays you 20 minutes.",
    "Judge": "Automatic: court cases come to you to decide.",
    "Charity Commissioner": None,  # the levy is automatic; forgiving heat is used from the button
}
REAL_ESTATE_FEE = 20
CHARITY_LEVY = 20


# --------------------------------------------------------------------------
# Reference data (job abilities, titles) for the clients
# --------------------------------------------------------------------------

_ref_cache = {}


def reference(state) -> dict:
    """Jobs and titles as the game version describes them."""
    key = state.get("game_version")
    v = game_versions.get_version(key)
    if not v:
        return {"jobs": [], "titles": []}
    stamp = (v.id, v.created_at, len(v.cards or ""))
    hit = _ref_cache.get(key)
    if hit and hit[0] == stamp:
        return hit[1]
    ref = (json.loads(v.cards or "{}").get("reference") or {})

    def num(x, default=0):
        try:
            return int(str(x).strip().split()[0])
        except (ValueError, IndexError):
            return default

    jobs = [{"name": j.get("Job"), "faction": j.get("Faction"), "tier": num(j.get("Tier")),
             "pay": num(j.get("Pay (mins per turn)")), "ability": (j.get("Ability") or "").replace("—", "").strip()}
            for j in ref.get("jobs") or [] if j.get("Job")]
    for j in jobs:
        j["automatic"] = AUTOMATIC.get(j["name"])
    titles = [{"name": t.get("Title"), "pay": num(t.get("Pay (mins per turn)")), "quantity": num(t.get("Quantity")),
               "abilities": t.get("Abilities") or "", "requirement": TITLE_REQUIREMENTS.get(t.get("Title"), "")}
              for t in ref.get("titles") or [] if t.get("Title")]
    out = {"jobs": jobs, "titles": titles}
    _ref_cache[key] = (stamp, out)
    return out


# --------------------------------------------------------------------------
# Who holds what
# --------------------------------------------------------------------------

def job_name(rp):
    return rp.job.name if rp and rp.job and rp.job.tier else None


def secondary_of(state, uid):
    return (state.get("secondary_jobs") or {}).get(str(uid))


def abilities_of(state, rp):
    """[(slot, job name)] of the Tier 3 abilities this player has."""
    out = []
    if rp and rp.job and rp.job.tier == 3:
        out.append(("primary", rp.job.name))
    sec = secondary_of(state, rp.userId) if rp else None
    if sec and rp.perk == "Executive":
        out.append(("secondary", sec))
    return out


def holders(room, state, job):
    """Alive players with this Tier 3 job's ability (their job, or their executive ability)."""
    return [p.userId for p in room.participants
            if B._alive(p) and any(name == job for _, name in abilities_of(state, p))]


def tidy_secondary(room, state):
    """An executive ability goes with the Executive title."""
    sec = state.get("secondary_jobs") or {}
    parts = B._participants(room)
    for uid in list(sec):
        rp = parts.get(int(uid))
        if not rp or rp.perk != "Executive":
            sec.pop(uid)


# --------------------------------------------------------------------------
# Titles
# --------------------------------------------------------------------------

def next_title(rp):
    if rp.perk == "Executive":
        return None
    return TITLES[TITLES.index(rp.perk) + 1] if rp.perk in TITLES else "Manager"


def title_problems(room, state, rp):
    """(title, [what's missing]) for the next title up."""
    title = next_title(rp)
    if not title:
        return None, ["You're already an Executive."]
    missing = []
    if not (rp.job and rp.job.tier == 3):
        missing.append("You need a Tier 3 job to apply for a title.")
    uid = str(rp.userId)
    if title == "Manager" and not (state.get("slips") or {}).get(uid):
        missing.append("Complete an assignment slip (it's traded in).")
    if title == "Senior":
        hand = state["hands"].get(uid, [])
        if not any(B.cards_mod.split_entry(e)[0] == "promotion" for e in hand):
            missing.append("You need a Promotion card in your hand.")
    if title in ("Senior", "Executive") and (rp.bleed or 0) > 0:
        missing.append("You must have no bleeding.")
    if title == "Executive":
        if (rp.heat or 0) > 0:
            missing.append("You must have no heat.")
        if not state["equipped"].get(uid):
            missing.append("Equip at least one collectable.")
    held = sum(1 for p in room.participants if p.perk == title and p.userId != rp.userId)
    if held >= TITLE_QUANTITY[title]:
        missing.append(f"All {TITLE_QUANTITY[title]} {title} titles are taken.")
    return title, missing


@socketio.on("boardApplyTitle")
@jwt_required()
def board_apply_title(data=None):
    """On your turn: take the next title up, if you meet its requirements."""
    ctx = B._context()
    if not ctx:
        return
    user_id, rp, room = ctx
    with B._room_locks[room.id]:
        state = B._load(room)
        if not B._require_own_turn(state, user_id):
            return
        title, missing = title_problems(room, state, rp)
        if missing:
            emit("error", {"message": missing[0]})
            return
        uid = str(user_id)
        traded = ""
        if title == "Manager":
            slip = state["slips"][uid].pop(0)
            B.cards_mod.discard(state["decks"], "assignment", slip)
            card = B._pc(state, "assignment", slip)
            traded = f", trading in the slip “{card['title'] if card else 'a slip'}”"
        elif title == "Senior":
            hand = state["hands"][uid]
            entry = next(e for e in hand if B.cards_mod.split_entry(e)[0] == "promotion")
            hand.remove(entry)
            deck, inst = B.cards_mod.split_entry(entry)
            B.cards_mod.discard(state["decks"], deck, inst)
            traded = ", using a Promotion card"
        old = rp.perk
        rp.perk = title
        db.session.commit()
        B._log(state, f"🎖️ {B._name(rp)} is promoted to {title}{traded}" + (f" (was {old})" if old else "") + ".",
               kind="round", user_id=user_id, announce=True)
        B._save(room, state)
    B._emit_room_state(room)
    B._broadcast(room, state)


@socketio.on("boardChooseSecondaryJob")
@jwt_required()
def board_choose_secondary_job(data=None):
    """An Executive chooses the ability of another, unheld Tier 3 job (once; it can't be changed)."""
    ctx = B._context()
    if not ctx:
        return
    user_id, rp, room = ctx
    name = str(B._parse(data).get("job") or "")
    with B._room_locks[room.id]:
        state = B._load(room)
        if rp.perk != "Executive":
            emit("error", {"message": "Only an Executive gets a second job ability."})
            return
        if secondary_of(state, user_id):
            emit("error", {"message": "Your executive ability is already chosen; it can't be changed."})
            return
        job = Job.query.filter_by(name=name, tier=3).first()
        if not job:
            emit("error", {"message": "Choose a Tier 3 job."})
            return
        if rp.job_id == job.id:
            emit("error", {"message": "That's already your job: choose a different one."})
            return
        taken = [p for p in room.participants if p.userId != user_id and B._alive(p)
                 and (p.job_id == job.id or secondary_of(state, p.userId) == name)]
        if taken:
            emit("error", {"message": f"{B._name(taken[0])} already has the {name} ability."})
            return
        state.setdefault("secondary_jobs", {})[str(user_id)] = name
        B._log(state, f"💼 {B._name(rp)} takes the {name} ability as their executive ability.",
               kind="round", user_id=user_id, announce=True)
        B._save(room, state)
    B._broadcast(room, state)


# --------------------------------------------------------------------------
# Abilities
# --------------------------------------------------------------------------

@socketio.on("boardUseAbility")
@jwt_required()
def board_use_ability(data=None):
    """Use your Tier 3 job's ability ({slot: 'primary'}) or your executive ability ({slot: 'secondary'})."""
    ctx = B._context()
    if not ctx:
        return
    user_id, rp, room = ctx
    slot = B._parse(data).get("slot") or "primary"
    with B._room_locks[room.id]:
        state = B._load(room)
        if not B._require_own_turn(state, user_id):
            return
        if not B._alive(rp):
            emit("error", {"message": "Servants of the Reaper have no job abilities."})
            return
        job = dict(abilities_of(state, rp)).get(slot)
        if not job:
            emit("error", {"message": "You don't have that ability." if slot == "primary"
                           else "Choose your executive ability first."})
            return
        if B.board_events.active(state):
            emit("error", {"message": f"Finish “{state['event']['title']}” first."})
            return
        used = state["turn"].setdefault("abilities_used", {})
        if used.get(slot):
            emit("error", {"message": f"You've already used the {job} ability this turn."})
            return
        error = B.board_events.ability_check(room, state, rp, job)
        if error:
            emit("error", {"message": error})
            return
        used[slot] = True
        ability = next((j["ability"] for j in reference(state)["jobs"] if j["name"] == job), "")
        B._log(state, f"⚡ {B._name(rp)} uses the {job} ability.", kind="card", user_id=user_id)
        B.board_events.start_ability(room, state, user_id, job, ability)
        B._save(room, state)
    B._emit_room_state(room)
    B._broadcast(room, state)


def real_estate_fee(room, state, rp, tile):
    """Visiting the Job Centre, Hospital or Senate: the Real Estate Officer demands 20 minutes."""
    if tile.get("building") not in ("job_centre", "hospital", "senate"):
        return
    for uid in holders(room, state, "Real Estate Officer"):
        if uid == rp.userId:
            continue
        officer = B._participants(room)[uid]
        fee = min(REAL_ESTATE_FEE, B._minutes_left(rp))
        if fee <= 0:
            continue
        B._set_minutes(rp, B._minutes_left(rp) - fee)
        B._set_minutes(officer, B._minutes_left(officer) + fee)
        db.session.commit()
        B._log(state, f"🏢 {B._name(rp)} pays the Real Estate Officer {B._name(officer)} {B._fmt(fee)}.",
               kind="money", user_id=rp.userId)


def charity_levy(room, state, rp):
    """With a Charity Commissioner in post, opposition players pay 20 minutes a turn."""
    commissioners = [u for u in holders(room, state, "Charity Commissioner") if u != rp.userId]
    faction = rp.job.type if rp.job and rp.job.tier else None
    if not commissioners or faction == "Public Service":
        return 0
    levy = min(CHARITY_LEVY, B._minutes_left(rp))
    if levy <= 0:
        return 0
    B._set_minutes(rp, B._minutes_left(rp) - levy)
    db.session.commit()
    B._log(state, f"🤝 {B._name(rp)} pays the Charity Commissioner's levy: {B._fmt(levy)}.",
           kind="money", user_id=rp.userId)
    return levy
