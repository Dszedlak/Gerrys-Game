"""
REST endpoints for game versions (card sets).

    GET  /api/game-versions                 every version, for the create-room picker
    POST /api/game-versions                 upload a spreadsheet as a new version
    GET  /api/game-versions/<key>/export    the version as an .xlsx to edit

Uploading is limited to the usernames in the GAME_DATA_ADMINS setting
(environment variable, comma-separated). Until someone is listed there,
versions are added with `python manage_cards.py import ...` instead.
"""
from flask import current_app, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
import io

from ..models import User
from .. import game_versions
from .. import card_import


def _is_data_admin() -> bool:
    user = User.query.get(get_jwt_identity())
    allowed = current_app.config.get("GAME_DATA_ADMINS") or []
    return bool(user and user.username in allowed)


class GameVersionListResource(Resource):
    @jwt_required()
    def get(self):
        return {
            "versions": game_versions.list_versions(),
            "default": game_versions.default_key(),
            "can_upload": _is_data_admin(),
        }

    @jwt_required()
    def post(self):
        if not _is_data_admin():
            return {"error": "Only game-data admins can publish a new version."}, 403
        upload = request.files.get("file")
        if not upload:
            return {"error": "Attach the card spreadsheet as 'file'."}, 400
        form = request.form
        try:
            sheets = card_import.read_any(upload.filename or "", upload.read())
            doc, warnings = card_import.build_version(
                sheets, key=form.get("key", ""), name=form.get("name", ""), notes=form.get("notes", "")
            )
            if form.get("dry_run") in ("1", "true", "yes"):
                return {"ok": True, "dry_run": True, "warnings": warnings,
                        "counts": {d: len(doc[d]) for d in card_import.DECKS}}
            user = User.query.get(get_jwt_identity())
            game_versions.save_version(
                doc, source="upload", created_by=user.username if user else None,
                make_default=form.get("make_default") in ("1", "true", "yes"),
            )
        except (card_import.ImportError_, ValueError) as e:
            return {"error": str(e)}, 400
        return {"ok": True, "version": game_versions._summary(game_versions.get_version(doc["key"])),
                "warnings": warnings}, 201


class GameVersionExportResource(Resource):
    @jwt_required()
    def get(self, key):
        doc = game_versions.version_doc(key)
        if not doc:
            return {"error": "No such version."}, 404
        data = card_import.write_xlsx(card_import.version_to_sheets(doc))
        return send_file(
            io.BytesIO(data),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"gerrys-game-{key}-cards.xlsx",
        )
