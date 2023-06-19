from flask import Blueprint
from init import db, bcrypt
from models.user import User, UserSchema
from flask_jwt_extended import jwt_required
from blueprints.auth_bp import admin_required, admin_or_owner_required
from flask import request
from sqlalchemy.exc import IntegrityError


users_bp = Blueprint('users', __name__, url_prefix='/users')


@users_bp.route('/')
@jwt_required()
def all_users():
    admin_required()
    stmt = db.select(User)
    users = db.session.scalars(stmt)
    return UserSchema(many=True, exclude=['password']).dump(users)


@users_bp.route('/', methods=['POST'])
@jwt_required()
def create_user():
    admin_required()
    try:
        user_info = UserSchema().load(request.json)
        user = User(
            username=user_info['username'],
            email=user_info['email'],
            password=bcrypt.generate_password_hash(
                user_info['password']).decode('utf-8'),
            is_admin=user_info['is_admin']
        )
        db.session.add(user)
        db.session.commit()
        return UserSchema(exclude=['password']).dump(user), 201
    except IntegrityError:
        return {'error': 'Email already in use'}, 409


@users_bp.route('/<int:user_id>')
@jwt_required()
def get_one_user(user_id):
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)
    if user:
        admin_or_owner_required(user.id)
        return UserSchema(exclude=['password']).dump(user)
    else:
        return {'error': 'User not found'}, 404


@users_bp.route('/<int:user_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_user(user_id):
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)
    user_info = UserSchema().load(request.json)
    if user:
        admin_or_owner_required(user.id)
        user.username = user_info.get('username', user.username)
        user.email = user_info.get('email', user.email)
        new_password = user_info.get('password')
        if new_password:
            user.password = bcrypt.generate_password_hash(
                new_password).decode('utf-8')
        db.session.commit()
        return UserSchema(exclude=['cats']).dump(user)
    else:
        return {'error': 'User not found'}, 404


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    admin_required()
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)
    if user:
        db.session.delete(user)
        db.session.commit()
        return {}, 200
    else:
        return {'error': 'User not found'}, 404
