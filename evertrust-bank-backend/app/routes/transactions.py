from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Account, Transaction, ExternalTransfer, Alert, AlertPrefs, User
from app.schemas import TransactionSchema, ExternalTransferSchema
from app.utils import validate_request
from app.services import AuditService, EmailService
from decimal import Decimal
from datetime import datetime

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('', methods=['GET'])
@jwt_required()
def get_transactions():
    """
    Get transactions with filtering options
    """
    try:
        current_user_id = get_jwt_identity()
        account_id = request.args.get('accountId')
        tx_type = request.args.get('type')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 records
        offset = int(request.args.get('offset', 0))
        
        # Get user's accounts
        accounts = Account.query.filter_by(user_id=current_user_id).all()
        account_ids = [acc.id for acc in accounts]
        
        if not account_ids:
            return jsonify([]), 200
        
        # Build query
        query = Transaction.query.filter(Transaction.account_id.in_(account_ids))
        
        if account_id and int(account_id) in account_ids:
            query = query.filter_by(account_id=account_id)
        
        if tx_type:
            query = query.filter_by(type=tx_type)
        
        if from_date:
            try:
                from_dt = datetime.strptime(from_date, '%Y-%m-%d')
                query = query.filter(Transaction.created_at >= from_dt)
            except ValueError:
                pass
        
        if to_date:
            try:
                to_dt = datetime.strptime(to_date, '%Y-%m-%d')
                query = query.filter(Transaction.created_at <= to_dt)
            except ValueError:
                pass
        
        # Get total count for pagination
        total_count = query.count()
        
        transactions = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
        
        return jsonify({
            'transactions': TransactionSchema(many=True).dump(transactions),
            'total_count': total_count,
            'has_more': (offset + limit) < total_count
        }), 200
        
    except Exception as e:
        AuditService.log_event(
            user_id=get_jwt_identity(),
            action='transaction_query_failed',
            entity='transaction',
            metadata={'error': str(e), 'params': dict(request.args)}
        )
        return jsonify({'message': 'Failed to retrieve transactions', 'error': str(e)}), 500

@transactions_bp.route('/deposit', methods=['POST'])
@jwt_required()
def deposit():
    """
    Create a deposit transaction
    """
    try:
        current_user_id = get_jwt_identity()
        data = validate_request(TransactionSchema, request.get_json())
        
        # Verify account belongs to user
        account = Account.query.filter_by(id=data['account_id'], user_id=current_user_id).first()
        if not account:
            return jsonify({'message': 'Account not found'}), 404
        
        # Create transaction
        transaction = Transaction(
            account_id=data['account_id'],
            type='Deposit',
            amount=data['amount'],
            description=data.get('description', 'Deposit'),
            counterparty=data.get('counterparty', 'Self'),
            status='Completed'
        )
        
        # Update account balance
        account.balance += Decimal(str(data['amount']))
        
        db.session.add(transaction)
        db.session.flush()  # Flush to get transaction ID
        
        # Log audit event using AuditService
        AuditService.log_event(
            user_id=current_user_id,
            action='deposit_created',
            entity='transaction',
            entity_id=transaction.id,
            metadata={
                'amount': str(data['amount']),
                'account_id': data['account_id'],
                'account_number': account.number,
                'description': data.get('description', 'Deposit')
            }
        )
        
        # Check for alerts and send notifications
        alert_prefs = AlertPrefs.query.filter_by(user_id=current_user_id).first()
        user = User.query.get(current_user_id)
        
        if alert_prefs and alert_prefs.large_tx and data['amount'] >= alert_prefs.large_tx_threshold:
            alert_message = f'Large deposit of ${data["amount"]:,.2f} to account {account.number}'
            
            # Create alert in database
            alert = Alert(
                user_id=current_user_id,
                type='large_tx',
                message=alert_message
            )
            db.session.add(alert)
            
            # Send email notification if enabled
            if alert_prefs.email_enabled and user.email:
                EmailService.send_alert_notification(
                    user_email=user.email,
                    alert_type='large_deposit',
                    message=alert_message,
                    account_info=account.number
                )
        
        db.session.commit()
        
        # Send transaction receipt email
        if user.email:
            transaction_data = {
                'type': 'Deposit',
                'amount': f"{data['amount']:,.2f}",
                'description': data.get('description', 'Deposit'),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Completed',
                'account': f"•••• {account.number[-4]}"
            }
            EmailService.send_async_email(
                to_email=user.email,
                subject=f"Deposit Receipt - ${data['amount']:,.2f}",
                html_content=EmailService.send_transaction_receipt(user.email, transaction_data)
            )
        
        return jsonify(TransactionSchema().dump(transaction)), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'message': 'Invalid request data', 'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        AuditService.log_event(
            user_id=current_user_id,
            action='deposit_failed',
            entity='transaction',
            metadata={'error': str(e), 'data': data}
        )
        return jsonify({'message': 'Deposit failed', 'error': str(e)}), 500

