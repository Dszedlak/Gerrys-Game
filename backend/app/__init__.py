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
            db.session.add(models.User(username="test", password="test"))
            db.session.add(models.User(username="david", password="test"))
            
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
    else:
        # Migrate existing database schema if needed
        with app.app_context():
            from . import models
            from sqlalchemy import inspect
            
            inspector = inspect(db.engine)
            
            # Check if room_participants table exists
            if 'room_participants' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('room_participants')]
                
                # Add missing is_in_jail column if it doesn't exist
                if 'is_in_jail' not in columns:
                    with db.engine.connect() as conn:
                        conn.execute(db.text('ALTER TABLE room_participants ADD COLUMN is_in_jail BOOLEAN DEFAULT 0'))
                        conn.commit()
                    print("Added is_in_jail column to room_participants table")


def createApp(configName):
    # Get path to frontend dist directory (one level up from backend)
    # __file__ = /backend/app/__init__.py
    # dirname(__file__) = /backend/app
    # dirname(dirname(__file__)) = /backend
    # dirname(dirname(dirname(__file__))) = /workspace
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    workspace_dir = os.path.dirname(backend_dir)
    frontend_dist = os.path.join(workspace_dir, 'frontend', 'dist')
    
    #Init Flask app (don't use static_url_path - handle all static files via routes)
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
    
    # Serve uploaded avatar files
    @app.route('/api/uploads/avatars/<filename>')
    def serve_avatar(filename):
        """Serve uploaded avatar images"""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
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
