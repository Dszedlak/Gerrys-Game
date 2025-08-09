import json
import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
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

            db.session.add(models.User(username="admin", password="szedlak123"))
            
            jobs_collection_path = os.path.join(os.path.dirname(__file__), "data_collections", "jobs.json")
            #Its probably worth making this a separate function and more generic so it can be reused
            with open(jobs_collection_path, "r", encoding="utf-8") as f:
                jobs_data = json.load(f)
                for job in jobs_data:
                    if not models.Job.query.filter_by(id=job["id"]).first():
                        db.session.add(models.Job(
                            id=job["id"],
                            tier=job["tier"],
                            name=job["name"],
                            type=job.get("type", ""),
                        ))

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
