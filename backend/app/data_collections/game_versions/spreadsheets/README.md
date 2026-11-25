# Card spreadsheets

Drop the Gerry's Game card spreadsheet (`.xlsx`) for a new version here,
along with its patch notes if you have them (e.g. `patch-notes-4.28.pdf`).

Each spreadsheet becomes a **game version**:

    python backend/manage_cards.py check  "backend/app/data_collections/game_versions/spreadsheets/<file>.xlsx"
    python backend/manage_cards.py import "backend/app/data_collections/game_versions/spreadsheets/<file>.xlsx" --key 4.28 --name "v4.28" --default --bundle

`--bundle` writes `../<key>.json` next to this folder, so the version ships
with the code. The spreadsheet layout the importer understands is described
at the top of `backend/app/card_import.py`; `../card-template.xlsx` is an example.