@transactions_bp.route('/withdraw', methods=['POST'])
@jwt_required()
def withdraw():
    """
    Create a withdrawal transaction
    """
    try:
        current_user_id = get_jwt_identity()
        data = validate_request(TransactionSchema, request.get_json())
        
        # Verify account belongs to user
        account = Account.query.filter_by(id=data['account_id'], user_id=current_user_id).first()
        if not account:
            return jsonify({'message': 'Account not found'}), 404
        
        # Check sufficient funds
        amount = Decimal(str(data['amount']))
        if account.balance < amount:
            return jsonify({'message': 'Insufficient funds'}), 400
        
        # Create transaction
        transaction = Transaction(
            account_id=data['account_id'],
            type='Withdrawal',
            amount=amount,
            description=data.get('description', 'Withdrawal'),
            counterparty=data.get('counterparty', 'Self'),
            status='Completed'
        )
        
        # Update account balance
        account.balance -= amount
        
        db.session.add(transaction)
        db.session.flush()
        
        # Log audit event
        AuditService.log_event(
            user_id=current_user_id,
            action='withdrawal_created',
            entity='transaction',
            entity_id=transaction.id,
            metadata={
                'amount': str(amount),
                'account_id': data['account_id'],
                'account_number': account.number,
                'description': data.get('description', 'Withdrawal')
            }
        )
        
        # Check for alerts and send notifications
        alert_prefs = AlertPrefs.query.filter_by(user_id=current_user_id).first()
        user = User.query.get(current_user_id)
        
        # Check for low balance alert
        if alert_prefs and alert_prefs.low_balance and account.balance < alert_prefs.low_balance_threshold:
            alert_message = f'Low balance alert: Account {account.number} has ${account.balance:,.2f}'
            
            alert = Alert(
                user_id=current_user_id,
                type='low_balance',
                message=alert_message
            )
            db.session.add(alert)
            
            if alert_prefs.email_enabled and user.email:
                EmailService.send_alert_notification(
                    user_email=user.email,
                    alert_type='low_balance',
                    message=alert_message,
                    account_info=account.number
                )
        
        # Check for large transaction alert
        if alert_prefs and alert_prefs.large_tx and amount >= alert_prefs.large_tx_threshold:
            alert_message = f'Large withdrawal of ${amount:,.2f} from account {account.number}'
            
            alert = Alert(
                user_id=current_user_id,
                type='large_tx',
                message=alert_message
            )
            db.session.add(alert)
            
            if alert_prefs.email_enabled and user.email:
                EmailService.send_alert_notification(
                    user_email=user.email,
                    alert_type='large_withdrawal',
                    message=alert_message,
                    account_info=account.number
                )
        
        db.session.commit()
        
        # Send transaction receipt
        if user.email:
            transaction_data = {
                'type': 'Withdrawal',
                'amount': f"{amount:,.2f}",
                'description': data.get('description', 'Withdrawal'),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Completed',
                'account': f"•••• {account.number[-4]}"
            }
            EmailService.send_async_email(
                to_email=user.email,
                subject=f"Withdrawal Receipt - ${amount:,.2f}",
                html_content=EmailService.send_transaction_receipt(user.email, transaction_data)
            )
        
        return jsonify(TransactionSchema().dump(transaction)), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'message': 'Invalid request data', 'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        AuditService.log_event(
            user_id=current_user_id,
            action='withdrawal_failed',
            entity='transaction',
            metadata={'error': str(e), 'data': data}
        )
        return jsonify({'message': 'Withdrawal failed', 'error': str(e)}), 500

