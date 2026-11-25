"""
Scenario cards as live, table-wide events.

When a scenario card is drawn, everyone sees it and it plays out step by
step: players roll their own dice, make their own choices, the Judge decides
court cases, everyone votes, and so on. The state of the card in progress is
`state["event"]` (sent to every client):

    {"id", "card" (public card), "inst", "drawer", "title", "queue": [step, ...],
     "prompt": the question waiting for an answer (or None), "lines": [result, ...],
     "roll": the last die rolled, "vars": per-card memory, "done", "keep", "chain"}

The queue holds JSON steps - {"fn": name, "args": {...}} - so a card in
progress survives a server restart. A step may add more steps (they run
next, in the order added) or ask a question (`_ask`); the answer calls the
prompt's `on` step with it. Card-specific scripts live in SCRIPTS, keyed by
the card's title slug; any other card runs its `effects` through the generic
interpreter, which turns rolls into dice each player rolls themselves.

Equipped collectables work here too: each Charm lowers a roll's target by 1
(or adds 1, where a card says "each charm adds 1"), each Hell Bent adds an
extra die in a War, and a title adds 1 to the die against War.
"""
import random
import re
from datetime import datetime

from flask_jwt_extended import jwt_required
from flask_socketio import emit

from app import socketio
from app.models import db, GovernmentMember, Job
from app.websocket import board as B

rules = B.rules
cards_mod = B.cards_mod

STEPS = {}
SCRIPTS = {}
# Hand cards that play out live (collectables, job opportunities, promotions, shortcuts)
CARD_SCRIPTS = {}
CARD_CHECKS = {}

GOVERNMENTS = ("Democracy", "Communism", "Dictatorship", "Republic")
# Named buildings, by the first tile you reach (Curfew: "move to the next named building tile")
BUILDING_TILES = (4, 9, 14, 19)
COURT_NEED = 5


def step(fn):
    STEPS[fn.__name__] = fn
    return fn


def script(*slugs):
    def wrap(fn):
        for s in slugs:
            SCRIPTS[s] = fn
        return fn
    return wrap


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(title or "").lower()).strip("-")


# --------------------------------------------------------------------------
# Equipped collectables that are always working
# --------------------------------------------------------------------------

PASSIVES = {"charm": "charm", "hell-bent": "hell_bent", "efficiency": "efficiency"}


def passive_of(card) -> str:
    if not card:
        return None
    return card.get("passive") or PASSIVES.get(slug(card.get("title")))


def passive_count(state, user_id, passive) -> int:
    """How many of this always-on collectable a player has equipped (they stack)."""
    cards = B._cards(state)
    return sum(1 for inst in state.get("equipped", {}).get(str(user_id), [])
               if passive_of(cards_mod.card_of(cards, "collectable", inst)) == passive)


def charm_counts(state, room) -> dict:
    return {p.userId: passive_count(state, p.userId, "charm") for p in room.participants}


# --------------------------------------------------------------------------
# The context a step runs in
# --------------------------------------------------------------------------

class Ctx:
    def __init__(self, room, state):
        self.room = room
        self.state = state
        self.ins = 0
        self.room_changed = False

    @property
    def ev(self):
        return self.state.get("event")

    # --- the queue ----------------------------------------------------------
    def push(self, fn, **args):
        """Run `fn` next (after anything else this step has already pushed)."""
        self.ev["queue"].insert(self.ins, {"fn": fn, "args": args})
        self.ins += 1

    def push_spec(self, spec):
        if spec:
            self.push(spec["fn"], **spec.get("args", {}))

    def ask(self, kind, user_id, on, args=None, skip_if=None, **ui):
        """Queue a question for a player; the answer runs step `on` with `answer=...`."""
        self.push("_ask", prompt={"kind": kind, "user_id": user_id, "on": {"fn": on, "args": args or {}},
                                  "skip_if": skip_if, **ui})

    def roll(self, user_id, label, on, args=None, need=None, charm="need", leader_need=None, skip_if=None):
        """
        Queue a die roll for a player. `charm`: "need" - each equipped Charm lowers
        the target by 1; "bonus" - each adds 1 to the roll; None - charms don't count.
        """
        war = bool(self.ev.get("war"))
        if leader_need is not None and self.player(user_id).get("leader"):
            need = leader_need
        charms = passive_count(self.state, user_id, "charm") if charm else 0
        extra = passive_count(self.state, user_id, "hell_bent") if war else 0
        target = None if need is None else max(1, int(need) - (charms if charm == "need" else 0))
        hint = []
        if need is not None:
            hint.append(f"needs {target}+")
            if charm == "need" and charms:
                hint.append(f"{charms} charm{'s' if charms > 1 else ''}: −{charms}")
        if charm == "bonus" and charms:
            hint.append(f"+{charms} from charm{'s' if charms > 1 else ''}")
        if extra:
            hint.append(f"+{extra} di{'ce' if extra > 1 else 'e'} (Hell Bent)")
        self.ask("roll", user_id, "_rolled", skip_if=skip_if, label=label, hint=" · ".join(hint),
                 args={"on": on, "args": args or {}, "need": target, "bonus": charms if charm == "bonus" else 0,
                       "dice": 1 + extra, "war": war, "label": label})

    def court(self, user_id, label, win, lose, a="Rule in their favour", b="Rule against them"):
        """A court case: the Judge decides when one is in play, otherwise roll 5+ (charms help)."""
        judge = self.judge()
        if judge is not None:
            self.ask("choice", judge, "_court_judged", args={"win": win, "lose": lose, "uid": user_id},
                     question=f"⚖️ Judge: decide {self.name(user_id)}'s case ({label})",
                     options=[{"key": "a", "label": f"A) {a}"}, {"key": "b", "label": f"B) {b}"}])
        else:
            self.roll(user_id, f"{label}: court case", "_court_rolled", args={"win": win, "lose": lose},
                      need=COURT_NEED)

    # --- results ------------------------------------------------------------
    def line(self, text, tone=""):
        self.ev["lines"].append({"text": text, "tone": tone})
        B._log(self.state, f"🃏 {text}", kind="card")

    def fx(self, effects, actor, chosen=None, quiet=False):
        """Apply plain card effects (time, bleed, heat, jail, fire, draw...) right away."""
        result = cards_mod.apply_effects(effects, actor, B._card_players(self.room), chosen=chosen,
                                         context={"judge": False, "charms": charm_counts(self.state, self.room)})
        if not quiet:
            for text in result["lines"]:
                self.line(text, tone_of(text))
        for note in result["notes"]:
            self.line(f"✍️ {note}", "note")
        B._apply_result(self.room, self.state, result)
        self.room_changed = True
        return result

    def time(self, uid, minutes):
        return self.fx([{"type": "time", "who": "self", "minutes": int(minutes)}], uid)

    # --- facts --------------------------------------------------------------
    def participants(self):
        return B._participants(self.room)

    def player(self, uid):
        return B._card_players(self.room).get(uid, {})

    def name(self, uid):
        return B._name(self.participants().get(uid))

    def order(self, alive=True, include_jailed=True):
        """Players in turn order, starting with whoever drew the card."""
        order = list(self.state.get("turn_order") or [])
        parts = self.participants()
        order += [u for u in parts if u not in order]
        drawer = self.ev["drawer"]
        if drawer in order:
            i = order.index(drawer)
            order = order[i:] + order[:i]
        out = []
        for u in order:
            rp = parts.get(u)
            if not rp:
                continue
            if alive and not B._alive(rp):
                continue
            if not include_jailed and rp.is_in_jail:
                continue
            out.append(u)
        return out

    def judge(self):
        judges = B.board_jobs.holders(self.room, self.state, B.JUDGE_JOB)
        return next((u for u in self.order() if u in judges), None)

    def leaders(self):
        return [u for u in self.order() if self.player(u).get("leader")]

    def options_for(self, uids):
        parts = self.participants()
        return [{"key": str(u), "label": B._name(parts.get(u))} for u in uids]

    def government(self):
        return B._government_type(self.room)


def tone_of(text):
    if re.search(r"\s\+\d|took |receives|wins|success|walks free|clean", text):
        return "good"
    if re.search(r"\s−\d|Jail|loses|failed|arrested|guilty", text):
        return "bad"
    return ""


# --------------------------------------------------------------------------
# Starting, running and finishing an event
# --------------------------------------------------------------------------

def start(room, state, inst, drawer, after_roll=None):
    """A scenario card was drawn: everyone sees it and it plays out."""
    cards = B._cards(state)
    card = cards_mod.card_of(cards, "scenario", inst)
    state["event_seq"] = state.get("event_seq", 0) + 1
    state.pop("event_secret", None)
    state["event"] = {
        "id": state["event_seq"],
        "deck": "scenario",
        "inst": inst,
        "card": B._pc(state, "scenario", inst),
        "title": card["title"],
        "drawer": drawer,
        "queue": [],
        "prompt": None,
        "lines": [],
        "roll": None,
        "vars": {},
        "done": False,
        "keep": False,
        "chain": False,
        "war": (card.get("kind") or "").lower() == "war" or "war" in slug(card["title"]).split("-"),
        "started_at": B._iso(B._now()),
        # Clients wait for the pawn to finish moving before showing it
        "after_roll": after_roll,
    }
    ctx = Ctx(room, state)
    fn = SCRIPTS.get(card.get("script") or "") or SCRIPTS.get(slug(card["title"]))
    if fn:
        fn(ctx, card)
    else:
        ctx.push("effects", effects=card.get("effects") or [], actor=drawer)
    return run(room, state, ctx)


def run(room, state, ctx=None):
    """Work through the queue until a question needs answering (or the card is done)."""
    ctx = ctx or Ctx(room, state)
    for _ in range(500):
        ev = state.get("event")
        if not ev or ev["done"] or ev["prompt"]:
            break
        if not ev["queue"]:
            # A scenario that did nothing at all can't be used right now: discard it
            if not ev["lines"] and not ev.get("played") and not ev["vars"].get("unusable"):
                cannot_play(ctx, "Nobody at the table is affected by this card right now.")
                continue
            break
        task = ev["queue"].pop(0)
        ctx.ins = 0
        STEPS[task["fn"]](ctx, **task.get("args", {}))
    ev = state.get("event")
    if ev and not ev["done"] and not ev["prompt"] and not ev["queue"]:
        finish(room, state, ctx)
    return ctx


def cannot_play(ctx, reason):
    """The card can't be used as things stand: say why, and wait for it to be discarded."""
    ev = ctx.ev
    ev["vars"]["unusable"] = True
    ev["queue"] = []
    ctx.ins = 0
    ctx.line(f"🚫 {reason}")
    ctx.ask("choice", ev["drawer"], "discard_unusable", args={"uid": ev["drawer"]}, unusable=True,
            question=f"“{ev['title']}” can't be used right now. Discard it (no new card is drawn).",
            options=[{"key": "discard", "label": "🗑️ Discard this card"}])


@step
def discard_unusable(ctx, answer, uid):
    ctx.line(f"🗑️ {ctx.name(uid)} discards “{ctx.ev['title']}”.")


def finish(room, state, ctx):
    ev = state["event"]
    ev["done"] = True
    ev["finished_at"] = B._iso(B._now())
    used = True
    if ev.get("entry"):
        # A card played from a hand only leaves it now that its action has happened
        used = bool(B._take_card(state, ev["drawer"], ev["entry"]))
    if used and not ev["keep"]:
        cards_mod.discard(state["decks"], ev.get("deck", "scenario"), ev["inst"])
    if ev.get("chain"):
        # e.g. Gerry's Slot Machine "draw scenario card", or a Shortcut onto a Scenario tile
        ev["chain"] = False
        B._log(state, f"🃏 {ctx.name(ev['drawer'])} draws a scenario card.", kind="card")
        B._land_scenario(room, state, ev["drawer"], None)
    elif state.get("gov_vote_pending") is not None:
        # The table rejected the government while this card was in play
        start_government_vote(room, state, state.pop("gov_vote_pending"))


