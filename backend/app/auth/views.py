import datetime
from flask import request
from flask.json import jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..models import User, db
from .. import jwt
from . import auth

@auth.route('/register', methods=['POST'])
def register():
    username=request.json['username']
    password=request.json['password']
    confirmPassword=request.json['confirmPassword']

    if username is None or password is None:
        return jsonify({'errors': 'Username or password is not valid.'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'errors': 'Username already taken.'}), 400
    if password != confirmPassword:
        return jsonify({'errors': 'Passwords do not match.'}), 400

    newUser = User(username=username, password=password)
    db.session.add(newUser)
    db.session.commit()

    access_token = create_access_token(identity=newUser, expires_delta=datetime.timedelta(hours=12))
    return jsonify({'success': True, 'token': access_token}), 200

@auth.route('/login', methods=['POST'])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if username is None or password is None:
        return jsonify({'errors': 'Could not verify.'}), 401

    user = User.query.filter_by(username=username).one_or_none()
    if user is not None and user.verifyPassword(password):
        access_token = create_access_token(identity=user, expires_delta=datetime.timedelta(hours=12))
        return jsonify({'success': True, 'token': access_token}), 200
        
    return jsonify({'errors': 'Bad username or password'}), 401 

@auth.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).one_or_none()
    return jsonify({'username': user.username}), 200

@jwt.unauthorized_loader
def unauthorizedCallback(reason):
    return jsonify({'errors': 'No valid token found'}), 401  

@jwt.invalid_token_loader
def invalidTokenCallback(reason):
    return jsonify({'errors': 'No valid token found'}), 401  

@jwt.expired_token_loader
def my_expired_token_callback(reason):
    return jsonify({'errors': 'JWT Expired.'}), 401
