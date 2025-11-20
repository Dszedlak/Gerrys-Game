from flask_restful import Resource, marshal_with
from .. import db
from ..models import User, db
from .util import LEADERBOARD_FIELDS
from flask.json import jsonify


class LeaderBoardResource(Resource):
    @marshal_with(LEADERBOARD_FIELDS)
    def get(self):
        users = db.session.query(User.username, User.score).all()
        print(users)
        return users