def start_government_vote(room, state, uid):
    """The majority rejects the government: `uid` (who tipped it) proposes a new one, then everyone votes."""
    state.pop("gov_vote_pending", None)
    state["event_seq"] = state.get("event_seq", 0) + 1
    state.pop("event_secret", None)
    text = ("The majority of the table rejects the government. The player whose vote tipped it chooses a "
            "new government, then everyone votes on it.")
    state["event"] = {
        "id": state["event_seq"], "deck": "government", "inst": None,
        "card": {"uid": None, "id": "no-confidence", "deck": "government", "title": "The table rejects the government",
                 "text": text, "equip": False, "example": False, "needs_target": False, "notes": []},
        "title": "The table rejects the government", "drawer": uid, "queue": [], "prompt": None, "lines": [],
        "roll": None, "vars": {}, "done": False, "keep": True, "chain": False, "war": False,
        "started_at": B._iso(B._now()), "after_roll": None, "played": False,
    }
    ctx = Ctx(room, state)
    current = ctx.government()
    ctx.ask("choice", uid, "token_gov", args={"uid": uid},
            question="👎 The majority rejects the government. Propose a new one for everyone to vote on:",
            options=[{"key": g, "label": g} for g in GOVERNMENTS if g != current])
    return run(room, state, ctx)


def cancel(state, reason):
    """Stop a card part-way (redraw, admin): nothing more happens."""
    ev = state.get("event")
    if not ev or ev["done"]:
        return False
    ev["queue"] = []
    ev["prompt"] = None
    ev["done"] = True
    ev["cancelled"] = reason
    if ev.get("entry"):
        # A played card that didn't happen stays in its player's hand
        ev["returned"] = True
        ev["lines"].append({"text": f"↩️ “{ev['title']}” wasn't used: it goes back into the hand it was played from.",
                            "tone": ""})
        return True
    if not ev["keep"]:
        cards_mod.discard(state["decks"], ev.get("deck", "scenario"), ev["inst"])
    return True


def active(state) -> bool:
    ev = state.get("event")
    return bool(ev and not ev["done"])


def public(state):
    """The event for every client (anonymous votes stay on the server)."""
    return state.get("event")


# --------------------------------------------------------------------------
# Built-in steps
# --------------------------------------------------------------------------

@step
def _ask(ctx, prompt):
    skip = prompt.pop("skip_if", None)
    if skip and ctx.ev["vars"].get(skip):
        return
    ctx.state["prompt_seq"] = ctx.state.get("prompt_seq", 0) + 1
    prompt["id"] = ctx.state["prompt_seq"]
    if prompt["kind"] == "vote":
        prompt["voted"] = []
        ctx.state["event_secret"] = {"votes": {}}
    ctx.ev["prompt"] = prompt


@step
def _rolled(ctx, answer, on, args, need, bonus, dice, war, label):
    uid = ctx.ev["vars"].get("_answering")
    values = [random.randint(1, 6) for _ in range(max(1, int(dice)))]
    extra = int(bonus or 0)
    if war and ctx.player(uid).get("titled"):
        extra += 1  # titles: +1 to the die against War
    total = sum(values) + extra
    ok = None if need is None else total >= need
    ctx.state["roll_seq"] = ctx.state.get("roll_seq", 0) + 1
    ctx.ev["roll"] = {"id": ctx.state["roll_seq"], "user_id": uid, "values": values, "bonus": extra,
                      "total": total, "need": need, "ok": ok, "label": label}
    shown = " + ".join(map(str, values)) + (f" + {extra}" if extra else "")
    shown += f" = {total}" if (extra or len(values) > 1) else ""
    verdict = "" if ok is None else (" — success" if ok else " — failed")
    ctx.line(f"🎲 {label}: {ctx.name(uid)} rolled {shown}{verdict}", "" if ok is None else ("good" if ok else "bad"))
    r = {"values": values, "total": total, "ok": ok, "need": need, "uid": uid}
    ctx.push(on, r=r, **args)


@step
def _court_rolled(ctx, r, win, lose):
    ctx.push_spec(win if r["ok"] else lose)


@step
def _court_judged(ctx, answer, win, lose, uid):
    won = answer == "a"
    ctx.line(f"⚖️ The Judge rules {'in favour of' if won else 'against'} {ctx.name(uid)}.", "good" if won else "bad")
    ctx.push_spec(win if won else lose)


@step
def say(ctx, text, tone=""):
    ctx.line(text, tone)


@step
def apply(ctx, effects, actor, chosen=None):
    ctx.fx(effects, actor, chosen)


def spec(fn, **args):
    return {"fn": fn, "args": args}


def fx_spec(actor, *effects):
    return spec("apply", effects=list(effects), actor=actor)


# --------------------------------------------------------------------------
# The generic interpreter: a card's effects, with rolls made by the players
# --------------------------------------------------------------------------

ROLLS = ("roll_check", "roll_table", "roll_until")


@step
def effects(ctx, effects, actor, chosen=None):
    batch = []
    for i, e in enumerate(effects or []):
        if not isinstance(e, dict):
            continue
        needs_pick = e.get("who") == "choose" and chosen is None and e.get("type") not in ROLLS
        if e.get("type") in ROLLS or needs_pick:
            if batch:
                ctx.fx(batch, actor, chosen)
                batch = []
            rest = effects[i + 1:]
            if needs_pick:
                others = [u for u in ctx.order() if u != actor]
                ctx.ask("pick", actor, "effects_chosen", args={"effects": effects[i:], "actor": actor},
                        question="Choose a player", options=ctx.options_for(others), min=1, max=1)
                return
            players = B._card_players(ctx.room)
            targets = cards_mod.resolve_who(e.get("who", "self"), actor, players, chosen)
            for u in [u for u in ctx.order() if u in targets]:
                ctx.push("generic_roll", effect=e, uid=u, chosen=chosen)
            if rest:
                ctx.push("effects", effects=rest, actor=actor, chosen=chosen)
            return
        batch.append(e)
    if batch:
        ctx.fx(batch, actor, chosen)


@step
def effects_chosen(ctx, answer, effects, actor):
    ctx.push("effects", effects=effects, actor=actor, chosen=int(answer[0]))


@step
def generic_roll(ctx, effect, uid, chosen=None):
    kind = effect["type"]
    label = effect.get("label") or ctx.ev["title"]
    if kind == "roll_check":
        win = spec("effects", effects=effect.get("success") or [], actor=uid, chosen=chosen)
        lose = spec("effects", effects=effect.get("failure") or [], actor=uid, chosen=chosen)
        if effect.get("court"):
            ctx.court(uid, label, spec("generic_won", uid=uid, then=win), spec("generic_lost", uid=uid, then=lose))
        else:
            ctx.roll(uid, label, "generic_check", args={"win": win, "lose": lose},
                     need=int(effect.get("threshold", 5)), leader_need=effect.get("leader_threshold"),
                     charm=None if effect.get("no_charm") else "need")
    elif kind == "roll_table":
        ctx.roll(uid, label, "generic_table", args={"effect": effect, "uid": uid},
                 charm="bonus" if effect.get("charm") == "bonus" else None)
    elif kind == "roll_until":
        ctx.roll(uid, f"{label}: roll until a {effect.get('face', 6)}", "generic_until",
                 args={"effect": effect, "uid": uid, "misses": 0}, charm=None)


@step
def generic_won(ctx, uid, then):
    ctx.line(f"{ctx.name(uid)} wins the case.", "good")
    ctx.push_spec(then)


@step
def generic_lost(ctx, uid, then):
    ctx.line(f"{ctx.name(uid)} loses the case.", "bad")
    ctx.push_spec(then)


@step
def generic_check(ctx, r, win, lose):
    ctx.push_spec(win if r["ok"] else lose)


def table_outcome(outcomes, value):
    keys = [k for k in outcomes if str(k).isdigit()]
    top = max((int(k) for k in keys), default=6)
    value = min(value, top)
    match = next((k for k in outcomes if cards_mod._face_matches(k, value)), None)
    return outcomes.get(match if match is not None else "else") or []


@step
def generic_table(ctx, r, effect, uid):
    ctx.push("effects", effects=table_outcome(effect.get("outcomes") or {}, r["total"]), actor=uid)


@step
def generic_until(ctx, r, effect, uid, misses):
    face = int(effect.get("face", 6))
    per = int(effect.get("per_roll", 0))
    if r["values"][0] == face:
        paid = misses * per
        ctx.line(f"{ctx.name(uid)} rolled a {face} after {misses + 1} roll{'s' if misses else ''}"
                 f"{f': {B._fmt(paid)} in all' if paid else ' — nothing to pay'}.", "good" if not paid else "bad")
        return
    if per:
        ctx.fx([{"type": "time", "who": "self", "minutes": per}], uid, quiet=True)
    ctx.roll(uid, f"{effect.get('label') or ctx.ev['title']}: roll until a {face}", "generic_until",
             args={"effect": effect, "uid": uid, "misses": misses + 1}, charm=None)


def plain_effects(card):
    """A card's effects without its notes (a script replaces the notes)."""
    return [e for e in card.get("effects") or [] if isinstance(e, dict) and e.get("type") != "note"]


# --------------------------------------------------------------------------
# Scenario cards (Gerry's Game v4.27)
# --------------------------------------------------------------------------

# --- Freedom of Information ----------------------------------------------------
@script("freedom-of-information")
def s_foi(ctx, card):
    for u in ctx.order():
        ctx.ask("choice", u, "foi_answer", args={"uid": u},
                question=f"{ctx.name(u)}: reveal your time, or refuse and take it to court?",
                options=[{"key": "reveal", "label": "Reveal my time"},
                         {"key": "court", "label": "Refuse: go to court"}])


def _reveal_time(ctx, uid, extra=""):
    ctx.line(f"🔎 {ctx.name(uid)} reveals their time: {B._fmt(ctx.player(uid)['minutes'])}{extra}.")


@step
def foi_answer(ctx, answer, uid):
    if answer == "reveal":
        _reveal_time(ctx, uid)
        return
    ctx.line(f"{ctx.name(uid)} refuses the subpoena and goes to court.")
    ctx.court(uid, "Freedom of Information", spec("say", text=f"{ctx.name(uid)} wins: their time stays secret.", tone="good"),
              spec("foi_lost", uid=uid), a="They keep their time secret", b="They must reveal it (+2 heat)")


@step
def foi_lost(ctx, uid):
    ctx.ask("choice", uid, "foi_final", args={"uid": uid},
            question=f"{ctx.name(uid)}: you lost in court. Reveal your time (+2 heat), or keep refusing and be arrested?",
            options=[{"key": "reveal", "label": "Reveal (+2 heat)"}, {"key": "refuse", "label": "Keep refusing (arrested)"}])


@step
def foi_final(ctx, answer, uid):
    if answer == "reveal":
        _reveal_time(ctx, uid)
        ctx.fx([{"type": "heat", "who": "self", "amount": 2}], uid)
    else:
        ctx.line(f"{ctx.name(uid)} keeps refusing and is arrested.", "bad")
        ctx.fx([{"type": "jail", "who": "self"}], uid)


# --- Christmas Crackers --------------------------------------------------------
CRACKER_ITEMS = [("collectable", "Collectable"), ("promotion", "Promotion"), ("job", "Job Opportunity"),
                 ("hospital", "Hospital Item"), ("shortcut", "Shortcut")]


@script("christmas-crackers")
def s_crackers(ctx, card):
    for u in ctx.order():
        ctx.ask("choice", u, "cracker_pick", args={"uid": u},
                question=f"🎄 {ctx.name(u)}: pick your Christmas cracker prize",
                options=[{"key": d, "label": label} for d, label in CRACKER_ITEMS])


