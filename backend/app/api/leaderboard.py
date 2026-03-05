from flask_restful import Resource, marshal_with
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models import User, db
from .util import LEADERBOARD_FIELDS
from flask.json import jsonify


class LeaderBoardResource(Resource):
    def get(self):
        try:
            users = db.session.query(User).all()
            return jsonify([{
                "username": user.username,
                "score": user.score,
                "profilePic": user.profilePic or "https://ui-avatars.com/api/?name=User"
            } for user in users])
        except Exception as e:
            print(f"[LeaderBoard] Error: {e}")
            return jsonify({"errors": str(e)}), 500


class FriendsLeaderBoardResource(Resource):
    @jwt_required()
    def get(self):
        try:
            current_user_id = get_jwt_identity()
            users = db.session.query(User).filter(User.id != current_user_id).all()
            return jsonify([{
                "username": user.username,
                "score": user.score,
                "profilePic": user.profilePic or "https://ui-avatars.com/api/?name=User"
            } for user in users])
        except Exception as e:
            print(f"[FriendsLeaderBoard] Error: {e}")
            return jsonify({"errors": str(e)}), 500
