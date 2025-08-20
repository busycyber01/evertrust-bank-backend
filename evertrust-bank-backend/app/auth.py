from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app import db
from app.models import User, AuditLog
from app.schemas import LoginSchema, RegisterSchema, ChangePasswordSchema
from app.utils import validate_request

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = validate_request(RegisterSchema, request.get_json())
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 409
    
    # Create new user
    user = User(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone'),
        address=data.get('address')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Create default account for the user
    from app.routes.accounts import create_default_account
    create_default_account(user.id)
    
    # Log the signup
    audit_log = AuditLog(
        user_id=user.id,
        action='user_signup',
        entity='user',
        entity_id=user.id,
        metadata={'email': user.email}
    )
    db.session.add(audit_log)
    db.session.commit()
    
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'message': 'User created successfully',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = validate_request(LoginSchema, request.get_json())
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Log the login
    audit_log = AuditLog(
        user_id=user.id,
        action='user_login',
        entity='user',
        entity_id=user.id
    )
    db.session.add(audit_log)
    db.session.commit()
    
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_user_id = get_jwt_identity()
    
    # Log the logout
    audit_log = AuditLog(
        user_id=current_user_id,
        action='user_logout',
        entity='user',
        entity_id=current_user_id
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify({'message': 'Successfully logged out'}), 200