from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy.sql.operators import is_natural_self_precedent
from sqlalchemy_utils import database_exists
from flask_jwt_extended import JWTManager
import config


db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")
jwt = JWTManager()

def initDatabase(app):
    if not database_exists(config.Config.SQLALCHEMY_DATABASE_URI):
        with app.app_context():
            from . import models
            db.create_all()
            db.session.add(models.User(username="admin", password="admin"))
            db.session.add(models.RoomState(name="Waiting"))
            db.session.add(models.RoomState(name="Running"))
            db.session.add(models.RoomState(name="Results"))
            db.session.add(models.User(username="jeff", password="jeff"))
            db.session.add(models.User(username="egg", password="egg"))
            db.session.add(models.User(username="nog", password="nog"))
            db.session.add(models.User(username="cock", password="cock"))
            db.session.add(models.User(username="balls", password="balls"))
            db.session.add(models.User(username="crip", password="crip"))
            db.session.add(models.User(username="Carbin", password="Carbin"))

            db.session.add(models.Quiz(creatorId=1, name="quiz1", description="epic test quiz"))
            db.session.add(models.Room(name="test", quizId=1, masterId=1, stateId=1))
            db.session.add(models.RoomState(name="test"))
            db.session.add(models.RoomParticipants(roomId=1, userId=5, score=0, isReady=True))
            db.session.add(models.RoomParticipants(roomId=1, userId=6, score=0, isReady=False))
            db.session.add(models.RoomParticipants(roomId=1, userId=7, score=0, isReady=False))
            db.session.add(models.RoomParticipants(roomId=1, userId=8, score=0, isReady=True))
            
            db.session.add(models.Quiz(creatorId=2, name="quiz2", description="epic test quiz"))
            db.session.add(models.Room(name="roogy", quizId=2, masterId=2, stateId=1))
            db.session.add(models.RoomState(name="leg"))
            db.session.add(models.RoomParticipants(roomId=2, userId=1, score=12, isReady=False))
            db.session.add(models.RoomParticipants(roomId=2, userId=2, score=5, isReady=True))
            db.session.add(models.RoomParticipants(roomId=2, userId=3, score=25, isReady=True))
            db.session.add(models.RoomParticipants(roomId=2, userId=4, score=18, isReady=True))

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
    from .websocket.QuizSession import QuizNamespace
    socketio.init_app(app)
    socketio.on_namespace(QuizNamespace())
    #Init API blueprints
    from .api import api as apiBlueprint
    from .auth import auth as authBlueprint
    app.register_blueprint(apiBlueprint, url_prefix="/api")
    app.register_blueprint(authBlueprint, url_prefix="/api/auth")
    return app