from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Account, User, AuditLog
from app.schemas import AccountSchema
from app.utils import validate_request
import random
import string

accounts_bp = Blueprint('accounts', __name__)

def generate_account_number():
    return ''.join(random.choices(string.digits, k=12))

def create_default_account(user_id):
    account = Account(
        user_id=user_id,
        type='Checking',
        number=generate_account_number(),
        balance=1000.00  # Initial balance for demo
    )
    db.session.add(account)
    db.session.commit()
    return account

@accounts_bp.route('', methods=['GET'])
@jwt_required()
def get_accounts():
    current_user_id = get_jwt_identity()
    accounts = Account.query.filter_by(user_id=current_user_id).all()
    
    return jsonify(AccountSchema(many=True).dump(accounts)), 200

@accounts_bp.route('/<int:account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id):
    current_user_id = get_jwt_identity()
    account = Account.query.filter_by(id=account_id, user_id=current_user_id).first()
    
    if not account:
        return jsonify({'message': 'Account not found'}), 404
    
    return jsonify(AccountSchema().dump(account)), 200

@accounts_bp.route('', methods=['POST'])
@jwt_required()
def create_account():
    current_user_id = get_jwt_identity()
    data = validate_request(AccountSchema, request.get_json())
    
    account = Account(
        user_id=current_user_id,
        type=data['type'],
        number=generate_account_number(),
        balance=0.00
    )
    
    db.session.add(account)
    
    # Log the account creation
    audit_log = AuditLog(
        user_id=current_user_id,
        action='account_created',
        entity='account',
        entity_id=account.id,
        metadata={'type': account.type}
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify(AccountSchema().dump(account)), 201