"""
Turn a card spreadsheet into a game version, and back again.

A game version is one complete set of cards (Scenario, Assignment Slip and
Collectable decks) plus patch notes. Versions are stored in the database
(see game_versions.py) so new ones can be uploaded while games are running;
each room plays the version it was created with.

The spreadsheet
---------------
One sheet per deck. Sheet names are matched loosely: anything containing
"scen" is the Scenario deck, "assign" the Assignment Slips, "collect" the
Collectables, "job" the Job Opportunities, "promot" the Promotion cards and
"hospital"/"bandage" the Hospital items. Headers are case-insensitive and
these spellings all work:

    ID          id, card id, code                    (optional - made from the title)
    Title       title, name, card, card name
    Text        text, description, card text, rules
    Copies      copies, count, qty, quantity, number, amount   (default 1)
    Equip       equip, equippable, permanent         (yes/true/1/x)
    Effects     effects, automation, auto            (what the server does)
    Reward      reward, reward effects               (assignment slips)

Everything except Title and Text is optional. A card with no Effects is
still drawn and shown to everyone - the table resolves it by hand.

Effects syntax
--------------
One clause per line, or separated by ";". Times accept 30, 30m, 1h, 1.5h.

    time <who> <+/-time>          everyone/others/self... gains or loses time
    roll <who> <+/-time>          roll the die, x that much per pip
    steal <who> <time>            take time from them
    give <who> <time>             give them your time
    bleed <who> <+/-n>            bleeding effect counters
    heat <who> <+/-n>
    move <start|job_centre|senate|hospital|black_market|tile number>
    jail <who>
    skip <who>                    they miss their next turn
    draw <n> [deck]               draw n cards (collectable by default; or job, promotion, hospital)
    takediscard <n>               may take n cards of their choice from the collectable discard pile
    note <text>                   shown on the card, resolved by hand

<who> is one of: self, all, others, choose, random, richest, poorest.
A JSON list in the cell is also accepted as-is.

This module is pure Python (zipfile + ElementTree), so it needs no extra
packages on the server.
"""
import csv
import io
import json
import os
import re
import zipfile
from xml.etree import ElementTree as ET

DECKS = ("scenario", "assignment", "collectable", "job", "promotion", "hospital", "shortcut", "oppression")
DRAW_DECKS = {"collectable": "collectable", "collectables": "collectable", "job": "job", "jobs": "job",
              "promotion": "promotion", "promotions": "promotion", "hospital": "hospital",
              "bandage": "hospital", "bandages": "hospital", "shortcut": "shortcut", "shortcuts": "shortcut"}
SELECTORS = ("self", "all", "others", "choose", "random", "richest", "poorest")

HEADER_ALIASES = {
    "id": ("id", "card id", "code", "card code"),
    "title": ("title", "name", "card", "card name", "card title"),
    "text": ("text", "description", "card text", "rules", "effect text", "details"),
    "copies": ("copies", "count", "qty", "quantity", "number", "amount", "no.", "no", "#"),
    "equip": ("equip", "equippable", "permanent", "equipped"),
    "effects": ("effects", "effect", "automation", "auto", "server effects"),
    "reward": ("reward", "rewards", "reward effects"),
    "start_in_discard": ("start in discard", "starts in discard", "start on discard pile", "in discard at start"),
}

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


class ImportError_(ValueError):
    """The spreadsheet can't be turned into a game version."""


# --------------------------------------------------------------------------
# Reading spreadsheets
# --------------------------------------------------------------------------