@transactions_bp.route('/transfer/internal', methods=['POST'])
@jwt_required()
def internal_transfer():
    """
    Transfer between user's own accounts
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['from_account_id', 'to_account_id', 'amount']
        if not all(k in data for k in required_fields):
            return jsonify({'message': 'Missing required fields', 'required': required_fields}), 400
        
        from_account_id = data['from_account_id']
        to_account_id = data['to_account_id']
        amount = Decimal(str(data['amount']))
        
        # Verify accounts belong to user
        from_account = Account.query.filter_by(id=from_account_id, user_id=current_user_id).first()
        to_account = Account.query.filter_by(id=to_account_id, user_id=current_user_id).first()
        
        if not from_account or not to_account:
            return jsonify({'message': 'Account not found'}), 404
        
        if from_account_id == to_account_id:
            return jsonify({'message': 'Cannot transfer to the same account'}), 400
        
        # Check sufficient funds
        if from_account.balance < amount:
            return jsonify({'message': 'Insufficient funds'}), 400
        
        # Create withdrawal transaction
        withdrawal = Transaction(
            account_id=from_account_id,
            type='Transfer',
            amount=amount,
            description=data.get('description', f'Transfer to account {to_account.number}'),
            counterparty=f'Account {to_account.number}',
            status='Completed'
        )
        
        # Create deposit transaction
        deposit = Transaction(
            account_id=to_account_id,
            type='Transfer',
            amount=amount,
            description=data.get('description', f'Transfer from account {from_account.number}'),
            counterparty=f'Account {from_account.number}',
            status='Completed'
        )
        
        # Update balances
        from_account.balance -= amount
        to_account.balance += amount
        
        db.session.add(withdrawal)
        db.session.add(deposit)
        db.session.flush()
        
        # Log audit event
        AuditService.log_event(
            user_id=current_user_id,
            action='internal_transfer_created',
            entity='transaction',
            entity_id=withdrawal.id,
            metadata={
                'from_account_id': from_account_id,
                'from_account_number': from_account.number,
                'to_account_id': to_account_id,
                'to_account_number': to_account.number,
                'amount': str(amount),
                'description': data.get('description', '')
            }
        )
        
        # Check for alerts and send notifications
        alert_prefs = AlertPrefs.query.filter_by(user_id=current_user_id).first()
        user = User.query.get(current_user_id)
        
        # Check for low balance alert on from_account
        if alert_prefs and alert_prefs.low_balance and from_account.balance < alert_prefs.low_balance_threshold:
            alert_message = f'Low balance alert: Account {from_account.number} has ${from_account.balance:,.2f}'
            
            alert = Alert(
                user_id=current_user_id,
                type='low_balance',
                message=alert_message
            )
            db.session.add(alert)
            
            if alert_prefs.email_enabled and user.email:
                EmailService.send_alert_notification(
                    user_email=user.email,
                    alert_type='low_balance',
                    message=alert_message,
                    account_info=from_account.number
                )
        
        # Check for large transaction alert
        if alert_prefs and alert_prefs.large_tx and amount >= alert_prefs.large_tx_threshold:
            alert_message = f'Large transfer of ${amount:,.2f} from account {from_account.number} to account {to_account.number}'
            
            alert = Alert(
                user_id=current_user_id,
                type='large_tx',
                message=alert_message
            )
            db.session.add(alert)
            
            if alert_prefs.email_enabled and user.email:
                EmailService.send_alert_notification(
                    user_email=user.email,
                    alert_type='large_transfer',
                    message=alert_message,
                    account_info=from_account.number
                )
        
        db.session.commit()
        
        # Send transaction receipt
        if user.email:
            transaction_data = {
                'type': 'Internal Transfer',
                'amount': f"{amount:,.2f}",
                'description': data.get('description', f'Transfer to account {to_account.number}'),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Completed',
                'account': f"•••• {from_account.number[-4]}"
            }
            EmailService.send_async_email(
                to_email=user.email,
                subject=f"Transfer Receipt - ${amount:,.2f}",
                html_content=EmailService.send_transaction_receipt(user.email, transaction_data)
            )
        
        return jsonify({
            'message': 'Transfer successful',
            'withdrawal': TransactionSchema().dump(withdrawal),
            'deposit': TransactionSchema().dump(deposit)
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'message': 'Invalid request data', 'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        AuditService.log_event(
            user_id=current_user_id,
            action='internal_transfer_failed',
            entity='transaction',
            metadata={'error': str(e), 'data': data}
        )
        return jsonify({'message': 'Transfer failed', 'error': str(e)}), 500

@transactions_bp.route('/transfer/external', methods=['POST'])
@jwt_required()
def external_transfer():
    """
    Transfer to external bank account
    """
    try:
        current_user_id = get_jwt_identity()
        data = validate_request(ExternalTransferSchema, request.get_json())
        
        # Verify account belongs to user
        from_account = Account.query.filter_by(id=data['from_account_id'], user_id=current_user_id).first()
        if not from_account:
            return jsonify({'message': 'Account not found'}), 404
        
        # Check sufficient funds (including fee)
        amount = Decimal(str(data['amount']))
        fee = Decimal('25.00')  # External transfer fee
        
        if from_account.balance < amount + fee:
            return jsonify({'message': 'Insufficient funds'}), 400
        
        # Create external transfer record
        transfer = ExternalTransfer(
            user_id=current_user_id,
            from_account_id=data['from_account_id'],
            bank_name=data['bank_name'],
            beneficiary_name=data['beneficiary_name'],
            beneficiary_account=data['beneficiary_account'],
            amount=amount,
            fee=fee,
            status='Processing'
        )
        
        # Create transaction for the withdrawal
        transaction = Transaction(
            account_id=data['from_account_id'],
            type='External Transfer',
            amount=amount + fee,
            description=f'External transfer to {data["beneficiary_name"]} at {data["bank_name"]}',
            counterparty=data['beneficiary_name'],
            status='Processing'
        )
        
        # Update account balance
        from_account.balance -= (amount + fee)
        
        db.session.add(transfer)
        db.session.add(transaction)
        db.session.flush()
        
        # Log audit event
        AuditService.log_event(
            user_id=current_user_id,
            action='external_transfer_created',
            entity='external_transfer',
            entity_id=transfer.id,
            metadata={
                'from_account_id': data['from_account_id'],
                'from_account_number': from_account.number,
                'bank_name': data['bank_name'],
                'beneficiary_name': data['beneficiary_name'],
                'beneficiary_account': data['beneficiary_account'][-4:],  # Last 4 digits only
                'amount': str(amount),
                'fee': str(fee)
            }
        )
    