@step
def cracker_pick(ctx, answer, uid):
    label = dict(CRACKER_ITEMS).get(answer, answer)
    if B._give_cards(ctx.state, uid, 1, answer):
        ctx.line(f"🎁 {ctx.name(uid)} receives a {label}.", "good")
    else:
        ctx.line(f"The {label.lower()} deck is empty: {ctx.name(uid)} gets nothing.")


# --- Experimental Drug ---------------------------------------------------------
DRUG_TABLE = {1: 2, 2: 0, 3: -2, 4: -4, 5: -6, 6: -cards_mod.BLEED_MAX}


@script("experimental-drug")
def s_drug(ctx, card):
    d = ctx.ev["drawer"]
    ctx.roll(d, "Experimental Drug", "drug_rolled", args={"uid": d}, charm="bonus")
    others = [u for u in ctx.order() if u != d]
    if others:
        ctx.ask("pick", d, "drug_offer", question="Offer the drug to other players? They must roll too.",
                options=ctx.options_for(others), min=0, max=len(others))


@step
def drug_rolled(ctx, r, uid):
    amount = DRUG_TABLE[min(6, r["total"])]
    if amount < 0 and not ctx.player(uid).get("bleed"):
        ctx.line(f"{ctx.name(uid)} isn't bleeding, so it does nothing.")
    elif amount:
        ctx.fx([{"type": "bleed", "who": "self", "amount": amount}], uid)
    else:
        ctx.line(f"{ctx.name(uid)}: no effect.")


@step
def drug_offer(ctx, answer):
    for key in answer:
        u = int(key)
        ctx.roll(u, "Experimental Drug", "drug_rolled", args={"uid": u}, charm="bonus")


# --- Judge cards -----------------------------------------------------------------
def _no_judge(ctx):
    cannot_play(ctx, "No Judge is in play, so this card can't be used.")


def _contraband_of(ctx, uid):
    cards = B._cards(ctx.state)
    found = []
    for zone in ("hands", "equipped"):
        for entry in list(ctx.state[zone].get(str(uid), [])):
            deck, inst = cards_mod.split_entry(entry)
            card = cards_mod.card_of(cards, deck, inst)
            if card and card.get("contraband"):
                found.append((zone, entry, deck, inst, card["title"]))
    return found


@script("contraband")
def s_contraband(ctx, card):
    judge = ctx.judge()
    if judge is None:
        return _no_judge(ctx)
    others = [u for u in ctx.order() if u != judge]
    ctx.ask("pick", judge, "contraband_search", args={"judge": judge},
            question="⚖️ Judge: which players should be searched for contraband?",
            options=ctx.options_for(others), min=0, max=len(others))


@step
def contraband_search(ctx, answer, judge):
    if not answer:
        ctx.line("The Judge searches nobody.")
    for key in answer:
        u = int(key)
        found = _contraband_of(ctx, u)
        if not found:
            ctx.line(f"🔍 {ctx.name(u)} is clean.", "good")
            continue
        for zone, entry, deck, inst, _ in found:
            ctx.state[zone][str(u)].remove(entry)
            cards_mod.discard(ctx.state["decks"], deck, inst)
        ctx.line(f"🔍 {ctx.name(u)} had contraband ({', '.join(f[4] for f in found)}): all discarded.", "bad")
        ctx.fx([{"type": "steal", "who": "choose", "minutes": 120}], judge, chosen=u)
        ctx.fx([{"type": "heat", "who": "self", "amount": 1}], u)


@script("chief-justice")
def s_chief_justice(ctx, card):
    judge = ctx.judge()
    if judge is None:
        return _no_judge(ctx)
    if ctx.government() == "Democracy":
        cannot_play(ctx, "Chief Justice has no effect under Democracy.")
        return
    peasants = [u for u in ctx.order() if not ctx.player(u).get("leader")]
    ctx.ask("pick", judge, "cj_compensate", args={"judge": judge},
            question="⚖️ Judge: which peasants should be compensated 1 hour (paid by the government leaders)?",
            options=ctx.options_for(peasants), min=0, max=len(peasants))
    ctx.push("cj_oppressions", judge=judge)


