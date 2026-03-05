import datetime
import os
import uuid
from flask import request, current_app, url_for
from flask.json import jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from ..models import User, db
from .. import jwt
from . import auth

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@auth.route("/register", methods=["POST"])
def register():
    username = request.json["username"]
    password = request.json["password"]
    confirmPassword = request.json["confirmPassword"]

    print(f"[REGISTER] Attempting registration for username: {username}")

    if username is None or password is None:
        print("[REGISTER] Failed: Username or password is missing.")
        return jsonify({"errors": "Username or password is not valid."}), 400
    if User.query.filter_by(username=username).first():
        print(f"[REGISTER] Failed: Username '{username}' already taken.")
        return jsonify({"errors": "Username already taken."}), 400
    if password != confirmPassword:
        print(f"[REGISTER] Failed: Passwords do not match for username '{username}'.")
        return jsonify({"errors": "Passwords do not match."}), 400

    newUser = User(username=username, password=password)
    db.session.add(newUser)
    db.session.commit()
    print(f"[REGISTER] User '{username}' registered successfully.")

    access_token = create_access_token(
        identity=newUser, expires_delta=datetime.timedelta(hours=12)
    )
    return jsonify({"success": True, "token": access_token}), 200


@auth.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    print(f"[LOGIN] Login attempt for username: {username}")

    if username is None or password is None:
        print("[LOGIN] Failed: Username or password missing.")
        return jsonify({"errors": "Could not verify."}), 401

    user = User.query.filter_by(username=username).one_or_none()
    if user is not None and user.verifyPassword(password):
        print(f"[LOGIN] Success for username: {username}")
        access_token = create_access_token(
            identity=user, expires_delta=datetime.timedelta(hours=6)
        )
        return jsonify({
            "success": True,
            "token": access_token,
            "username": user.username 
        }), 200

    print(f"[LOGIN] Failed: Bad username or password for username: {username}")
    return jsonify({"errors": "Bad username or password"}), 401


@auth.route("/verify-token", methods=["GET"])
@jwt_required()
def verify_token():
    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).one_or_none()
    print(f"[VERIFY-TOKEN] Token verified for user ID: {userId}")
    return jsonify({"username": user.username}), 200


@jwt.unauthorized_loader
def unauthorizedCallback(reason):
    print(f"[JWT] Unauthorized: {reason}")
    return jsonify({"errors": "No valid token found"}), 401


@jwt.invalid_token_loader
def invalidTokenCallback(reason):
    print(f"[JWT] Invalid token: {reason}")
    return jsonify({"errors": "No valid token found"}), 401


@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    print("[JWT] Expired token.")
    return jsonify({"errors": "JWT Expired."}), 401


@auth.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    """Get current user's profile"""
    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).one_or_none()
    if not user:
        return jsonify({"errors": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "score": user.score,
        "profilePic": user.profilePic or "https://ui-avatars.com/api/?name=User"
    }), 200


@auth.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """Update current user's profile (username and/or profile picture)"""
    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).one_or_none()
    if not user:
        return jsonify({"errors": "User not found"}), 404
    
    data = request.json or {}
    
    # Update username if provided
    new_username = data.get("username")
    if new_username:
        # Check if username is already taken by another user
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != userId:
            return jsonify({"errors": "Username already taken"}), 400
        user.username = new_username
    
    # Update profile picture if provided
    new_pic = data.get("profilePic")
    if new_pic is not None:
        user.profilePic = new_pic
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "id": user.id,
        "username": user.username,
        "score": user.score,
        "profilePic": user.profilePic or "https://ui-avatars.com/api/?name=User"
    }), 200


@auth.route("/upload-avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    """Upload a profile picture (PNG or JPEG only)"""
    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).one_or_none()
    if not user:
        return jsonify({"errors": "User not found"}), 404
    
    if 'file' not in request.files:
        return jsonify({"errors": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"errors": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"errors": "Only PNG and JPEG files are allowed"}), 400
    
    # Create uploads directory if it doesn't exist
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    
    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{userId}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_folder, filename)
    
    # Delete old avatar file if it exists and is a local upload
    if user.profilePic and '/api/uploads/avatars/' in user.profilePic:
        old_filename = user.profilePic.split('/')[-1]
        old_filepath = os.path.join(upload_folder, old_filename)
        if os.path.exists(old_filepath):
            os.remove(old_filepath)
    
    # Save the new file
    file.save(filepath)
    
    # Update user profile with the new image URL
    user.profilePic = f"/api/uploads/avatars/{filename}"
    db.session.commit()
    
    return jsonify({
        "success": True,
        "profilePic": user.profilePic
    }), 200
