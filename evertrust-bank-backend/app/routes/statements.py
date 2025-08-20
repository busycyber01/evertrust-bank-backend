from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Account, Transaction, AuditLog
from app.services.pdf_service import generate_statement_pdf
from datetime import datetime, timedelta
import io

statements_bp = Blueprint('statements', __name__)

@statements_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_statement():
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    if not all(k in data for k in ['account_id', 'start_date', 'end_date']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    account_id = data['account_id']
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d') + timedelta(days=1)  # Include end date
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=account_id, user_id=current_user_id).first()
    if not account:
        return jsonify({'message': 'Account not found'}), 404
    
    # Get transactions for the date range
    transactions = Transaction.query.filter(
        Transaction.account_id == account_id,
        Transaction.created_at >= start_date,
        Transaction.created_at < end_date
    ).order_by(Transaction.created_at.desc()).all()
    
    # Generate PDF
    pdf_buffer = generate_statement_pdf(account, transactions, start_date, end_date)
    
    # Log the statement generation
    audit_log = AuditLog(
        user_id=current_user_id,
        action='statement_generated',
        entity='account',
        entity_id=account_id,
        metadata={
            'start_date': data['start_date'],
            'end_date': data['end_date']
        }
    )
    db.session.add(audit_log)
    db.session.commit()
    
    # Return PDF as download
    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"statement_{account.number}_{data['start_date']}_{data['end_date']}.pdf",
        mimetype='application/pdf'
    )