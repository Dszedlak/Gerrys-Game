import json
import os
from flask import Flask, send_from_directory
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

            # --- Load and insert jobs ---
            from .data_collections.loader import load_jobs  # removed load_governments here
            jobs_data = load_jobs()
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
    # Get path to frontend dist directory (one level up from backend)
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'dist')
    
    #Init Flask app
    app = Flask(__name__, 
                static_folder=frontend_dist,
                static_url_path='')
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
    
    # Serve index.html for all non-API routes (Vue Router fallback)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_spa(path):
        """Serve Vue.js SPA - return index.html for all non-API routes"""
        # If path is for static assets, serve them directly
        if path and os.path.exists(os.path.join(frontend_dist, path)):
            return send_from_directory(frontend_dist, path)
        # For all other routes (including root), serve index.html (Vue Router will handle routing)
        if os.path.exists(os.path.join(frontend_dist, 'index.html')):
            return send_from_directory(frontend_dist, 'index.html')
        # Fallback if dist doesn't exist
        return "Frontend not built. Run 'npm run build' in the frontend directory.", 500

    return app