@step
def cj_compensate(ctx, answer, judge):
    picked = [int(k) for k in answer]
    leaders = ctx.leaders()
    if not picked:
        ctx.line("The Judge awards no compensation.")
        return
    if not leaders:
        ctx.line("There are no government leaders to pay compensation.")
        return
    total = 60 * len(picked)
    share = -(-total // len(leaders))  # rounded up
    ctx.line(f"⚖️ The Judge awards 1 hour each to {', '.join(ctx.name(u) for u in picked)}, "
             f"paid by {', '.join(ctx.name(u) for u in leaders)}.")
    for u in picked:
        ctx.time(u, 60)
    for u in leaders:
        ctx.time(u, -share)


@step
def cj_oppressions(ctx, judge):
    opps = ctx.state.get("oppressions") or []
    if not opps:
        return
    options = [{"key": str(o["id"]), "label": (B._pc(ctx.state, "oppression", o["card"]) or {}).get("title", "Oppression")}
               for o in opps]
    ctx.ask("pick", judge, "cj_remove", question="⚖️ Judge: remove up to 4 government oppressions",
            options=options, min=0, max=min(4, len(options)))


@step
def cj_remove(ctx, answer):
    for key in answer:
        o = next((x for x in ctx.state["oppressions"] if str(x["id"]) == key), None)
        if o:
            ctx.state["oppressions"].remove(o)
            cards_mod.discard(ctx.state["decks"], "oppression", o["card"])
            title = (B._pc(ctx.state, "oppression", o["card"]) or {}).get("title", "an oppression")
            ctx.line(f"⚖️ The Judge removes “{title}”.", "good")


@script("jury-corruption")
def s_jury(ctx, card):
    judge = ctx.judge()
    if judge is None:
        return _no_judge(ctx)
    others = [u for u in ctx.order() if u != judge]
    ctx.ask("pick", judge, "jury_picked", args={"judge": judge},
            question="⚖️ Judge: which players should be considered? You roll 5+ for each to send them to Jail (half the fee to leave).",
            options=ctx.options_for(others), min=0, max=len(others))


@step
def jury_picked(ctx, answer, judge):
    if not answer:
        ctx.line("The Judge picks nobody.")
    for key in answer:
        u = int(key)
        ctx.roll(judge, f"Jury Corruption ({ctx.name(u)})", "jury_rolled", args={"uid": u}, need=5)


@step
def jury_rolled(ctx, r, uid):
    if r["ok"]:
        half = ctx.state.setdefault("half_jail", [])
        if uid not in half:
            half.append(uid)
        ctx.line(f"{ctx.name(uid)} is sent to Jail (leaving costs half the usual fee).", "bad")
        ctx.fx([{"type": "jail", "who": "self"}], uid, quiet=True)
    else:
        ctx.line(f"{ctx.name(uid)} walks free.", "good")


# --- All players ------------------------------------------------------------------
@script("time-bank-collapse")
def s_time_bank(ctx, card):
    ctx.push("effects", effects=plain_effects(card), actor=ctx.ev["drawer"])
    for u in ctx.order():
        ctx.push("hand_over", uid=u, count=2, to=None)


def _collectables_in_hand(ctx, uid):
    return [e for e in ctx.state["hands"].get(str(uid), []) if cards_mod.split_entry(e)[0] == "collectable"]


@step
def hand_over(ctx, uid, count, to):
    """Discard (to=None) or give (to=uid) `count` collectables of the player's choice."""
    held = _collectables_in_hand(ctx, uid)
    if len(held) <= count:
        hand_over_done(ctx, held, uid, to)
        return
    verb = "discard" if to is None else f"hand over to {ctx.name(to)}"
    ctx.ask("cards", uid, "hand_over_done", args={"uid": uid, "to": to}, count=count, candidates=held,
            question=f"{ctx.name(uid)}: choose {count} collectables to {verb}")


@step
def hand_over_done(ctx, answer, uid, to):
    hand = ctx.state["hands"].setdefault(str(uid), [])
    titles = []
    for entry in answer:
        if entry not in hand:
            continue
        hand.remove(entry)
        deck, inst = cards_mod.split_entry(entry)
        titles.append((B._pc(ctx.state, deck, inst) or {}).get("title", "a card"))
        if to is None:
            cards_mod.discard(ctx.state["decks"], deck, inst)
        else:
            ctx.state["hands"].setdefault(str(to), []).append(entry)
    if not titles:
        ctx.line(f"{ctx.name(uid)} has no collectables to {'discard' if to is None else 'hand over'}.")
    elif to is None:
        ctx.line(f"{ctx.name(uid)} discards {', '.join(titles)}.", "bad")
    else:
        ctx.line(f"{ctx.name(uid)} hands {len(titles)} collectable{'s' if len(titles) > 1 else ''} to {ctx.name(to)}.", "bad")


@script("curfew")
def s_curfew(ctx, card):
    for u in ctx.order(include_jailed=False):
        ctx.roll(u, "Curfew", "curfew_rolled", args={"uid": u}, need=5, leader_need=3)
    ctx.push("say", text="Everyone who made it inside moved to the next named building and took its action.")


def _next_building(position):
    for t in BUILDING_TILES:
        if t > position:
            return t
    return BUILDING_TILES[0]


@step
def curfew_rolled(ctx, r, uid):
    if not r["ok"]:
        ctx.fx([{"type": "bleed", "who": "self", "amount": 3}, {"type": "heat", "who": "self", "amount": 1}], uid)
        return
    to = _next_building(B._position(ctx.state, uid))
    ctx.state["positions"][str(uid)] = to
    ctx.line(f"{ctx.name(uid)} makes it inside: moves to {rules.tile_label(to)}.", "good")
    dealt = B._deal_landing_cards(ctx.room, ctx.state, ctx.participants()[uid], rules.tile(to))
    if dealt:
        ctx.line(dealt.lstrip("🎴 "), "good")


@script("reputation")
def s_reputation(ctx, card):
    voters = ctx.order()
    ctx.ask("vote", None, "reputation_counted", voters=voters, anonymous=True, exclude_self=True,
            question="🗳️ Anonymous straw poll: who should lose time? Each vote costs them 1.5 hours.",
            options=ctx.options_for(voters))


@step
def reputation_counted(ctx, answer):
    tally = {}
    for choice in answer.values():
        tally[int(choice)] = tally.get(int(choice), 0) + 1
    if not tally:
        ctx.line("Nobody voted.")
    for u, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        ctx.line(f"🗳️ {ctx.name(u)}: {n} vote{'s' if n > 1 else ''}.")
        ctx.time(u, -90 * n)


# --- Court and choices for the drawer --------------------------------------------
@script("sexual-misconduct")
def s_misconduct(ctx, card):
    d = ctx.ev["drawer"]
    ctx.push("apply", effects=[{"type": "fire", "who": "self"}], actor=d)
    ctx.ask("choice", d, "misconduct_choice", args={"uid": d},
            question="You lost your job. Take your employer to court? (5+ to win)",
            options=[{"key": "accept", "label": "Accept it"}, {"key": "court", "label": "Take them to court"}])


@step
def misconduct_choice(ctx, answer, uid):
    if answer == "accept":
        ctx.line(f"{ctx.name(uid)} accepts it.")
        return
    ctx.line(f"⚖️ {ctx.name(uid)} chooses to take their employer to court.")
    ctx.court(uid, "Sexual Misconduct",
              spec("say", text=f"{ctx.name(uid)} becomes the SHAG officer: choose any available job in the You panel.", tone="good"),
              fx_spec(uid, {"type": "time", "who": "self", "minutes": -240}, {"type": "heat", "who": "self", "amount": 2}),
              a="They become the SHAG officer (any job)", b="−4 hours, +2 heat")


@script("insurance-fraud")
def s_insurance(ctx, card):
    d = ctx.ev["drawer"]
    ctx.push("apply", effects=[{"type": "time", "who": "self", "minutes": -120}], actor=d)
    ctx.ask("choice", d, "insurance_choice", args={"uid": d},
            question="You paid 2 hours for the damage. Take your insurer to court? (5+: +6 hours; lose: −4 hours, +2 heat)",
            options=[{"key": "accept", "label": "Leave it"}, {"key": "court", "label": "Take them to court"}])


@step
def insurance_choice(ctx, answer, uid):
    if answer == "accept":
        ctx.line(f"{ctx.name(uid)} leaves it there.")
        return
    ctx.line(f"⚖️ {ctx.name(uid)} chooses to take their insurer to court.")
    ctx.court(uid, "Insurance Fraud", fx_spec(uid, {"type": "time", "who": "self", "minutes": 360}),
              fx_spec(uid, {"type": "time", "who": "self", "minutes": -240}, {"type": "heat", "who": "self", "amount": 2}),
              a="The insurer pays out (+6 hours)", b="−4 hours, +2 heat")


@script("gambling-addict")
def s_gambling(ctx, card):
    d = ctx.ev["drawer"]
    ctx.ask("choice", d, "gamble_choice", args={"uid": d},
            question="You owe 4 hours. Pay now, or gamble it? One roll: 5+ clears it with +2 hours back; "
                     "otherwise the debt doubles to 8 hours and the court orders it paid.",
            options=[{"key": "pay", "label": "Pay 4 hours"}, {"key": "gamble", "label": "Gamble it (one roll)"}])


@step
def gamble_choice(ctx, answer, uid):
    if answer == "pay":
        ctx.line(f"💸 {ctx.name(uid)} chooses to pay the 4 hours now.")
        ctx.time(uid, -240)
        return
    ctx.line(f"🎰 {ctx.name(uid)} chooses to gamble it: one roll, 5 or higher to win.")
    ctx.roll(uid, "Gambling", "gamble_rolled", args={"uid": uid}, need=5)


@step
def gamble_rolled(ctx, r, uid):
    if r["ok"]:
        ctx.line(f"{ctx.name(uid)} scores big and clears the debt.", "good")
        ctx.time(uid, 120)
        return
    ctx.line(f"⚖️ {ctx.name(uid)} loses: the debt doubles to 8 hours, and the court orders it paid.", "bad")
    ctx.time(uid, -480)


@script("bank-robbery")
def s_bank(ctx, card):
    d = ctx.ev["drawer"]
    ctx.ev["vars"]["crew"] = [d]
    for u in ctx.order():
        if u != d:
            ctx.ask("choice", u, "bank_join", args={"uid": u},
                    question=f"{ctx.name(u)}: help {ctx.name(d)} rob the Time Bank?",
                    options=[{"key": "join", "label": "I'm in"}, {"key": "no", "label": "No thanks"}])
    ctx.push("bank_go")


@step
def bank_join(ctx, answer, uid):
    if answer == "join":
        ctx.ev["vars"]["crew"].append(uid)
        ctx.line(f"{ctx.name(uid)} joins the robbery.")


@step
def bank_go(ctx):
    crew = ctx.ev["vars"]["crew"]
    ctx.line(f"The crew: {', '.join(ctx.name(u) for u in crew)}. Each tries to roll a 6.")
    for u in crew:
        ctx.roll(u, "Bank Robbery", "bank_rolled", args={"uid": u}, need=6, skip_if="winner")
    ctx.push("bank_end")


@step
def bank_rolled(ctx, r, uid):
    if r["ok"]:
        ctx.ev["vars"]["winner"] = uid
        ctx.line(f"💰 {ctx.name(uid)} cracks the vault and shares out the 12 hours.", "good")


@step
def bank_end(ctx):
    v = ctx.ev["vars"]
    crew = v["crew"]
    if v.get("winner") is not None:
        ctx.ask("allocate", v["winner"], "bank_split", total=720, step=30, recipients=crew,
                labels={str(u): ctx.name(u) for u in crew},
                question="Share out the 12 hours of loot between the crew")
        return
    ctx.line("Everyone failed: the whole crew goes to court for attempted armed robbery.", "bad")
    for u in crew:
        ctx.court(u, "Attempted robbery", spec("say", text=f"{ctx.name(u)} is acquitted.", tone="good"),
                  fx_spec(u, {"type": "heat", "who": "self", "amount": 2}), a="Acquitted", b="Guilty (+2 heat)")


@step
def bank_split(ctx, answer):
    for key, minutes in answer.items():
        if minutes:
            ctx.time(int(key), minutes)


@script("gerry-s-slot-machine")
def s_slots(ctx, card):
    d = ctx.ev["drawer"]
    ctx.roll(d, "Gerry's Slot Machine", "slots_rolled", args={"uid": d}, charm="bonus")


@step
def slots_rolled(ctx, r, uid):
    v = min(8, r["total"])
    if v >= 8:
        ctx.line(f"🎰 JACKPOT! {ctx.name(uid)} wins the game!", "good")
        B._log(ctx.state, f"🏆 {ctx.name(uid)} hit the jackpot on Gerry's Slot Machine and wins the game!",
               kind="round", announce=True)
    elif v == 7:
        ctx.ask("choice", uid, "slots_seven", args={"uid": uid}, question="🎰 7! Become an Executive, or take 8 hours?",
                options=[{"key": "exec", "label": "Become Executive"}, {"key": "time", "label": "+8 hours"}])
    elif v == 6:
        ctx.fx([{"type": "bleed", "who": "self", "amount": -cards_mod.BLEED_MAX},
                {"type": "heat", "who": "self", "amount": -cards_mod.HEAT_MAX}], uid)
    elif v == 5:
        ctx.ask("tile", uid, "slots_move", args={"uid": uid}, question="🎰 5! Move directly to any tile",
                tiles=[{"key": t["index"], "label": f"{t['index']}. {t['label']}"} for t in rules.TILES])
    elif v == 4:
        ctx.fx([{"type": "draw", "deck": "collectable", "count": 2}], uid)
    elif v == 3:
        ctx.line(f"🎰 3: {ctx.name(uid)} draws another scenario card.")
        ctx.ev["chain"] = True
    elif v == 2:
        ctx.time(uid, -180)
    else:
        ctx.line(f"🎰 1: {ctx.name(uid)} is arrested.", "bad")
        ctx.fx([{"type": "jail", "who": "self"}], uid, quiet=True)


@step
def slots_seven(ctx, answer, uid):
    if answer == "exec":
        rp = ctx.participants()[uid]
        rp.perk = "Executive"
        db.session.commit()
        ctx.room_changed = True
        ctx.line(f"{ctx.name(uid)} becomes an Executive.", "good")
    else:
        ctx.time(uid, 480)


@step
def slots_move(ctx, answer, uid):
    rp = ctx.participants()[uid]
    if rp.is_in_jail:
        ctx.line(f"{ctx.name(uid)} is in Jail and can't move.")
        return
    ctx.state["positions"][str(uid)] = int(answer)
    ctx.line(f"{ctx.name(uid)} moves to {rules.tile_label(int(answer))}.")


# --- Factions ---------------------------------------------------------------------
@script("loan-sharks")
def s_loan_sharks(ctx, card):
    sharks = [u for u in ctx.order() if (ctx.player(u).get("faction") or "").lower() == "illicit"]
    if not sharks:
        cannot_play(ctx, "Nobody holds an Illicit job, so this card can't be used.")
        return
    victims = [u for u in ctx.order() if u not in sharks]
    if not victims:
        cannot_play(ctx, "Everyone is Illicit: there's nobody to collect from.")
        return
    for s in sharks:
        ctx.ask("pick", s, "shark_victim", args={"shark": s}, question=f"🦈 {ctx.name(s)}: choose your victim",
                options=ctx.options_for(victims), min=1, max=1)


@step
def shark_victim(ctx, answer, shark):
    v = int(answer[0])
    ctx.ask("choice", shark, "shark_claim", args={"shark": shark, "victim": v},
            question=f"🦈 What do you take from {ctx.name(v)}?",
            options=[{"key": "time", "label": "A) Claim back 3 hours"},
                     {"key": "cards", "label": "B) 2 collectables (their choice)"}])


@step
def shark_claim(ctx, answer, shark, victim):
    if answer == "time":
        ctx.fx([{"type": "steal", "who": "choose", "minutes": 180}], shark, chosen=victim)
    else:
        ctx.push("hand_over", uid=victim, count=2, to=shark)


FIRE_SALE = [("job", "Job Opportunity", 10), ("hospital", "Hospital Item", 20),
             ("collectable", "Collectable", 30), ("shortcut", "Shortcut", 30)]


@script("fire-sale")
def s_fire_sale(ctx, card):
    ctx.push("effects", effects=plain_effects(card), actor=ctx.ev["drawer"])
    for u in ctx.order():
        if (ctx.player(u).get("faction") or "").lower() == "public service":
            ctx.ask("buy", u, "fire_sale_bought", args={"uid": u}, max=2,
                    items=[{"key": d, "label": label, "minutes": m} for d, label, m in FIRE_SALE],
                    question=f"🔥 {ctx.name(u)}: buy up to two items at Fire Sale prices (not doubled by Democracy)")


@step
def fire_sale_bought(ctx, answer, uid):
    prices = {d: m for d, _, m in FIRE_SALE}
    labels = {d: label for d, label, _ in FIRE_SALE}
    bought = []
    for deck, n in answer.items():
        for _ in range(int(n)):
            if ctx.player(uid)["minutes"] < prices[deck]:
                ctx.line(f"{ctx.name(uid)} can't afford a {labels[deck]}.")
                break
            if not B._give_cards(ctx.state, uid, 1, deck):
                ctx.line(f"The {labels[deck].lower()} deck is empty.")
                break
            ctx.fx([{"type": "time", "who": "self", "minutes": -prices[deck]}], uid, quiet=True)
            bought.append(labels[deck])
    ctx.line(f"🛒 {ctx.name(uid)} buys {', '.join(bought)}." if bought else f"{ctx.name(uid)} buys nothing.")


# --- Government ---------------------------------------------------------------------
@script("revolution")
def s_revolution(ctx, card):
    ctx.push("effects", effects=plain_effects(card), actor=ctx.ev["drawer"])
    ctx.push("revolution_change")


@step
def revolution_change(ctx):
    current = ctx.government()
    _change_government(ctx, random.choice([g for g in GOVERNMENTS if g != current]), "🚩 Revolution! ")


def _change_government(ctx, new, prefix="🏛️ "):
    room = ctx.room
    gov = room.government
    if gov is None:
        from app.models import Government
        gov = Government(type=new, room_id=room.id)
        db.session.add(gov)
    gov.type = new
    db.session.flush()
    GovernmentMember.query.filter_by(government_id=gov.id).delete(synchronize_session=False)
    text = f"{prefix}The government is now {new}."
    if new == "Communism":
        alive = ctx.order()
        politburo = random.sample(alive, min(2, len(alive)))
        for uid in politburo:
            db.session.add(GovernmentMember(government_id=gov.id, user_id=uid, role="politburo"))
        text += f" The Politburo: {' and '.join(ctx.name(u) for u in politburo)}."
    elif new == "Dictatorship":
        text += " Everyone now bids secretly for the Dictator's seat (the auction is open)."
    elif new == "Republic":
        text += " Everyone now votes for the Head of State (the ballot is open)."
    db.session.commit()
    # A new government starts with everyone's approval
    B.board_gov.reset_approvals(room)
    ctx.room_changed = True
    B._check_government(room, ctx.state)
    ctx.line(text)
    # Choosing the new leaders opens for everyone straight away
    from app.websocket import sockets
    if new == "Dictatorship":
        sockets.begin_dictator_bidding(room)
    elif new == "Republic":
        sockets.begin_republic_voting(room)


@script("no-confidence-vote")
def s_no_confidence(ctx, card):
    if ctx.government() == "Democracy":
        cannot_play(ctx, "Under Democracy this card is ignored.")
        return
    leaders = ctx.leaders()
    if not leaders:
        cannot_play(ctx, "There are no government leaders to vote on.")
        return
    judge = ctx.judge()
    if judge is not None:
        ctx.ask("pick", judge, "nc_judge_pick", args={"judge": judge},
                question="⚖️ Judge: decide one leader's outcome yourself? (pick none to leave it to the vote)",
                options=ctx.options_for(leaders), min=0, max=1)
    ctx.push("nc_votes", leaders=leaders)


@step
def nc_judge_pick(ctx, answer, judge):
    if not answer:
        return
    leader = int(answer[0])
    ctx.ev["vars"]["judged"] = leader
    ctx.ask("choice", judge, "nc_judged", args={"leader": leader},
            question=f"⚖️ Judge: should {ctx.name(leader)} stay in government?",
            options=[{"key": "keep", "label": "Stays"}, {"key": "remove", "label": "Removed"}])


@step
def nc_judged(ctx, answer, leader):
    _nc_outcome(ctx, leader, answer == "remove", "by the Judge")


@step
def nc_votes(ctx, leaders):
    judged = ctx.ev["vars"].get("judged")
    for leader in leaders:
        if leader != judged:
            ctx.ask("vote", None, "nc_counted", args={"leader": leader}, voters=ctx.order(), anonymous=True,
                    question=f"🗳️ No confidence: should {ctx.name(leader)} stay in government?",
                    options=[{"key": "keep", "label": "Stay"}, {"key": "remove", "label": "Remove"}])


@step
def nc_counted(ctx, answer, leader):
    removes = sum(1 for v in answer.values() if v == "remove")
    keeps = len(answer) - removes
    ctx.line(f"🗳️ {ctx.name(leader)}: {keeps} to stay, {removes} to remove.")
    _nc_outcome(ctx, leader, removes > keeps, "by the vote")


def _nc_outcome(ctx, leader, removed, how):
    if not removed:
        ctx.line(f"{ctx.name(leader)} stays in government ({how}).", "good")
        return
    gov = ctx.room.government
    if gov:
        GovernmentMember.query.filter_by(government_id=gov.id, user_id=leader).delete(synchronize_session=False)
        db.session.commit()
    barred = ctx.state.setdefault("barred_leaders", [])
    if leader not in barred:
        barred.append(leader)
    ctx.room_changed = True
    ctx.line(f"{ctx.name(leader)} is removed from government ({how}) and can't be the next leader.", "bad")


# --- Rolls ---------------------------------------------------------------------------
@script("time-laundering")
def s_laundering(ctx, card):
    d = ctx.ev["drawer"]
    everyone = ctx.order()
    ctx.line("💵 8 hours = 4 lots of 2 hours: one roll per lot (4+ to yourself, 3+ to someone else), "
             "then a court case for any lots that fail.")
    ctx.ask("allocate", d, "launder_split", args={"uid": d}, total=480, step=120, recipients=everyone,
            labels={str(u): ctx.name(u) + (" (you: 4+)" if u == d else " (3+)") for u in everyone},
            question="Launder 8 hours in 2-hour lots: who gets each lot? (to yourself 4+, to another player 3+)")


@step
def launder_split(ctx, answer, uid):
    ctx.ev["vars"]["failed"] = {}
    for key, minutes in answer.items():
        to = int(key)
        for _ in range(int(minutes) // 120):
            ctx.roll(uid, f"Launder 2h to {ctx.name(to)}", "launder_rolled", args={"to": to},
                     need=4 if to == uid else 3)
    ctx.push("launder_court")


@step
def launder_rolled(ctx, r, to):
    if r["ok"]:
        ctx.time(to, 120)
    else:
        failed = ctx.ev["vars"]["failed"]
        failed[str(to)] = failed.get(str(to), 0) + 120


@step
def launder_court(ctx):
    for key, minutes in ctx.ev["vars"].get("failed", {}).items():
        u = int(key)
        ctx.line(f"{ctx.name(u)} goes to court over {B._fmt(minutes)} of failed laundering.", "bad")
        ctx.court(u, "Time Laundering", spec("say", text=f"{ctx.name(u)} is acquitted.", tone="good"),
                  fx_spec(u, {"type": "time", "who": "self", "minutes": -minutes}),
                  a="Acquitted", b=f"Pay {B._fmt(minutes)}")


# --- Ongoing cards ---------------------------------------------------------------------
@script("rnli")
def s_rnli(ctx, card):
    d = ctx.ev["drawer"]
    ctx.roll(d, "RNLI", "rnli_rolled", args={"uid": d}, need=5)


@step
def rnli_rolled(ctx, r, uid):
    bill = 180 if r["ok"] else 480
    debts = ctx.state.setdefault("debts", {})
    debts[str(uid)] = {"card": ctx.ev["inst"], "title": ctx.ev["title"], "minutes": bill, "plan": 60,
                       # repayments start next turn
                       "paid_seq": ctx.state.get("turn_seq") if B._current_turn_user(ctx.state) == uid else None}
    ctx.ev["keep"] = True
    ctx.line(f"🛟 {ctx.name(uid)}'s RNLI bill is {B._fmt(bill)}: 1 hour a turn (or up to 3) is repaid when they "
             "collect income, and 30 minutes interest is added at the end of each turn until it's paid.", "bad")


@script("income-tax")
def s_income_tax(ctx, card):
    ctx.state["income_tax"] = {"card": ctx.ev["inst"], "title": ctx.ev["title"], "donated": 0, "goal": 1440}
    ctx.ev["keep"] = True
    ctx.line("💷 Income Tax is in force: landing on Collectables & Promotions costs no job 30m, "
             "Tier 1/2 1h, Tier 3 1.5h, a title 2h — until 24 hours are donated to the state.")


@script("bounty-board")
def s_bounty(ctx, card):
    state = ctx.state
    keep_reveal = state.get("reveal")
    added = 0
    while len(state["assignments"]) < cards_mod.MAX_ASSIGNMENTS:
        inst, _ = cards_mod.draw(state["decks"], "assignment", B._cards(state))
        if not inst:
            break
        target = cards_mod.black_bag(ctx.order(), state["assignments"])
        if target is None:
            cards_mod.discard(state["decks"], "assignment", inst)
            break
        B._place_assignment(ctx.room, state, inst, ctx.ev["drawer"], target)
        added += 1
    state["reveal"] = keep_reveal
    state["bounty"] = {"card": ctx.ev["inst"], "title": ctx.ev["title"], "left": 2}
    ctx.ev["keep"] = True
    ctx.line(f"📜 {added} new assignment slip{'s' if added != 1 else ''} fill the board. The next two assignments "
             "can be completed against anyone with a title: double reward, and the target is demoted.")


def income_tax_for(rp) -> int:
    if rp.perk:
        return 120
    tier = rp.job.tier if rp.job else 0
    if tier >= 3:
        return 90
    if tier >= 1:
        return 60
    return 30


# --------------------------------------------------------------------------
# Hand cards that play out live: moves, jobs, assignments, the Senate...
# --------------------------------------------------------------------------

def card(*slugs, check=None):
    def wrap(fn):
        for s_ in slugs:
            CARD_SCRIPTS[s_] = fn
            if check:
                CARD_CHECKS[s_] = check
        return fn
    return wrap


def card_script(card_def):
    """The live script for a hand card, if it has one."""
    if not card_def or card_def.get("deck") not in cards_mod.HAND_DECKS:
        return None
    return CARD_SCRIPTS.get(card_def.get("script") or "") or CARD_SCRIPTS.get(slug(card_def["title"]))


def card_check(room, state, user_id, card_def):
    """Why the card can't be played right now (it stays in your hand), or None."""
    check = CARD_CHECKS.get(card_def.get("script") or "") or CARD_CHECKS.get(slug(card_def["title"]))
    return check(room, state, user_id) if check else None


def start_card(room, state, deck, inst, actor, entry=None):
    """
    A hand card was played: everyone sees it play out (like a scenario card).
    It stays in the hand (as `entry`) until its action has happened: cancelling it returns it.
    """
    card_def = cards_mod.card_of(B._cards(state), deck, inst)
    state["event_seq"] = state.get("event_seq", 0) + 1
    state.pop("event_secret", None)
    state["event"] = {
        "id": state["event_seq"], "deck": deck, "inst": inst, "card": B._pc(state, deck, inst),
        "title": card_def["title"], "drawer": actor, "queue": [], "prompt": None, "lines": [], "roll": None,
        "vars": {}, "done": False, "keep": False, "chain": False, "war": False,
        "started_at": B._iso(B._now()), "after_roll": None, "played": True, "entry": entry,
    }
    ctx = Ctx(room, state)
    card_script(card_def)(ctx, card_def)
    return run(room, state, ctx)


def _own_turn(state, user_id):
    return state.get("started") and B._current_turn_user(state) == user_id


def _jailed(room, user_id):
    rp = B._participants(room).get(user_id)
    return bool(rp and rp.is_in_jail)


# --- Advance: move to another player's tile, not beyond the Black Market --------------
def _advance_targets(room, state, user_id):
    mine = B._position(state, user_id)
    out = []
    for uid, rp in B._participants(room).items():
        pos = state["positions"].get(str(uid))
        if uid == user_id or pos is None or rp.is_in_jail or not B._alive(rp):
            continue
        if mine < pos <= rules.BLACK_MARKET:
            out.append((uid, pos))
    return sorted(out, key=lambda t: t[1])


def _check_advance(room, state, user_id):
    if not _own_turn(state, user_id):
        return "Use Advance on your turn."
    if _jailed(room, user_id):
        return "You can't advance out of Jail."
    if not _advance_targets(room, state, user_id):
        return "Nobody is ahead of you before the Black Market, so there's nobody to advance to."
    return None


@card("advance", check=_check_advance)
def c_advance(ctx, card_def):
    me = ctx.ev["drawer"]
    options = [{"key": str(uid), "label": f"{ctx.name(uid)} — {rules.tile_label(pos)}"}
               for uid, pos in _advance_targets(ctx.room, ctx.state, me)]
    ctx.ask("pick", me, "advance_go", args={"uid": me}, question="Advance to which player?",
            options=options, min=1, max=1)


@step
def advance_go(ctx, answer, uid):
    target = int(answer[0])
    to = ctx.state["positions"].get(str(target))
    text = B._card_move(ctx.room, ctx.state, ctx.participants()[uid], to=to, action=True,
                        why=f"advances to {ctx.name(target)} on")
    ctx.line(f"🏃 {text}.", "good")
    ctx.room_changed = True


# --- Shortcut: jump 5 tiles and action it, or move to the Senate if within 5 ----------
SENATE_TILE = 9


def _check_shortcut(room, state, user_id):
    if not _own_turn(state, user_id):
        return "Use a Shortcut on your turn."
    if _jailed(room, user_id):
        return "You can't take a Shortcut out of Jail."
    return None


@card("shortcut", check=_check_shortcut)
def c_shortcut(ctx, card_def):
    me = ctx.ev["drawer"]
    pos = B._position(ctx.state, me)
    five = rules.compute_move(pos, 5)
    landing = rules.tile_label(five["jumped_from"] if five["jumped_from"] is not None else five["to"])
    options = [{"key": "jump", "label": f"Jump 5 tiles → {landing}"}]
    dist = (SENATE_TILE - pos) % rules.BOARD_SIZE
    if 1 <= dist <= 5 and rules.tile(pos)["kind"] not in ("senate", "senate_virus"):
        options.append({"key": "senate", "label": f"Move to the Senate ({dist} tile{'s' if dist > 1 else ''})"})
    ctx.ask("choice", me, "shortcut_go", args={"uid": me}, question="Where does your Shortcut take you?",
            options=options)


@step
def shortcut_go(ctx, answer, uid):
    rp = ctx.participants()[uid]
    if answer == "senate":
        text = B._card_move(ctx.room, ctx.state, rp, to=SENATE_TILE, action=True, why="takes a Shortcut to")
    else:
        text = B._card_move(ctx.room, ctx.state, rp, steps=5, action=True, why="jumps 5 tiles to")
    ctx.line(f"🏃 {text}.", "good")
    ctx.room_changed = True


# --- Mission Objective: change a slip's target, or introduce a new slip ---------------
def _check_mission(room, state, user_id):
    if not state.get("started"):
        return "The game hasn't started."
    deck = state["decks"]["assignment"]
    can_new = len(state["assignments"]) < cards_mod.MAX_ASSIGNMENTS and (deck["draw"] or deck["discard"])
    order = state.get("turn_order") or []
    movable = any(any(u != a["target"] and cards_mod.assignments_against([x for x in state["assignments"] if x is not a], u)
                      < cards_mod.MAX_PER_TARGET for u in order) for a in state["assignments"])
    if not movable and not can_new:
        return "There are no assignment slips to change or draw."
    return None


@card("mission-objective", check=_check_mission)
def c_mission(ctx, card_def):
    me = ctx.ev["drawer"]
    options = []
    if any(_retarget_pool(ctx, a) for a in ctx.state["assignments"]):
        options.append({"key": "change", "label": "Change the target of a slip"})
    if len(ctx.state["assignments"]) < cards_mod.MAX_ASSIGNMENTS:
        options.append({"key": "new", "label": "Introduce a new assignment"})
    ctx.ask("choice", me, "mission_choice", args={"uid": me}, question="Mission Objective: what do you do?",
            options=options)


@step
def mission_choice(ctx, answer, uid):
    if answer == "new":
        state = ctx.state
        keep_reveal = state.get("reveal")
        inst, _ = cards_mod.draw(state["decks"], "assignment", B._cards(state))
        target = cards_mod.black_bag(ctx.order(), state["assignments"]) if inst else None
        if not inst or target is None:
            if inst:
                cards_mod.discard(state["decks"], "assignment", inst)
            ctx.line("No assignment could be drawn.")
            return
        B._place_assignment(ctx.room, state, inst, uid, target)
        state["reveal"] = keep_reveal
        title = (B._pc(state, "assignment", inst) or {}).get("title", "a slip")
        ctx.line(f"📜 A new assignment, “{title}”, targets {ctx.name(target)}.")
        return
    options = [{"key": str(a["id"]), "label": f"“{(B._pc(ctx.state, 'assignment', a['card']) or {}).get('title', 'Slip')}” → "
                                             f"{ctx.name(a['target'])}"} for a in ctx.state["assignments"] if _retarget_pool(ctx, a)]
    if not options:
        ctx.line("No slip can be moved: everyone else already has the most slips on them.")
        return
    ctx.ask("pick", uid, "mission_slip", args={"uid": uid}, question="Which slip do you want to retarget?",
            options=options, min=1, max=1)


def _retarget_pool(ctx, slip):
    """Who a slip could be moved onto: anyone else with room for another slip."""
    others = [a for a in ctx.state["assignments"] if a is not slip]
    return [u for u in ctx.order() if u != slip["target"]
            and cards_mod.assignments_against(others, u) < cards_mod.MAX_PER_TARGET]


@step
def mission_slip(ctx, answer, uid):
    slip = next((a for a in ctx.state["assignments"] if str(a["id"]) == answer[0]), None)
    if not slip:
        ctx.line("That slip has gone.")
        return
    pool = _retarget_pool(ctx, slip)
    if not pool:
        ctx.line("Nobody else has room for that slip.")
        return
    title = (B._pc(ctx.state, "assignment", slip["card"]) or {}).get("title", "the slip")
    ctx.ask("pick", uid, "mission_target", args={"uid": uid, "slip": slip["id"]},
            question=f"“{title}” targets {ctx.name(slip['target'])} now. Who should it target instead?",
            options=ctx.options_for(pool), min=1, max=1)


@step
def mission_target(ctx, answer, uid, slip):
    a = next((x for x in ctx.state["assignments"] if x["id"] == slip), None)
    if not a:
        return
    old = a["target"]
    a["target"] = int(answer[0])
    # Shown on the slip, so everyone can see it changed
    a["retargeted"] = {"from": old, "by": uid, "round": ctx.state.get("round")}
    title = (B._pc(ctx.state, "assignment", a["card"]) or {}).get("title", "A slip")
    ctx.line(f"🔁 Assignment changed: “{title}” now targets {ctx.name(a['target'])} instead of {ctx.name(old)}.", "good")
    B._log(ctx.state, f"🔁 {ctx.name(uid)} moved the assignment “{title}” from {ctx.name(old)} to {ctx.name(a['target'])}.",
           kind="card", announce=True)


# --- Remote Access: the Senate from anywhere, this turn -------------------------------
def _check_remote(room, state, user_id):
    if not _own_turn(state, user_id):
        return "Use Remote Access on your turn."
    if state["turn"].get("remote_senate"):
        return "You already have Remote Access this turn."
    return None


@card("remote-access", check=_check_remote)
def c_remote(ctx, card_def):
    me = ctx.ev["drawer"]
    ctx.state["turn"]["remote_senate"] = True
    ctx.line(f"🏛️ {ctx.name(me)} can use the Senate from anywhere this turn: change a vote, "
             "or introduce an oppression if they're in government.", "good")


# --- Jobs: Job Opportunity, Careers Advisor, Promotion -----------------------------------
def _job_free(room, job, user_id):
    """Tier 3 jobs are unique: one holder each."""
    if job.tier != 3:
        return True
    return not any(p.job_id == job.id and p.userId != user_id and B._alive(p) for p in room.participants)


def _job_options(room, user_id, jobs):
    rp = B._participants(room).get(user_id)
    return [{"key": str(j.id), "label": f"{j.name} ({j.type}, Tier {j.tier})"}
            for j in jobs if _job_free(room, j, user_id) and (not rp or rp.job_id != j.id)]


def _set_job(ctx, uid, job_id):
    job = Job.query.get(int(job_id))
    rp = ctx.participants()[uid]
    if not job or not _job_free(ctx.room, job, uid):
        ctx.line("That job has just been taken.")
        return
    rp.job_id = job.id
    db.session.commit()
    socketio.emit("userJobUpdate", {"user_id": uid, "job_name": job.name, "job_tier": job.tier}, room=str(ctx.room.id))
    ctx.room_changed = True
    ctx.line(f"💼 {ctx.name(uid)} becomes a {job.name} ({job.type}, Tier {job.tier}).", "good")


def _check_started(room, state, user_id):
    return None if state.get("started") else "The game hasn't started."


@card("job-opportunity", check=_check_started)
def c_job_opportunity(ctx, card_def):
    me = ctx.ev["drawer"]
    jobs = Job.query.filter_by(tier=1).order_by(Job.id).all()
    ctx.ask("job", me, "job_chosen", args={"uid": me}, question="Job Opportunity: choose a Tier 1 job",
            options=_job_options(ctx.room, me, jobs), keep=True, card="Job Opportunity")


@card("careers-advisor", check=_check_started)
def c_careers(ctx, card_def):
    me = ctx.ev["drawer"]
    jobs = Job.query.filter(Job.tier >= 1).order_by(Job.tier, Job.type, Job.name).all()
    ctx.ask("job", me, "job_chosen", args={"uid": me}, question="Careers Advisor: choose any available job",
            options=_job_options(ctx.room, me, jobs), keep=True, card="Careers Advisor")


@step
def job_chosen(ctx, answer, uid):
    if answer == "keep":
        ctx.line(f"{ctx.name(uid)} keeps their job.")
        return
    _set_job(ctx, uid, answer)


TITLES = ["Manager", "Senior", "Executive"]


def _promotion_options(room, user_id):
    rp = B._participants(room).get(user_id)
    options = []
    tier = rp.job.tier if rp.job else 0
    # Titles are only for Tier 3 jobs (and only while one of that title is free)
    if rp.perk != "Executive" and tier == 3:
        nxt = TITLES[TITLES.index(rp.perk) + 1] if rp.perk in TITLES else "Manager"
        held = sum(1 for p in room.participants if p.perk == nxt and p.userId != user_id)
        if held < B.board_jobs.TITLE_QUANTITY[nxt]:
            options.append({"key": "title", "label": f"Title: {rp.perk or 'none'} → {nxt}"})
    if 1 <= tier < 3:
        jobs = Job.query.filter_by(type=rp.job.type, tier=tier + 1).order_by(Job.name).all()
        options += [{"key": o["key"], "label": f"Job: {o['label']}"} for o in _job_options(room, user_id, jobs)]
    return options


def _check_promotion(room, state, user_id):
    if not state.get("started"):
        return "The game hasn't started."
    if not _promotion_options(room, user_id):
        return "There's nothing to promote: your job can't go up a tier, and titles need a Tier 3 job."
    return None


@card("promotion", check=_check_promotion)
def c_promotion(ctx, card_def):
    me = ctx.ev["drawer"]
    options = _promotion_options(ctx.room, me)
    title = [o for o in options if o["key"] == "title"]
    jobs = [o for o in options if o["key"] != "title"]
    if title and jobs:
        ctx.ask("choice", me, "promotion_route", args={"uid": me}, question="Promotion: go up a title level, or a job tier?",
                options=title + [{"key": "job", "label": "Job: up a tier (choose from the jobs list)"}])
    elif title:
        ctx.ask("choice", me, "promotion_chosen", args={"uid": me}, question="Promotion: go up a title level", options=title)
    else:
        _ask_promotion_job(ctx, me)


def _ask_promotion_job(ctx, uid):
    options = [{"key": o["key"], "label": o["label"].replace("Job: ", "", 1)}
               for o in _promotion_options(ctx.room, uid) if o["key"] != "title"]
    ctx.ask("job", uid, "promotion_chosen", args={"uid": uid}, question="Promotion: choose your job one tier up",
            options=options, keep=False, card="Promotion")


@step
def promotion_route(ctx, answer, uid):
    if answer == "title":
        ctx.push("promotion_chosen", answer="title", uid=uid)
    else:
        _ask_promotion_job(ctx, uid)


@step
def promotion_chosen(ctx, answer, uid):
    if answer != "title":
        _set_job(ctx, uid, answer)
        return
    rp = ctx.participants()[uid]
    old = rp.perk
    rp.perk = TITLES[TITLES.index(old) + 1] if old in TITLES else "Manager"
    db.session.commit()
    ctx.room_changed = True
    ctx.line(f"⬆️ {ctx.name(uid)} is promoted: {old or 'no title'} → {rp.perk}.", "good")


# --- Revolution Token: a vote to change the government -----------------------------------
@card("revolution-token", check=_check_started)
def c_revolution_token(ctx, card_def):
    me = ctx.ev["drawer"]
    current = ctx.government()
    ctx.ask("choice", me, "token_gov", args={"uid": me}, question="Call a vote: change the government to…",
            options=[{"key": g, "label": g} for g in GOVERNMENTS if g != current])


@step
def token_gov(ctx, answer, uid):
    ctx.line(f"🗳️ {ctx.name(uid)} calls a vote to change the government to {answer}.")
    ctx.ask("vote", None, "token_counted", args={"new": answer}, voters=ctx.order(), anonymous=True,
            question=f"🗳️ Change the government to {answer}?",
            options=[{"key": "yes", "label": "Yes, change it"}, {"key": "no", "label": "No, keep it"}])


@step
def token_counted(ctx, answer, new):
    yes = sum(1 for v in answer.values() if v == "yes")
    no = len(answer) - yes
    ctx.line(f"🗳️ {yes} for, {no} against.")
    if yes > no:
        _change_government(ctx, new)
    else:
        ctx.line("The vote fails: the government stays.", "bad")



# --------------------------------------------------------------------------
# Tier 3 job abilities (board_jobs.py): used on your turn, once per turn
# --------------------------------------------------------------------------

ABILITIES = {}
ABILITY_CHECKS = {}


def ability(job, check=None):
    def wrap(fn):
        ABILITIES[job] = fn
        if check:
            ABILITY_CHECKS[job] = check
        return fn
    return wrap


def ability_check(room, state, rp, job):
    if job not in ABILITIES:
        automatic = B.board_jobs.AUTOMATIC.get(job)
        return automatic or f"The {job} ability works by itself."
    check = ABILITY_CHECKS.get(job)
    return check(room, state, rp) if check else None


def start_ability(room, state, uid, job, text):
    """A job ability: everyone sees it play out (like a card)."""
    state["event_seq"] = state.get("event_seq", 0) + 1
    state.pop("event_secret", None)
    state["event"] = {
        "id": state["event_seq"], "deck": "ability", "inst": None,
        "card": {"uid": None, "id": B._slug_id(job), "deck": "ability", "title": job, "text": text,
                 "equip": False, "example": False, "needs_target": False, "notes": []},
        "title": job, "drawer": uid, "queue": [], "prompt": None, "lines": [], "roll": None,
        "vars": {}, "done": False, "keep": True, "chain": False, "war": False,
        "started_at": B._iso(B._now()), "after_roll": None, "played": True,
    }
    ctx = Ctx(room, state)
    ABILITIES[job](ctx)
    return run(room, state, ctx)


def _others(ctx, uid, alive=True):
    return [u for u in ctx.order() if u != uid]


def _move_roll(state):
    return (state.get("turn") or {}).get("move_roll")


def _need_roll(room, state, rp):
    return None if _move_roll(state) else "Roll for your move first: this ability uses your movement roll."


def _transfer(ctx, src, dst, minutes, why=""):
    """Move time between players (as much as the payer has)."""
    parts = ctx.participants()
    payer, payee = parts[src], parts.get(dst) if dst is not None else None
    amount = min(int(minutes), B._minutes_left(payer))
    if amount <= 0:
        ctx.line(f"{ctx.name(src)} has no time to pay.")
        return 0
    B._set_minutes(payer, B._minutes_left(payer) - amount)
    if payee:
        B._set_minutes(payee, B._minutes_left(payee) + amount)
    db.session.commit()
    ctx.room_changed = True
    to = f" to {ctx.name(dst)}" if payee else ""
    ctx.line(f"{ctx.name(src)} pays {B._fmt(amount)}{to}{why}.", "bad" if src != ctx.ev["drawer"] else "")
    return amount


# --- Stock Broker -------------------------------------------------------------
STOCK_TABLE = {1: -30, 2: -10, 3: 10, 4: 20, 5: 30, 6: 40}


@ability("Stock Broker", check=_need_roll)
def a_stock_broker(ctx):
    me = ctx.ev["drawer"]
    roll = _move_roll(ctx.state)
    ctx.ask("pick", me, "stock_pick", args={"uid": me, "roll": roll},
            question=f"Steal 30 minutes from whom? Your movement roll was {roll}: "
                     f"you'll get {B._fmt(STOCK_TABLE[roll]) if STOCK_TABLE[roll] >= 0 else '−' + B._fmt(STOCK_TABLE[roll])}.",
            options=ctx.options_for(_others(ctx, me)), min=1, max=1)


@step
def stock_pick(ctx, answer, uid, roll):
    target = int(answer[0])
    gain = STOCK_TABLE.get(min(6, max(1, int(roll))), 0)
    victim = ctx.participants()[target]
    taken = min(30, B._minutes_left(victim))
    B._set_minutes(victim, B._minutes_left(victim) - taken)
    me = ctx.participants()[uid]
    B._set_minutes(me, max(0, B._minutes_left(me) + gain))
    db.session.commit()
    ctx.room_changed = True
    ctx.line(f"📈 {ctx.name(uid)} takes {B._fmt(taken)} from {ctx.name(target)} and gambles it on a {roll}: "
             f"{'+' if gain >= 0 else '−'}{B._fmt(gain)} for {ctx.name(uid)}.", "good" if gain > 0 else "bad")


# --- CFO: sanction up to three players with 6+ items ------------------------------
def items_of(state, rp):
    """A job, a title, each collectable (in hand or equipped), each completed slip."""
    uid = str(rp.userId)
    hand = [e for e in state["hands"].get(uid, []) if B.cards_mod.split_entry(e)[0] == "collectable"]
    return (1 if rp.job and rp.job.tier else 0) + (1 if rp.perk else 0) + len(hand) + \
        len(state["equipped"].get(uid, [])) + len(state["slips"].get(uid, []))


def _cfo_targets(room, state, rp):
    return [p.userId for p in room.participants
            if p.userId != rp.userId and B._alive(p) and items_of(state, p) >= 6]


def _check_cfo(room, state, rp):
    return None if _cfo_targets(room, state, rp) else "Nobody else holds 6 or more items right now."


@ability("CFO", check=_check_cfo)
def a_cfo(ctx):
    me = ctx.ev["drawer"]
    targets = _cfo_targets(ctx.room, ctx.state, ctx.participants()[me])
    options = [{"key": str(u), "label": f"{ctx.name(u)} ({items_of(ctx.state, ctx.participants()[u])} items)"} for u in targets]
    ctx.ask("pick", me, "cfo_pick", args={"uid": me}, question="Sanction up to three players with 6 or more items (20 minutes each)",
            options=options, min=1, max=min(3, len(options)))


@step
def cfo_pick(ctx, answer, uid):
    for key in answer:
        _transfer(ctx, int(key), None, 20, " in sanctions")


# --- Time Keeper: siphon 20 minutes from one or two players ---------------------------
@ability("Time Keeper")
def a_time_keeper(ctx):
    me = ctx.ev["drawer"]
    others = _others(ctx, me)
    ctx.ask("pick", me, "keeper_pick", args={"uid": me}, question="Siphon 20 minutes from one or two players",
            options=ctx.options_for(others), min=1, max=min(2, len(others)))


@step
def keeper_pick(ctx, answer, uid):
    for key in answer:
        _transfer(ctx, int(key), uid, 20)


# --- Charity Commissioner: forgive a heat at an agreed price ------------------------------
def _check_charity(room, state, rp):
    if not any(p.userId != rp.userId and B._alive(p) and (p.heat or 0) > 0 for p in room.participants):
        return "Nobody else has any heat to forgive."
    return None


@ability("Charity Commissioner", check=_check_charity)
def a_charity(ctx):
    me = ctx.ev["drawer"]
    hot = [u for u in _others(ctx, me) if (ctx.participants()[u].heat or 0) > 0]
    ctx.ask("pick", me, "charity_pick", args={"uid": me}, question="Forgive 1 heat for whom?",
            options=[{"key": str(u), "label": f"{ctx.name(u)} ({ctx.participants()[u].heat} heat)"} for u in hot],
            min=1, max=1)


@step
def charity_pick(ctx, answer, uid):
    target = int(answer[0])
    ctx.ask("choice", uid, "charity_price", args={"uid": uid, "target": target},
            question=f"Your price for forgiving {ctx.name(target)} 1 heat",
            options=[{"key": str(m), "label": "Free" if not m else B._fmt(m)} for m in (0, 30, 60, 90, 120, 180)])


@step
def charity_price(ctx, answer, uid, target):
    price = int(answer)
    ctx.ask("choice", target, "charity_deal", args={"uid": uid, "target": target, "price": price},
            question=f"{ctx.name(uid)} offers to forgive 1 of your heat for {'nothing' if not price else B._fmt(price)}. Deal?",
            options=[{"key": "yes", "label": "Deal"}, {"key": "no", "label": "No deal"}])


@step
def charity_deal(ctx, answer, uid, target, price):
    if answer != "yes":
        ctx.line(f"{ctx.name(target)} turns the deal down.")
        return
    if price:
        _transfer(ctx, target, uid, price)
    ctx.fx([{"type": "heat", "who": "self", "amount": -1}], target)


# --- Doctor: three hospital items -------------------------------------------------------
@ability("Doctor")
def a_doctor(ctx):
    me = ctx.ev["drawer"]
    got = B._give_cards(ctx.state, me, 3, "hospital")
    ctx.line(f"🏥 {ctx.name(me)} draws {len(got)} hospital item{'s' if len(got) != 1 else ''}.", "good")


# --- Chancellor: the Senate from anywhere, at +30 minutes ---------------------------------
def _check_chancellor(room, state, rp):
    return "You already have Senate access this turn." if state["turn"].get("remote_senate") else None


@ability("Chancellor", check=_check_chancellor)
def a_chancellor(ctx):
    me = ctx.ev["drawer"]
    ctx.state["turn"]["remote_senate"] = True
    ctx.state["turn"]["remote_surcharge"] = 30
    ctx.line(f"🏛️ {ctx.name(me)} can use the Senate from anywhere this turn (costs are 30 minutes more).", "good")


# --- Assassin: 20 minutes bleeding on one player, 10 on another --------------------------
@ability("Assassin")
def a_assassin(ctx):
    me = ctx.ev["drawer"]
    ctx.ask("pick", me, "assassin_first", args={"uid": me}, question="Inflict 20 minutes bleeding on whom?",
            options=ctx.options_for(_others(ctx, me)), min=1, max=1)


@step
def assassin_first(ctx, answer, uid):
    first = int(answer[0])
    ctx.fx([{"type": "bleed", "who": "self", "amount": 2}], first)
    rest = [u for u in _others(ctx, uid) if u != first]
    if rest:
        ctx.ask("pick", uid, "assassin_second", args={"uid": uid},
                question="And 10 minutes bleeding on a different player? (or nobody)",
                options=ctx.options_for(rest), min=0, max=1)


@step
def assassin_second(ctx, answer, uid):
    if answer:
        ctx.fx([{"type": "bleed", "who": "self", "amount": 1}], int(answer[0]))


# --- Syndicate Leader: +1 heat, with a movement roll of 4+ ---------------------------------
def _check_syndicate(room, state, rp):
    roll = _move_roll(state)
    if not roll:
        return "Roll for your move first: you need 4 or higher (charms don't count)."
    return None if roll >= 4 else f"Your movement roll was {roll}: you need 4 or higher to sanction a player."


@ability("Syndicate Leader", check=_check_syndicate)
def a_syndicate(ctx):
    me = ctx.ev["drawer"]
    ctx.ask("pick", me, "syndicate_pick", args={"uid": me}, question="Sanction whom with +1 heat?",
            options=ctx.options_for(_others(ctx, me)), min=1, max=1)


@step
def syndicate_pick(ctx, answer, uid):
    ctx.fx([{"type": "heat", "who": "self", "amount": 1}], int(answer[0]))


# --- Pimp: a collectable from another player (their choice) ------------------------------------
def _pimp_targets(room, state, rp):
    return [p.userId for p in room.participants if p.userId != rp.userId and B._alive(p)
            and any(B.cards_mod.split_entry(e)[0] == "collectable" for e in state["hands"].get(str(p.userId), []))]


def _check_pimp(room, state, rp):
    return None if _pimp_targets(room, state, rp) else "Nobody else has a collectable in their hand."


@ability("Pimp", check=_check_pimp)
def a_pimp(ctx):
    me = ctx.ev["drawer"]
    targets = _pimp_targets(ctx.room, ctx.state, ctx.participants()[me])
    ctx.ask("pick", me, "pimp_pick", args={"uid": me}, question="Take a collectable from whom? (they choose which)",
            options=ctx.options_for(targets), min=1, max=1)


@step
def pimp_pick(ctx, answer, uid):
    ctx.push("hand_over", uid=int(answer[0]), count=1, to=uid)


# --- Chaos Creator: roll the black die --------------------------------------------------------
CHAOS = {1: "+5 to the Horseman counter", 2: "Time Virus everyone", 3: "Draw a Scenario card",
         4: "Time Virus a player", 5: "+1 heat to a player", 6: "Steal 30 minutes from every player"}


@ability("Chaos Creator")
def a_chaos(ctx):
    me = ctx.ev["drawer"]
    ctx.roll(me, "Chaos Creator", "chaos_rolled", args={"uid": me}, charm=None)


@step
def chaos_rolled(ctx, r, uid):
    v = r["values"][0]
    ctx.line(f"🌀 {v}: {CHAOS[v]}.")
    if v == 1:
        B._apply_counter(ctx.state, 5, f"🌀 {ctx.name(uid)}'s chaos adds 5")
    elif v == 2:
        ctx.roll(uid, "Time Virus (everyone)", "chaos_virus_all", args={"uid": uid}, charm=None)
    elif v == 3:
        ctx.ev["chain"] = True
    elif v == 4:
        ctx.ask("pick", uid, "chaos_virus_pick", args={"uid": uid}, question="Release the Time Virus on whom?",
                options=ctx.options_for(_others(ctx, uid)), min=1, max=1)
    elif v == 5:
        ctx.ask("pick", uid, "syndicate_pick", args={"uid": uid}, question="+1 heat to whom?",
                options=ctx.options_for(_others(ctx, uid)), min=1, max=1)
    else:
        for u in _others(ctx, uid):
            _transfer(ctx, u, uid, 30)


@step
def chaos_virus_all(ctx, r, uid):
    loss = B.rules.time_virus_minutes(r["values"][0])
    for u in _others(ctx, uid):
        ctx.time(u, -loss)


@step
def chaos_virus_pick(ctx, answer, uid):
    ctx.roll(uid, f"Time Virus on {ctx.name(int(answer[0]))}", "chaos_virus_one", args={"uid": uid, "target": int(answer[0])},
             charm=None)


@step
def chaos_virus_one(ctx, r, uid, target):
    ctx.time(target, -B.rules.time_virus_minutes(r["values"][0]))


# --------------------------------------------------------------------------
# Answers
# --------------------------------------------------------------------------

def _validate(state, room, prompt, user_id, answer):
    """Normalise an answer for this kind of prompt, or return (None, error)."""
    kind = prompt["kind"]
    if kind == "roll":
        return True, None
    if kind == "choice":
        keys = [o["key"] for o in prompt["options"]]
        return (answer, None) if answer in keys else (None, "Pick one of the options.")
    if kind == "pick":
        keys = [o["key"] for o in prompt["options"]]
        picked = [str(a) for a in (answer or [])]
        if len(set(picked)) != len(picked) or not all(k in keys for k in picked):
            return None, "Pick from the list."
        if not prompt.get("min", 0) <= len(picked) <= prompt.get("max", len(keys)):
            return None, f"Pick between {prompt.get('min', 0)} and {prompt.get('max', len(keys))}."
        return picked, None
    if kind == "cards":
        cands = prompt["candidates"]
        if answer == "random":
            return random.sample(cands, min(prompt["count"], len(cands))), None
        picked = list(answer or [])
        if len(picked) != min(prompt["count"], len(cands)) or len(set(picked)) != len(picked) or \
                not all(c in cands for c in picked):
            return None, f"Choose {prompt['count']} of your collectables."
        return picked, None
    if kind == "allocate":
        try:
            alloc = {str(k): int(v) for k, v in (answer or {}).items() if int(v)}
        except (TypeError, ValueError):
            return None, "Enter amounts."
        allowed = {str(u) for u in prompt["recipients"]}
        if any(k not in allowed or v < 0 or v % prompt["step"] for k, v in alloc.items()):
            return None, "Split it between the players listed, in steps of the lot size."
        if sum(alloc.values()) != prompt["total"]:
            return None, f"Share out exactly {B._fmt(prompt['total'])}."
        return alloc, None
    if kind == "job":
        keys = [o["key"] for o in prompt["options"]]
        answer = str(answer)
        if answer == "keep" and prompt.get("keep"):
            return answer, None
        return (answer, None) if answer in keys else (None, "Choose one of the jobs this card offers.")
    if kind == "tile":
        try:
            t = int(answer)
        except (TypeError, ValueError):
            return None, "Choose a tile."
        return (t, None) if 0 <= t < len(rules.TILES) else (None, "Choose a tile.")
    if kind == "buy":
        try:
            counts = {k: int(v) for k, v in (answer or {}).items() if int(v) > 0}
        except (TypeError, ValueError):
            return None, "Choose what to buy."
        if any(k not in {i["key"] for i in prompt["items"]} for k in counts) or sum(counts.values()) > prompt["max"]:
            return None, f"Choose up to {prompt['max']} items."
        return counts, None
    return None, "Unknown question."


def answer_prompt(room, state, user_id, prompt_id, answer, is_admin, on_behalf=False):
    """Returns an error message, or None when the answer was taken."""
    ev = state.get("event")
    prompt = ev and ev.get("prompt")
    if not prompt or prompt.get("id") != prompt_id:
        return "That question has already been answered."

    if prompt["kind"] == "vote":
        voters = prompt["voters"]
        secret = state.setdefault("event_secret", {"votes": {}})
        votes = secret["votes"]
        if answer == "__close__":
            if not is_admin:
                return "Only the admin can close the vote."
        else:
            if user_id not in voters:
                return "You don't have a vote here."
            if str(user_id) in votes:
                return "You've already voted."
            keys = [o["key"] for o in prompt["options"]]
            if answer not in keys or (prompt.get("exclude_self") and answer == str(user_id)):
                return "Pick one of the options."
            votes[str(user_id)] = answer
            prompt["voted"] = sorted(int(k) for k in votes)
            if len(votes) < len(voters):
                return None
        ev["prompt"] = None
        state.pop("event_secret", None)
        ctx = Ctx(room, state)
        ctx.push(prompt["on"]["fn"], answer=votes, **prompt["on"]["args"])
        run(room, state, ctx)
        return None

    if prompt["user_id"] != user_id and not is_admin:
        return f"Waiting for {B._name(B._participants(room).get(prompt['user_id']))}."
    value, error = _validate(state, room, prompt, user_id, answer)
    if error:
        return error
    ev["prompt"] = None
    ev["vars"]["_answering"] = prompt["user_id"]
    if prompt["user_id"] != user_id:
        B._log(state, f"🛠️ The admin answered for {B._name(B._participants(room).get(prompt['user_id']))}.", kind="admin")
    ctx = Ctx(room, state)
    ctx.push(prompt["on"]["fn"], answer=value, **prompt["on"]["args"])
    run(room, state, ctx)
    return None


# --------------------------------------------------------------------------
# Sockets
# --------------------------------------------------------------------------

def _finish_request(room, state, ctx):
    B._save(room, state)
    B._broadcast(room, state)
    if ctx is None or ctx.room_changed:
        B._emit_room_state(room)


@socketio.on("boardEventAnswer")
@jwt_required()
def board_event_answer(data=None):
    ctx_ = B._context()
    if not ctx_:
        return
    user_id, rp, room = ctx_
    payload = B._parse(data)
    with B._room_locks[room.id]:
        state = B._load(room)
        error = answer_prompt(room, state, user_id, B._int_or_none(payload.get("prompt_id")),
                              payload.get("answer"), B._is_admin(room, user_id))
        if error:
            emit("error", {"message": error})
            return
        _finish_request(room, state, None)


@socketio.on("boardEventSkip")
@jwt_required()
def board_event_skip(data=None):
    """Admin: skip the question being asked (or stop the card altogether with {stop: true})."""
    ctx_ = B._context()
    if not ctx_:
        return
    user_id, rp, room = ctx_
    if not B._is_admin(room, user_id):
        emit("error", {"message": "Only the room admin can skip a step."})
        return
    stop = bool(B._parse(data).get("stop"))
    with B._room_locks[room.id]:
        state = B._load(room)
        ev = state.get("event")
        if not active(state):
            emit("error", {"message": "No scenario card is in play."})
            return
        if stop:
            cancel(state, "admin")
            B._log(state, f"🛠️ The admin stopped “{ev['title']}”.", kind="admin")
        else:
            ev["prompt"] = None
            state.pop("event_secret", None)
            B._log(state, f"🛠️ The admin skipped a step of “{ev['title']}”.", kind="admin")
            run(room, state)
        _finish_request(room, state, None)


@socketio.on("boardEventWithdraw")
@jwt_required()
def board_event_withdraw(data=None):
    """Take back a card you played, while you're still choosing what it does: it stays in your hand."""
    ctx_ = B._context()
    if not ctx_:
        return
    user_id, rp, room = ctx_
    with B._room_locks[room.id]:
        state = B._load(room)
        ev = state.get("event")
        if not active(state) or not ev.get("entry") or ev.get("drawer") != user_id:
            emit("error", {"message": "You don't have a card in play to take back."})
            return
        prompt = ev.get("prompt")
        if not prompt or prompt.get("user_id") != user_id:
            emit("error", {"message": "Others are answering this card now, so it can't be taken back."})
            return
        cancel(state, "withdrawn")
        B._log(state, f"↩️ {B._name(rp)} took back “{ev['title']}”.", kind="card", user_id=user_id)
        _finish_request(room, state, None)


@socketio.on("boardPayDebt")
@jwt_required()
def board_pay_debt(data=None):
    """Pay 1–3 hours off a card debt (RNLI) on your turn."""
    ctx_ = B._context()
    if not ctx_:
        return
    user_id, rp, room = ctx_
    minutes = B._int_or_none(B._parse(data).get("minutes")) or 0
    with B._room_locks[room.id]:
        state = B._load(room)
        debt = state.get("debts", {}).get(str(user_id))
        if not debt:
            emit("error", {"message": "You don't owe anything."})
            return
        if B._current_turn_user(state) != user_id:
            emit("error", {"message": "Pay your debt on your turn."})
            return
        if debt.get("paid_seq") == state.get("turn_seq"):
            emit("error", {"message": "You've already paid this turn."})
            return
        least = min(60, debt["minutes"])
        if not least <= minutes <= 180 or minutes > debt["minutes"]:
            emit("error", {"message": "Pay between 1 and 3 hours (or what's left)."})
            return
        if B._minutes_left(rp) < minutes:
            emit("error", {"message": "Not enough time."})
            return
        B.repay_debt(state, rp, minutes)
        B._save(room, state)
    B._emit_clock(room, rp)
    B._broadcast(room, state)
    B._emit_room_state(room)


@socketio.on("boardDonateTax")
@jwt_required()
def board_donate_tax(data=None):
    """Donate time to the state to lift Income Tax (24 hours in all, from anyone)."""
    ctx_ = B._context()
    if not ctx_:
        return
    user_id, rp, room = ctx_
    minutes = B._int_or_none(B._parse(data).get("minutes")) or 0
    with B._room_locks[room.id]:
        state = B._load(room)
        tax = state.get("income_tax")
        if not tax:
            emit("error", {"message": "Income Tax isn't in force."})
            return
        if minutes <= 0 or minutes % 30:
            emit("error", {"message": "Donate in steps of 30 minutes."})
            return
        minutes = min(minutes, tax["goal"] - tax["donated"])
        if B._minutes_left(rp) < minutes:
            emit("error", {"message": "Not enough time."})
            return
        B._set_minutes(rp, B._minutes_left(rp) - minutes)
        db.session.commit()
        tax["donated"] += minutes
        B._log(state, f"💷 {B._name(rp)} donated {B._fmt(minutes)} to the state "
                      f"({B._fmt(tax['donated'])} of 24h).", kind="money", user_id=user_id)
        if tax["donated"] >= tax["goal"]:
            state.pop("income_tax")
            cards_mod.discard(state["decks"], "scenario", tax["card"])
            B._log(state, "💷 24 hours have been donated: Income Tax is lifted.", kind="card", announce=True)
        B._save(room, state)
    B._emit_clock(room, rp)
    B._broadcast(room, state)
    B._emit_room_state(room)
