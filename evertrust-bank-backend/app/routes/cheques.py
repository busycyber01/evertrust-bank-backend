from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Cheque, Account, AuditLog
from app.schemas import ChequeSchema
from app.utils import validate_request

cheques_bp = Blueprint('cheques', __name__)

@cheques_bp.route('', methods=['GET'])
@jwt_required()
def get_cheques():
    current_user_id = get_jwt_identity()
    cheques = Cheque.query.filter_by(user_id=current_user_id).order_by(Cheque.requested_at.desc()).all()
    return jsonify(ChequeSchema(many=True).dump(cheques)), 200

@cheques_bp.route('/request', methods=['POST'])
@jwt_required()
def request_cheque():
    current_user_id = get_jwt_identity()
    data = validate_request(ChequeSchema, request.get_json())
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=data['account_id'], user_id=current_user_id).first()
    if not account:
        return jsonify({'message': 'Account not found'}), 404
    
    # Check for existing pending request
    pending_request = Cheque.query.filter_by(
        user_id=current_user_id, 
        account_id=data['account_id'],
        request_status='Requested'
    ).first()
    
    if pending_request:
        return jsonify({'message': 'You already have a pending cheque request for this account'}), 400
    
    # Create cheque request
    cheque = Cheque(
        user_id=current_user_id,
        account_id=data['account_id'],
        leaves=data.get('leaves', 25),
        request_status='Requested'
    )
    
    db.session.add(cheque)
    
    # Log the cheque request
    audit_log = AuditLog(
        user_id=current_user_id,
        action='cheque_requested',
        entity='cheque',
        entity_id=cheque.id,
        metadata={
            'account_id': data['account_id'],
            'leaves': data.get('leaves', 25)
        }
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify(ChequeSchema().dump(cheque)), 201

@cheques_bp.route('/<int:cheque_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_cheque(cheque_id):
    current_user_id = get_jwt_identity()
    
    cheque = Cheque.query.filter_by(id=cheque_id, user_id=current_user_id).first()
    if not cheque:
        return jsonify({'message': 'Cheque request not found'}), 404
    
    if cheque.request_status != 'Requested':
        return jsonify({'message': 'Only requested cheques can be canceled'}), 400
    
    cheque.request_status = 'Canceled'
    cheque.canceled_at = datetime.now()
    
    db.session.add(cheque)
    
    # Log the cheque cancellation
    audit_log = AuditLog(
        user_id=current_user_id,
        action='cheque_canceled',
        entity='cheque',
        entity_id=cheque.id
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify(ChequeSchema().dump(cheque)), 200