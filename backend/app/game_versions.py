"""
Game versions: the card sets a room can be played with.

* Versions live in the `game_version` table, so a new one can be uploaded
  (POST /api/game-versions, or `python manage_cards.py import ...`) while
  games are running - no restart needed.
* Versions shipped with the code sit in data_collections/game_versions/*.json
  and are synced into the table on startup (bundled versions are refreshed
  from their file; uploaded ones are never touched).
* Each room stores the key of the version it was created with, and the board
  reads its decks from that version only. Publishing a new version therefore
  never changes a game in progress.
"""
import glob
import json
import os
from datetime import datetime

from app import db
from app.models import GameVersion
from app.websocket import board_cards as cards_mod

BUNDLED_DIR = os.path.join(os.path.dirname(__file__), "data_collections", "game_versions")
# Files in BUNDLED_DIR that aren't card sets
NOT_VERSIONS = {"automation.json"}
DECKS = cards_mod.DECK_NAMES

# key -> (row id, created_at, parsed cards); refreshed whenever a version is saved
_cache = {}


def _counts(cards: dict) -> dict:
    return {d: sum(int(c.get("copies", 1) or 1) for c in cards.get(d, [])) for d in DECKS}


def _summary(v: GameVersion) -> dict:
    cards = json.loads(v.cards or "{}")
    return {
        "key": v.key,
        "name": v.name,
        "notes": v.notes or "",
        "source": v.source,
        "is_default": bool(v.is_default),
        "created_at": v.created_at.isoformat() + "Z" if v.created_at else None,
        "created_by": v.created_by,
        "counts": _counts(cards),
        "examples": sum(1 for d in DECKS for c in cards.get(d, []) if c.get("example")),
    }


def list_versions() -> list:
    rows = GameVersion.query.order_by(GameVersion.created_at.desc()).all()
    return [_summary(v) for v in rows]


def get_version(key) -> GameVersion:
    return GameVersion.query.filter_by(key=str(key)).first() if key else None


def default_key():
    v = GameVersion.query.filter_by(is_default=True).first() or \
        GameVersion.query.order_by(GameVersion.created_at.desc()).first()
    return v.key if v else None


def resolve_key(requested=None):
    """The version a new room should use: the one asked for if it exists, else the default."""
    if requested and get_version(requested):
        return str(requested)
    return default_key()


def get_cards(key) -> dict:
    """Parsed decks ({deck: {card id: card}}) for a version; empty decks if it doesn't exist."""
    v = get_version(key)
    if not v:
        return {d: {} for d in DECKS}
    hit = _cache.get(v.key)
    stamp = (v.id, v.created_at, len(v.cards or ""), hash(v.cards))
    if hit and hit[0] == stamp:
        return hit[1]
    parsed = cards_mod.parse_cards(json.loads(v.cards or "{}"))
    _cache[v.key] = (stamp, parsed)
    return parsed


def version_doc(key) -> dict:
    v = get_version(key)
    if not v:
        return None
    return {"key": v.key, "name": v.name, "notes": v.notes or "", **json.loads(v.cards or "{}")}


def validate_doc(doc: dict) -> list:
    """Problems that would stop a version from being playable."""
    problems = []
    for d in DECKS:
        seen = set()
        for c in doc.get(d) or []:
            if not c.get("id") or not c.get("title"):
                problems.append(f"A {d} card is missing its id or title.")
            elif c["id"] in seen:
                problems.append(f"Duplicate {d} card id “{c['id']}”.")
            seen.add(c.get("id"))
            for e in cards_mod.walk_effects((c.get("effects") or []) + (c.get("reward") or [])):
                if e.get("type") not in cards_mod.EFFECT_TYPES:
                    problems.append(f"{d} “{c.get('title')}”: unknown effect “{e.get('type')}”.")
                if not cards_mod.is_selector(e.get("who", "self")):
                    problems.append(f"{d} “{c.get('title')}”: unknown player selector “{e.get('who')}”.")
    return problems


def save_version(doc: dict, *, source="upload", created_by=None, make_default=False, replace=False) -> GameVersion:
    """
    Store a version. An existing key is only overwritten with replace=True
    (rooms already playing it keep their shuffled decks, but new draws would
    use the new card text - so normally publish a new key instead).
    """
    problems = validate_doc(doc)
    if problems:
        raise ValueError("; ".join(problems[:5]))
    cards = {d: list(doc.get(d) or []) for d in DECKS}
    if doc.get("reference"):
        cards["reference"] = doc["reference"]
    v = get_version(doc["key"])
    if v and not replace:
        raise ValueError(f"Version {doc['key']} already exists. Use a new version number.")
    if not v:
        v = GameVersion(key=str(doc["key"]))
        db.session.add(v)
    v.name = doc.get("name") or f"Gerry's Game v{doc['key']}"
    v.notes = doc.get("notes") or ""
    v.cards = json.dumps(cards, ensure_ascii=False)
    v.source = source
    v.created_by = created_by
    v.created_at = datetime.utcnow()
    if make_default:
        GameVersion.query.filter(GameVersion.key != v.key).update({"is_default": False})
        v.is_default = True
    db.session.commit()
    _cache.pop(v.key, None)
    return v


def set_default(key) -> bool:
    v = get_version(key)
    if not v:
        return False
    GameVersion.query.update({"is_default": False})
    v.is_default = True
    db.session.commit()
    return True


def bundled_docs() -> list:
    docs = []
    for path in sorted(glob.glob(os.path.join(BUNDLED_DIR, "*.json"))):
        if os.path.basename(path) in NOT_VERSIONS:
            continue
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        doc.setdefault("key", os.path.splitext(os.path.basename(path))[0])
        docs.append(doc)
    return docs


def sync_bundled():
    """Load the versions shipped in data_collections/game_versions into the table."""
    for doc in bundled_docs():
        v = get_version(doc["key"])
        stored = {d: list(doc.get(d) or []) for d in DECKS}
        if doc.get("reference"):
            stored["reference"] = doc["reference"]
        cards = json.dumps(stored, ensure_ascii=False)
        if v is None:
            save_version(doc, source="bundled", make_default=bool(doc.get("default")))
            print(f"[game_versions] added bundled version {doc['key']}")
        elif v.source == "bundled" and (v.cards != cards or v.name != doc.get("name") or (v.notes or "") != doc.get("notes", "")):
            save_version(doc, source="bundled", replace=True)
            print(f"[game_versions] refreshed bundled version {doc['key']}")
    if not GameVersion.query.filter_by(is_default=True).first():
        key = default_key()
        if key:
            set_default(key)
