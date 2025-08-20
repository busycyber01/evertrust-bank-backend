from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import MobileDeposit, Account, AuditLog
from app.schemas import MobileDepositSchema
from app.utils import validate_request
import os
import uuid
from datetime import datetime

deposits_bp = Blueprint('deposits', __name__)

@deposits_bp.route('/mobile', methods=['POST'])
@jwt_required()
def mobile_deposit():
    current_user_id = get_jwt_identity()
    
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    # Validate other form data
    data = request.form
    if not all(k in data for k in ['account_id', 'amount']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    account_id = data['account_id']
    amount = Decimal(data['amount'])
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=account_id, user_id=current_user_id).first()
    if not account:
        return jsonify({'message': 'Account not found'}), 404
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_ext}"
    
    # In a real application, you would save the file to cloud storage
    # For demo purposes, we'll just store the filename
    
    # Create mobile deposit record
    deposit = MobileDeposit(
        user_id=current_user_id,
        account_id=account_id,
        filename=filename,
        amount=amount,
        status='Pending'
    )
    
    db.session.add(deposit)
    
    # Log the mobile deposit
    audit_log = AuditLog(
        user_id=current_user_id,
        action='mobile_deposit',
        entity='mobile_deposit',
        entity_id=deposit.id,
        metadata={
            'account_id': account_id,
            'amount': str(amount),
            'filename': filename
        }
    )
    db.session.add(audit_log)
    db.session.commit()
    
    # Simulate processing after a delay
    # In a real application, this would be handled by a background job
    deposit.status = 'Processed'
    deposit.processed_at = datetime.now()
    
    # Create transaction and update balance
    transaction = Transaction(
        account_id=account_id,
        type='Deposit',
        amount=amount,
        description='Mobile deposit',
        counterparty='Mobile Deposit'
    )
    
    account.balance += amount
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify(MobileDepositSchema().dump(deposit)), 201

@deposits_bp.route('', methods=['GET'])
@jwt_required()
def get_deposits():
    current_user_id = get_jwt_identity()
    deposits = MobileDeposit.query.filter_by(user_id=current_user_id).order_by(MobileDeposit.created_at.desc()).all()
    return jsonify(MobileDepositSchema(many=True).dump(deposits)), 200