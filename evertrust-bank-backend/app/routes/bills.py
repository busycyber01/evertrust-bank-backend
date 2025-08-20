from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Biller, Bill, Account, Transaction, AuditLog, Alert, AlertPrefs
from app.schemas import BillerSchema, BillSchema
from app.utils import validate_request
from decimal import Decimal
from datetime import datetime, timedelta

bills_bp = Blueprint('bills', __name__)

@bills_bp.route('/billers', methods=['GET'])
@jwt_required()
def get_billers():
    current_user_id = get_jwt_identity()
    billers = Biller.query.filter_by(user_id=current_user_id).all()
    return jsonify(BillerSchema(many=True).dump(billers)), 200

@bills_bp.route('/billers', methods=['POST'])
@jwt_required()
def create_biller():
    current_user_id = get_jwt_identity()
    data = validate_request(BillerSchema, request.get_json())
    
    biller = Biller(
        user_id=current_user_id,
        name=data['name'],
        category=data.get('category'),
        account_number=data.get('account_number')
    )
    
    db.session.add(biller)
    
    # Log the biller creation
    audit_log = AuditLog(
        user_id=current_user_id,
        action='biller_created',
        entity='biller',
        entity_id=biller.id,
        metadata={'name': biller.name}
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify(BillerSchema().dump(biller)), 201

@bills_bp.route('/pay', methods=['POST'])
@jwt_required()
def pay_bill():
    current_user_id = get_jwt_identity()
    data = validate_request(BillSchema, request.get_json())
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=data['account_id'], user_id=current_user_id).first()
    if not account:
        return jsonify({'message': 'Account not found'}), 404
    
    # Verify biller belongs to user
    biller = Biller.query.filter_by(id=data['biller_id'], user_id=current_user_id).first()
    if not biller:
        return jsonify({'message': 'Biller not found'}), 404
    
    # Check sufficient funds
    if account.balance < Decimal(str(data['amount'])):
        return jsonify({'message': 'Insufficient funds'}), 400
    
    # Create bill record
    bill = Bill(
        user_id=current_user_id,
        biller_id=data['biller_id'],
        account_id=data['account_id'],
        amount=data['amount'],
        status='Pending',
        due_date=data.get('due_date', datetime.now() + timedelta(days=30))
    )
    
    # Create transaction
    transaction = Transaction(
        account_id=data['account_id'],
        type='Withdrawal',
        amount=data['amount'],
        description=f'Bill payment to {biller.name}',
        counterparty=biller.name
    )
    
    # Update account balance
    account.balance -= Decimal(str(data['amount']))
    
    db.session.add(bill)
    db.session.add(transaction)
    
    # Log the bill payment
    audit_log = AuditLog(
        user_id=current_user_id,
        action='bill_paid',
        entity='bill',
        entity_id=bill.id,
        metadata={
            'biller': biller.name,
            'amount': str(data['amount']),
            'account_id': data['account_id']
        }
    )
    db.session.add(audit_log)
    
    # Check for alerts
    alert_prefs = AlertPrefs.query.filter_by(user_id=current_user_id).first()
    
    # Check for low balance alert
    if alert_prefs and alert_prefs.low_balance and account.balance < alert_prefs.low_balance_threshold:
        alert = Alert(
            user_id=current_user_id,
            type='low_balance',
            message=f'Low balance alert: Account {account.number} has ${account.balance}'
        )
        db.session.add(alert)
    
    # Check for large transaction alert
    if alert_prefs and alert_prefs.large_tx and data['amount'] >= alert_prefs.large_tx_threshold:
        alert = Alert(
            user_id=current_user_id,
            type='large_tx',
            message=f'Large bill payment of ${data["amount"]} to {biller.name}'
        )
        db.session.add(alert)
    
    db.session.commit()
    
    # Update bill status to completed
    bill.status = 'Completed'
    bill.paid_date = datetime.now()
    db.session.commit()
    
    return jsonify(BillSchema().dump(bill)), 201

@bills_bp.route('', methods=['GET'])
@jwt_required()
def get_bills():
    current_user_id = get_jwt_identity()
    bills = Bill.query.filter_by(user_id=current_user_id).order_by(Bill.created_at.desc()).limit(50).all()
    return jsonify(BillSchema(many=True).dump(bills)), 200