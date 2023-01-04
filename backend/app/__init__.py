from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy.sql.operators import is_natural_self_precedent
from sqlalchemy_utils import database_exists
from flask_jwt_extended import JWTManager
import config

import eventlet
eventlet.monkey_patch()

db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')
jwt = JWTManager()

def initDatabase(app):
    if not database_exists(config.Config.SQLALCHEMY_DATABASE_URI):
        with app.app_context():
            from . import models
            db.create_all()

            db.session.add(models.User(username="admin", password="admin"))
            db.session.add(models.User(username="jeff", password="jeff"))
            db.session.add(models.User(username="aaron", password="aaron"))
            db.session.add(models.User(username="xi xinping", password="xi xinping"))
            db.session.add(models.User(username="LiterallyHitler", password="LiterallyHitler"))
            db.session.add(models.User(username="Stalin", password="Stalin"))
            db.session.add(models.User(username="Josef Mengele", password="Josef"))
            db.session.add(models.User(username="Paul Gerry", password="Paul"))

            #db.session.add(models.Government(name="Democracy", description="TEST1"))
            #db.session.add(models.RoomState(name="Anarchy", description="TEST2"))
            #db.session.add(models.RoomState(name="Communism", description="TEST3"))
            #db.session.add(models.RoomState(name="Dictatorship", description="TEST3"))

            #db.session.add(models.Laws(name="law1"), description="the big law1")
            #db.session.add(models.Laws(name="law2"), description="the big law2")
            #db.session.add(models.Laws(name="law3"), description="the big law3")
            #db.session.add(models.Laws(name="law4"), description="the big law4")

            db.session.add(models.Room(name="test", id=1))
            db.session.add(models.RoomParticipants(roomId=1, userId=5))
            db.session.add(models.RoomParticipants(roomId=1, userId=6))
            db.session.add(models.RoomParticipants(roomId=1, userId=7))
            db.session.add(models.RoomParticipants(roomId=1, userId=8))
            
            db.session.add(models.Room(name="roogy", id=2))
            db.session.add(models.RoomParticipants(roomId=2, userId=1))
            db.session.add(models.RoomParticipants(roomId=2, userId=2))
            db.session.add(models.RoomParticipants(roomId=2, userId=3))
            db.session.add(models.RoomParticipants(roomId=2, userId=4))

            db.session.commit()

def createApp(configName):
    #Init Flask app
    app = Flask(__name__)
    app.config.from_object(config.APP_CONFIG[configName])
    #Init database
    db.init_app(app)
    initDatabase(app)
    #Init JWT
    jwt.init_app(app)
    #Init CORS (temporary)
    CORS(app, resources={r"/*": {"origins": "*"}})
    #Init websocket
    from .websocket.sockets import socketio
    socketio.init_app(app)
    #Init API blueprints
    from .api import api as apiBlueprint
    from .auth import auth as authBlueprint
    app.register_blueprint(apiBlueprint, url_prefix="/api")
    app.register_blueprint(authBlueprint, url_prefix="/api/auth")

    return app
