from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Card, AuditLog, Alert, AlertPrefs
from app.schemas import CardSchema
from app.utils import validate_request
from datetime import datetime, timedelta
import random

cards_bp = Blueprint('cards', __name__)

def generate_card_number(brand):
    # Generate a valid test card number based on brand
    if brand == 'Visa':
        prefix = '4'
    elif brand == 'MasterCard':
        prefix = '5' + random.choice('12345')
    else:
        prefix = '3' + random.choice('47')
    
    # Generate the rest of the digits
    digits = prefix + ''.join(random.choices('0123456789', k=15-len(prefix)))
    
    # Simple Luhn check digit calculation
    total = 0
    for i, digit in enumerate(digits):
        n = int(digit)
        if (i + len(digits)) % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    
    check_digit = (10 - (total % 10)) % 10
    return digits + str(check_digit)

@cards_bp.route('', methods=['GET'])
@jwt_required()
def get_cards():
    current_user_id = get_jwt_identity()
    cards = Card.query.filter_by(user_id=current_user_id).all()
    
    # If no cards exist, create a default one
    if not cards:
        card = Card(
            user_id=current_user_id,
            last4='1234',
            brand='Visa',
            is_frozen=False,
            per_tx_limit=5000.00,
            daily_limit=10000.00,
            expires=datetime.now() + timedelta(days=365*3)
        )
        db.session.add(card)
        db.session.commit()
        cards = [card]
    
    return jsonify(CardSchema(many=True).dump(cards)), 200

@cards_bp.route('/<int:card_id>', methods=['PATCH'])
@jwt_required()
def update_card(card_id):
    current_user_id = get_jwt_identity()
    data = validate_request(CardSchema, request.get_json())
    
    card = Card.query.filter_by(id=card_id, user_id=current_user_id).first()
    if not card:
        return jsonify({'message': 'Card not found'}), 404
    
    # Track changes for alert
    changes = {}
    if 'is_frozen' in data and data['is_frozen'] != card.is_frozen:
        changes['frozen'] = data['is_frozen']
        card.is_frozen = data['is_frozen']
    
    if 'per_tx_limit' in data and data['per_tx_limit'] != card.per_tx_limit:
        changes['per_tx_limit'] = data['per_tx_limit']
        card.per_tx_limit = data['per_tx_limit']
    
    if 'daily_limit' in data and data['daily_limit'] != card.daily_limit:
        changes['daily_limit'] = data['daily_limit']
        card.daily_limit = data['daily_limit']
    
    db.session.add(card)
    
    # Log the card update
    audit_log = AuditLog(
        user_id=current_user_id,
        action='card_updated',
        entity='card',
        entity_id=card.id,
        metadata=changes
    )
    db.session.add(audit_log)
    
    # Check for card change alert
    alert_prefs = AlertPrefs.query.filter_by(user_id=current_user_id).first()
    if alert_prefs and alert_prefs.card_change and changes:
        alert = Alert(
            user_id=current_user_id,
            type='card_change',
            message=f'Card settings changed: {", ".join([f"{k}: {v}" for k, v in changes.items()])}'
        )
        db.session.add(alert)
    
    db.session.commit()
    
    return jsonify(CardSchema().dump(card)), 200