def _col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx(data: bytes) -> dict:
    """{sheet name: [[cell text, ...], ...]} from .xlsx bytes."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        raise ImportError_("That file isn't a valid .xlsx spreadsheet.") from e

    shared = []
    if "xl/sharedStrings.xml" in zf.namelist():
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        for si in root.findall("m:si", _NS):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t")))

    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    targets = {r.get("Id"): r.get("Target") for r in rels}

    sheets = {}
    for sheet in wb.find("m:sheets", _NS):
        target = targets.get(sheet.get(f"{_REL_NS}id"), "")
        path = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
        root = ET.fromstring(zf.read(path))
        rows = []
        for row in root.iter(f"{{{_NS['m']}}}row"):
            cells = {}
            for c in row.findall("m:c", _NS):
                kind = c.get("t")
                if kind == "inlineStr":
                    value = "".join(t.text or "" for t in c.iter(f"{{{_NS['m']}}}t"))
                else:
                    v = c.find("m:v", _NS)
                    value = v.text if v is not None and v.text is not None else ""
                    if kind == "s" and value != "":
                        value = shared[int(value)]
                    elif kind == "b":
                        value = "TRUE" if value == "1" else "FALSE"
                    elif kind is None and re.fullmatch(r"-?\d+\.0+", value or ""):
                        value = value.split(".")[0]
                cells[_col_index(c.get("r"))] = value
            if cells:
                width = max(cells) + 1
                rows.append([cells.get(i, "") for i in range(width)])
        sheets[sheet.get("name")] = rows
    return sheets


def read_csv(text: str, sheet_name: str) -> dict:
    return {sheet_name: [row for row in csv.reader(io.StringIO(text))]}


def read_any(filename: str, data: bytes) -> dict:
    name = filename.lower()
    if name.endswith(".xlsx"):
        return read_xlsx(data)
    if name.endswith(".csv"):
        return read_csv(data.decode("utf-8-sig"), filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
    if name.endswith(".json"):
        doc = json.loads(data.decode("utf-8-sig"))
        return {"__json__": doc}
    raise ImportError_("Upload a .xlsx (Excel), .csv or .json file.")


# --------------------------------------------------------------------------
# Effects syntax
# --------------------------------------------------------------------------

def parse_minutes(token: str) -> int:
    """'30', '30m', '-1h', '+1.5h', '2h30' -> minutes."""
    t = token.strip().lower().replace(" ", "")
    m = re.fullmatch(r"([+-]?)(\d+(?:\.\d+)?)h(?:(\d+)m?)?", t)
    if m:
        sign = -1 if m.group(1) == "-" else 1
        return sign * int(round(float(m.group(2)) * 60 + int(m.group(3) or 0)))
    m = re.fullmatch(r"([+-]?)(\d+)(?:m|min|mins|minutes)?", t)
    if m:
        return (-1 if m.group(1) == "-" else 1) * int(m.group(2))
    raise ValueError(f"'{token}' isn't a time (try 30, 30m, 1h or 1.5h)")


def _who(token: str) -> str:
    t = token.strip().lower()
    aliases = {"everyone": "all", "me": "self", "you": "self", "target": "choose", "chosen": "choose",
               "other": "others", "opponents": "others"}
    t = aliases.get(t, t)
    if t not in SELECTORS:
        raise ValueError(f"'{token}' isn't a player selector ({', '.join(SELECTORS)})")
    return t


def parse_effects(cell: str):
    """Effects cell -> (effects list, warnings)."""
    cell = (cell or "").strip()
    if not cell:
        return [], []
    if cell.startswith("["):
        try:
            effects = json.loads(cell)
            if isinstance(effects, list):
                return effects, []
        except json.JSONDecodeError as e:
            return [{"type": "note", "text": cell}], [f"Effects JSON didn't parse ({e}); kept as a note."]

    effects, warnings = [], []
    for raw in re.split(r"[;\n]+", cell):
        clause = raw.strip()
        if not clause:
            continue
        parts = clause.split()
        verb = parts[0].lower()
        args = parts[1:]
        try:
            if verb == "note":
                effects.append({"type": "note", "text": clause[4:].strip()})
            elif verb in ("time", "roll"):
                if len(args) != 2:
                    raise ValueError(f"'{verb}' needs a player and a time, e.g. '{verb} others -30'")
                e = {"who": _who(args[0])}
                if verb == "time":
                    e.update(type="time", minutes=parse_minutes(args[1]))
                else:
                    e.update(type="time_roll", per_pip=parse_minutes(args[1]), dice=1)
                effects.append(e)
            elif verb in ("steal", "give"):
                if len(args) != 2:
                    raise ValueError(f"'{verb}' needs a player and a time, e.g. '{verb} choose 1h'")
                effects.append({"type": verb, "who": _who(args[0]), "minutes": abs(parse_minutes(args[1]))})
            elif verb in ("bleed", "heat"):
                if len(args) != 2:
                    raise ValueError(f"'{verb}' needs a player and an amount, e.g. '{verb} self +1'")
                effects.append({"type": verb, "who": _who(args[0]), "amount": int(args[1])})
            elif verb == "move":
                if len(args) != 1:
                    raise ValueError("'move' needs a place, e.g. 'move start'")
                to = args[0].lower()
                effects.append({"type": "move", "to": int(to) if to.isdigit() else to})
            elif verb in ("jail", "skip"):
                effects.append({"type": "jail" if verb == "jail" else "skip_turn",
                                "who": _who(args[0]) if args else "self"})
            elif verb == "draw":
                deck = DRAW_DECKS.get(args[1].lower()) if len(args) > 1 else "collectable"
                if not deck:
                    raise ValueError(f"'{args[1]}' isn't a deck you can draw from (collectable, job, promotion, hospital)")
                effects.append({"type": "draw", "deck": deck, "count": int(args[0]) if args else 1})
            elif verb in ("takediscard", "pickdiscard", "take_discard"):
                effects.append({"type": "take_discard", "count": int(args[0]) if args else 1})
            else:
                raise ValueError(f"unknown effect '{verb}'")
        except ValueError as e:
            warnings.append(f"“{clause}”: {e}; kept as a note.")
            effects.append({"type": "note", "text": clause})
    return effects, warnings


def format_effects(effects) -> str:
    """The reverse of parse_effects, for exporting back to a spreadsheet."""
    out = []
    for e in effects or []:
        t = e.get("type")
        who = e.get("who", "self")
        if t == "time":
            out.append(f"time {who} {e.get('minutes', 0):+d}")
        elif t == "time_roll":
            out.append(f"roll {who} {e.get('per_pip', 0):+d}")
        elif t in ("steal", "give"):
            out.append(f"{t} {who} {e.get('minutes', 0)}")
        elif t in ("bleed", "heat"):
            out.append(f"{t} {who} {e.get('amount', 0):+d}")
        elif t == "move":
            out.append(f"move {e.get('to')}")
        elif t == "jail":
            out.append(f"jail {who}")
        elif t == "skip_turn":
            out.append(f"skip {who}")
        elif t == "draw":
            deck = e.get("deck", "collectable")
            out.append(f"draw {e.get('count', 1)}" + ("" if deck == "collectable" else f" {deck}"))
        elif t == "take_discard":
            out.append(f"takediscard {e.get('count', 1)}")
        elif t == "note":
            out.append(f"note {e.get('text', '')}")
    return "; ".join(out)


# --------------------------------------------------------------------------
# Sheets -> cards
# --------------------------------------------------------------------------

def deck_for_sheet(name: str):
    n = name.lower()
    # Most specific first: "Hospital Items" must not be read as collectables
    if "hospital" in n or "bandage" in n:
        return "hospital"
    if "job" in n:
        return "job"
    if "shortcut" in n:
        return "shortcut"
    if "promot" in n:
        return "promotion"
    if "scen" in n:
        return "scenario"
    if "assign" in n or "slip" in n:
        return "assignment"
    if "collect" in n or "item" in n:
        return "collectable"
    return None


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "card"


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in ("y", "yes", "true", "1", "x", "✓", "equip")


def _header_map(header_row):
    found = {}
    for i, cell in enumerate(header_row):
        h = str(cell).strip().lower()
        for key, aliases in HEADER_ALIASES.items():
            if h in aliases and key not in found:
                found[key] = i
    return found


def sheets_to_cards(sheets: dict):
    """
    {sheet: rows} -> ({deck: [card, ...]}, warnings).
    Raises ImportError_ if no deck could be found at all.
    """
    if "__json__" in sheets:
        doc = sheets["__json__"]
        return {d: list(doc.get(d) or []) for d in DECKS}, []

    decks = {d: [] for d in DECKS}
    warnings = []
    for sheet_name, rows in sheets.items():
        deck = deck_for_sheet(sheet_name)
        if not deck:
            warnings.append(f"Sheet “{sheet_name}” was skipped (its name doesn't say Scenario, Assignment, "
                            "Collectable, Job, Promotion or Hospital).")
            continue
        # The header is the first row that has a title column
        header_at, cols = None, {}
        for i, row in enumerate(rows[:10]):
            cols = _header_map(row)
            if "title" in cols:
                header_at = i
                break
        if header_at is None:
            warnings.append(f"Sheet “{sheet_name}” has no Title/Name column, so it was skipped.")
            continue

        used_ids = {c["id"] for c in decks[deck]}
        for n, row in enumerate(rows[header_at + 1:], start=header_at + 2):
            def get(key):
                i = cols.get(key)
                return str(row[i]).strip() if i is not None and i < len(row) else ""

            title = get("title")
            if not title:
                continue
            where = f"{sheet_name} row {n}"
            card_id = get("id") or f"{deck[:2]}-{_slug(title)}"
            base, k = card_id, 2
            while card_id in used_ids:
                card_id, k = f"{base}-{k}", k + 1
            used_ids.add(card_id)

            copies_raw = get("copies") or "1"
            try:
                copies = max(1, int(float(copies_raw)))
            except ValueError:
                warnings.append(f"{where}: copies “{copies_raw}” isn't a number; using 1.")
                copies = 1

            card = {"id": card_id, "title": title, "text": get("text"), "copies": copies}
            if _truthy(get("equip")):
                card["equip"] = True
            if _truthy(get("start_in_discard")):
                card["start_in_discard"] = True
            # Assignment slips use their Reward column (or Effects, if that's what it's called)
            source = (get("reward") or get("effects")) if deck == "assignment" else get("effects")
            effects, w = parse_effects(source)
            warnings += [f"{where}: {x}" for x in w]
            if effects:
                card["reward" if deck == "assignment" else "effects"] = effects
            decks[deck].append(card)

    if not any(decks.values()):
        raise ImportError_(
            "No cards found. Name the sheets Scenario / Assignments / Collectables and give each a Title column."
        )
    return decks, warnings


def build_version(sheets: dict, *, key: str, name: str = "", notes: str = ""):
    """A complete version document from a spreadsheet, plus import warnings."""
    key = str(key or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,31}", key):
        raise ImportError_("The version needs a short key such as 4.27 or 4.28-beta (letters, numbers, . _ -).")
    reference = {}
    if is_card_workbook(sheets):
        decks, reference, summary, warnings = parse_card_workbook(sheets)
        notes = notes or summary
    else:
        decks, warnings = sheets_to_cards(sheets)
    for deck in DECKS:
        if not decks[deck]:
            warnings.append(f"No {deck} cards in this upload; that deck will be empty.")
    doc = {"key": key, "name": name or f"Gerry's Game v{key}", "notes": notes or "", **decks}
    if reference:
        doc["reference"] = reference
    return doc, warnings


# --------------------------------------------------------------------------
# Cards -> spreadsheet (so the current cards can be edited in Excel)
# --------------------------------------------------------------------------

def _xml_escape(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _col_letter(i: int) -> str:
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def write_xlsx(sheets: dict) -> bytes:
    """Minimal .xlsx writer: {sheet name: [[cell, ...], ...]} -> bytes (text cells, bold header)."""
    buf = io.BytesIO()
    names = list(sheets)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            + "".join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                      for i in range(len(names)))
            + "</Types>"))
        z.writestr("_rels/.rels", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>"))
        z.writestr("xl/workbook.xml", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
            + "".join(f'<sheet name="{_xml_escape(n)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, n in enumerate(names))
            + "</sheets></workbook>"))
        z.writestr("xl/_rels/workbook.xml.rels", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>'
                      for i in range(len(names)))
            + f'<Relationship Id="rId{len(names) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>"))
        z.writestr("xl/styles.xml", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
            '<cellXfs count="3"><xf/><xf fontId="1" applyFont="1"/><xf applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf></cellXfs>'
            "</styleSheet>"))
        for i, name in enumerate(names):
            rows = sheets[name]
            xml_rows = []
            for r, row in enumerate(rows):
                style = 1 if r == 0 else 2
                cells = "".join(
                    f'<c r="{_col_letter(c)}{r + 1}" t="inlineStr" s="{style}"><is><t xml:space="preserve">{_xml_escape(v)}</t></is></c>'
                    for c, v in enumerate(row) if v not in (None, "")
                )
                xml_rows.append(f'<row r="{r + 1}">{cells}</row>')
            widths = '<cols><col min="1" max="1" width="22" customWidth="1"/><col min="2" max="2" width="26" customWidth="1"/>' \
                     '<col min="3" max="3" width="60" customWidth="1"/><col min="4" max="5" width="9" customWidth="1"/>' \
                     '<col min="6" max="6" width="40" customWidth="1"/></cols>'
            z.writestr(f"xl/worksheets/sheet{i + 1}.xml", (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'{widths}<sheetData>{"".join(xml_rows)}</sheetData></worksheet>'))
    return buf.getvalue()


SHEET_TITLES = {"scenario": "Scenario Cards", "assignment": "Assignment Slips", "collectable": "Collectables",
                "job": "Job Opportunities", "promotion": "Promotion Cards", "hospital": "Hospital Items",
                "shortcut": "Shortcuts", "oppression": "Oppressions"}


def version_to_sheets(doc: dict) -> dict:
    sheets = {}
    for deck in DECKS:
        effects_col = "Reward" if deck == "assignment" else "Effects"
        rows = [["ID", "Title", "Text", "Copies", "Equip", effects_col, "Start in discard"]]
        for c in doc.get(deck) or []:
            effects = c.get("reward") if deck == "assignment" else c.get("effects")
            rows.append([c.get("id", ""), c.get("title", ""), c.get("text", ""), str(c.get("copies", 1)),
                         "yes" if c.get("equip") else "", format_effects(effects),
                         "yes" if c.get("start_in_discard") else ""])
        sheets[SHEET_TITLES[deck]] = rows
    return sheets


# --------------------------------------------------------------------------
# The full card workbook (Gerrys_Game_Cards.xlsx)
# --------------------------------------------------------------------------
# One tab per category, laid out like the game file:
#   Collectables      Name | Deck | Quantity | Contraband | Reusable | Effect
#   Assignment Slips  Objective | Uses / relates to | Reward (hours) | Quantity
#   Scenario Cards    Card | Type | Special condition | Card text
#   Jobs, Titles, Governments, Oppressions, Summary   (kept as reference data)
# Rows after a "Total" row, and note rows, are ignored. The automatic effects
# come from automation.json (matched by card name), not from the workbook.

AUTOMATION_PATH = os.path.join(os.path.dirname(__file__), "data_collections", "game_versions", "automation.json")
REFERENCE_SHEETS = ("jobs", "titles", "governments", "oppressions")


def _minutes_in(text: str) -> int:
    m = re.search(r"(\d+)\s*(?:min|mins|minutes)", text or "")
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:h|hour)", text or "")
    return int(round(float(m.group(1)) * 60)) if m else 0


def oppression_effects(effect_type: str, amount: str) -> list:
    """What an oppression card does to the player it's used on (who: choose)."""
    t = norm_title(effect_type)
    mins = _minutes_in(amount)
    if t == "steal time" and mins:
        return [{"type": "steal", "who": "choose", "minutes": mins}]
    if t == "bleeding" and mins:
        return [{"type": "bleed", "who": "choose", "amount": max(1, mins // 10)}]
    if t == "time virus":
        return [{"type": "time_roll", "who": "choose", "per_pip": -30, "dice": 1}]
    if t == "heat":
        return [{"type": "heat", "who": "choose", "amount": 1}]
    if t == "demote":
        return [{"type": "demote", "who": "choose"}]
    if t == "steal collectable":
        return [{"type": "note", "text": "The player gives you a collectable of their choice (use Give in their cards)."}]
    if t == "sacrifice item":
        return [{"type": "note", "text": "The player sacrifices an item of their choice: a job, a title level, a collectable or a completed slip."}]
    return []
DECK_PREFIX = {"scenario": "scn", "assignment": "asg", "collectable": "col", "job": "job",
               "promotion": "pro", "hospital": "hos", "shortcut": "sct", "oppression": "opp"}


def norm_title(text: str) -> str:
    """Card names for matching: 'Gerry’s Slot Machine' == 'gerrys slot machine', 'Strike!' == 'strike'."""
    t = str(text or "").lower().replace("’", "").replace("'", "").replace("‘", "")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return t.strip()


def load_automation(path: str = AUTOMATION_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    out = {"defaults": raw.get("defaults") or {}}
    for section in ("collectable", "scenario", "assignment", "oppression"):
        out[section] = {norm_title(k): v for k, v in (raw.get(section) or {}).items()}
    return out


def _sheet(sheets: dict, *names):
    for name, rows in sheets.items():
        if name.strip().lower() in names:
            return name, rows
    return None, None


def _columns(header, wanted: dict) -> dict:
    """{key: column index} for headers that start with any of the wanted prefixes."""
    cols = {}
    for i, cell in enumerate(header):
        h = str(cell).strip().lower()
        for key, prefixes in wanted.items():
            if key not in cols and any(h.startswith(p) for p in prefixes):
                cols[key] = i
    return cols


def _cell(row, cols, key):
    i = cols.get(key)
    return str(row[i]).strip() if i is not None and i < len(row) else ""


def is_card_workbook(sheets: dict) -> bool:
    _, rows = _sheet(sheets, "collectables")
    if rows:
        cols = _columns(rows[0], {"deck": ("deck",), "name": ("name",)})
        if "deck" in cols and "name" in cols:
            return True
    _, rows = _sheet(sheets, "scenario cards")
    return bool(rows) and "text" in _columns(rows[0], {"text": ("card text",)})


def _apply_automation(card: dict, auto: dict, effects_key: str):
    if not auto:
        return
    if auto.get(effects_key) or auto.get("effects"):
        card[effects_key] = list(auto.get(effects_key) or auto.get("effects"))
    if auto.get("equip"):
        card["equip"] = True


def _hand_deck_for(name: str, deck_cell: str) -> str:
    n = norm_title(name)
    d = deck_cell.lower()
    if n == "promotion":
        return "promotion"
    if n == "job opportunity":
        return "job"
    if n == "shortcut":
        return "shortcut"
    if "hospital" in d and "collect" not in d:
        return "hospital"
    return "collectable"


def parse_card_workbook(sheets: dict, automation: dict = None):
    """The full card workbook -> ({deck: [card]}, reference data, summary notes, warnings)."""
    automation = automation if automation is not None else load_automation()
    defaults = (automation.get("defaults") or {}).get("copies") or {}
    decks = {d: [] for d in DECKS}
    warnings = []
    used = set()

    def new_id(deck, title):
        base = f"{DECK_PREFIX[deck]}-{_slug(title)}"
        cid, k = base, 2
        while cid in used:
            cid, k = f"{base}-{k}", k + 1
        used.add(cid)
        return cid

    def copies_of(raw, title, where):
        if str(raw).strip():
            try:
                return max(1, int(float(str(raw).split("+")[0]) + sum(int(x) for x in str(raw).split("+")[1:])))
            except ValueError:
                warnings.append(f"{where}: quantity “{raw}” isn't a number; using 1.")
                return 1
        n = defaults.get(norm_title(title))
        if n:
            warnings.append(f"{where}: no quantity in the sheet, using {n} copies.")
            return int(n)
        warnings.append(f"{where}: no quantity in the sheet; using 1.")
        return 1

    def body_rows(rows):
        for i, row in enumerate(rows[1:], start=2):
            first = str(row[0]).strip() if row else ""
            if first.lower() == "total":
                return
            yield i, row

    # Collectables tab: collectables, plus job opportunities, shortcuts, promotions, hospital items
    name, rows = _sheet(sheets, "collectables")
    if rows:
        cols = _columns(rows[0], {"name": ("name",), "deck": ("deck",), "qty": ("quantity", "qty", "copies"),
                                  "contraband": ("contraband",), "reusable": ("reusable",),
                                  "text": ("effect", "text", "card text")})
        for i, row in body_rows(rows):
            title = _cell(row, cols, "name")
            if not title:
                continue
            deck = _hand_deck_for(title, _cell(row, cols, "deck"))
            card = {"id": new_id(deck, title), "title": title, "text": _cell(row, cols, "text"),
                    "copies": copies_of(_cell(row, cols, "qty"), title, f"{name} row {i} ({title})")}
            if _truthy(_cell(row, cols, "contraband")):
                card["contraband"] = True
            if _truthy(_cell(row, cols, "reusable")):
                card["reusable"] = True
                card["equip"] = True
            auto = automation.get("collectable", {}).get(norm_title(title))
            _apply_automation(card, auto, "effects")
            # e.g. the Revolution Token: one copy starts the game on the discard pile
            start = int((auto or {}).get("start_in_discard") or 0)
            if start:
                start = min(start, card["copies"])
                decks[deck].append({**card, "id": new_id(deck, title + " start"), "copies": start,
                                    "start_in_discard": True})
                card["copies"] -= start
            if card["copies"] > 0:
                decks[deck].append(card)
            # "Collectable / Hospital Item": also dealt from the Hospital
            deck_cell = _cell(row, cols, "deck").lower()
            if deck == "collectable" and "collect" in deck_cell and "hospital" in deck_cell:
                decks["hospital"].append({**card, "id": new_id("hospital", title)})

    # Assignment slips: "<objective> <target>", reward in hours
    name, rows = _sheet(sheets, "assignment slips", "assignments")
    if rows:
        cols = _columns(rows[0], {"objective": ("objective", "title", "name"), "uses": ("uses", "relates"),
                                  "reward": ("reward",), "qty": ("quantity", "qty", "copies")})
        for i, row in body_rows(rows):
            objective = _cell(row, cols, "objective")
            if not objective:
                continue
            card = {"id": new_id("assignment", objective), "title": objective,
                    "text": f"{objective} your target.",
                    "copies": copies_of(_cell(row, cols, "qty"), objective, f"{name} row {i}")}
            reward = _cell(row, cols, "reward")
            try:
                hours = float(reward) if reward else 0
            except ValueError:
                hours = 0
                warnings.append(f"{name} row {i}: reward “{reward}” isn't a number of hours.")
            card["reward"] = ([{"type": "time", "who": "self", "minutes": int(round(hours * 60))}] if hours else [])
            auto = automation.get("assignment", {}).get(norm_title(objective))
            if auto and auto.get("reward"):
                card["reward"] += list(auto["reward"])
            if hours:
                card["text"] += f" Reward: {hours:g} hour{'s' if hours != 1 else ''}."
            decks["assignment"].append(card)

    # Scenario cards
    name, rows = _sheet(sheets, "scenario cards", "scenarios")
    if rows:
        cols = _columns(rows[0], {"card": ("card",), "type": ("type",), "text": ("card text", "text")})
        if cols.get("card") == cols.get("text"):
            cols["card"] = 0
        for i, row in body_rows(rows):
            title, text = _cell(row, cols, "card"), _cell(row, cols, "text")
            if not title or not text:
                continue
            card = {"id": new_id("scenario", title), "title": title, "text": text, "copies": 1}
            if _cell(row, cols, "type"):
                card["kind"] = _cell(row, cols, "type")
            _apply_automation(card, automation.get("scenario", {}).get(norm_title(title)), "effects")
            decks["scenario"].append(card)

    # Government oppressions: one row per physical card
    name, rows = _sheet(sheets, "oppressions")
    if rows:
        cols = _columns(rows[0], {"num": ("card",), "type": ("effect",), "amount": ("amount",),
                                  "text": ("card text", "text")})
        for i, row in body_rows(rows):
            effect_type, text = _cell(row, cols, "type"), _cell(row, cols, "text")
            if not effect_type or not text:
                continue
            amount = _cell(row, cols, "amount")
            title = effect_type if not amount or amount in ("—", "-") else f"{effect_type} ({amount})"
            card = {"id": new_id("oppression", f"{_cell(row, cols, 'num')} {title}"), "title": title,
                    "text": text, "copies": 1}
            auto = automation.get("oppression", {}).get(norm_title(title))
            card["effects"] = list((auto or {}).get("effects") or oppression_effects(effect_type, amount))
            decks["oppression"].append(card)

    # Reference tabs, kept with the version for later use
    reference = {}
    for sheet_name, rows in sheets.items():
        key = sheet_name.strip().lower()
        if key not in REFERENCE_SHEETS or not rows:
            continue
        header = [str(h).strip() for h in rows[0]]
        entries = []
        for _, row in body_rows(rows):
            filled = [str(c).strip() for c in row if str(c).strip()]
            if len(filled) < 2:
                continue  # a note row
            entries.append({header[j]: str(row[j]).strip() for j in range(min(len(header), len(row))) if header[j]})
        reference[key] = entries

    _, summary = _sheet(sheets, "summary")
    notes = "\n".join(" · ".join(str(c) for c in r if str(c).strip()) for r in (summary or []) if any(str(c).strip() for c in r))

    def automatic(card):
        return any(e.get("type") != "note" for e in (card.get("effects") or []) + (card.get("reward") or []))
    auto_n = sum(1 for d in decks.values() for c in d if automatic(c))
    total_n = sum(len(d) for d in decks.values())
    warnings.append(f"{auto_n} of {total_n} distinct cards act automatically; the others show their "
                    "instructions for the table to resolve.")
    return decks, reference, notes, warnings
