"""
Manage Gerry's Game card versions from the command line.

    python manage_cards.py list
    python manage_cards.py import cards.xlsx --key 4.28 --name "v4.28" --notes-file "patch notes.txt" --default --bundle
    python manage_cards.py check cards.xlsx            # parse only, print warnings
    python manage_cards.py export 4.28 out.xlsx        # edit the cards in Excel
    python manage_cards.py default 4.28                # what new rooms get unless they pick another

--bundle also writes app/data_collections/game_versions/<key>.json so the
version ships with the code (and is in git). Without it the version only
lives in the database. Either way the running server picks it up straight
away; rooms already playing keep the version they were created with.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)


def _read(path):
    from app import card_import
    with open(path, "rb") as f:
        return card_import.read_any(path, f.read())


def _print_warnings(warnings):
    for w in warnings:
        print(f"  ! {w}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    imp = sub.add_parser("import")
    imp.add_argument("file")
    imp.add_argument("--key", required=True)
    imp.add_argument("--name", default="")
    imp.add_argument("--notes", default="")
    imp.add_argument("--notes-file")
    imp.add_argument("--default", action="store_true")
    imp.add_argument("--replace", action="store_true", help="overwrite an existing version with this key")
    imp.add_argument("--bundle", action="store_true", help="also save it in data_collections/game_versions")

    chk = sub.add_parser("check")
    chk.add_argument("file")

    exp = sub.add_parser("export")
    exp.add_argument("key")
    exp.add_argument("out")

    d = sub.add_parser("default")
    d.add_argument("key")

    args = p.parse_args(argv)
    from app import card_import

    if args.cmd == "check":
        doc, warnings = card_import.build_version(_read(args.file), key="check")
        print({deck: len(doc[deck]) for deck in card_import.DECKS})
        _print_warnings(warnings)
        return 0

    from app import createApp
    app = createApp("development")
    with app.app_context():
        from app import game_versions

        if args.cmd == "list":
            for v in game_versions.list_versions():
                flag = " (default)" if v["is_default"] else ""
                print(f"{v['key']:<16} {v['name']}{flag}  {v['counts']}  [{v['source']}]")
        elif args.cmd == "import":
            notes = args.notes
            if args.notes_file:
                with open(args.notes_file, encoding="utf-8") as f:
                    notes = f.read()
            doc, warnings = card_import.build_version(_read(args.file), key=args.key, name=args.name, notes=notes)
            _print_warnings(warnings)
            source = "bundled" if args.bundle else "upload"
            game_versions.save_version(doc, source=source, created_by="manage_cards",
                                       make_default=args.default, replace=args.replace)
            if args.bundle:
                path = os.path.join(game_versions.BUNDLED_DIR, f"{args.key}.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({**doc, "default": args.default}, f, ensure_ascii=False, indent=2)
                print(f"wrote {path}")
            print(f"saved version {args.key}: " + ", ".join(f"{len(doc[deck])} {deck}" for deck in card_import.DECKS))
        elif args.cmd == "export":
            doc = game_versions.version_doc(args.key)
            if not doc:
                print(f"No version {args.key}")
                return 1
            with open(args.out, "wb") as f:
                f.write(card_import.write_xlsx(card_import.version_to_sheets(doc)))
            print(f"wrote {args.out}")
        elif args.cmd == "default":
            if not game_versions.set_default(args.key):
                print(f"No version {args.key}")
                return 1
            print(f"{args.key} is now the default")
    return 0


if __name__ == "__main__":
    sys.exit(main())
