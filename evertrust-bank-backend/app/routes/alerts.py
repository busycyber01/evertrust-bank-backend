from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Alert, AlertPrefs, AuditLog
from app.schemas import AlertSchema, AlertPrefsSchema
from app.utils import validate_request

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('', methods=['GET'])
@jwt_required()
def get_alerts():
    current_user_id = get_jwt_identity()
    alerts = Alert.query.filter_by(user_id=current_user_id).order_by(Alert.created_at.desc()).limit(50).all()
    return jsonify(AlertSchema(many=True).dump(alerts)), 200

@alerts_bp.route('/<int:alert_id>/read', methods=['POST'])
@jwt_required()
def mark_alert_read(alert_id):
    current_user_id = get_jwt_identity()
    
    alert = Alert.query.filter_by(id=alert_id, user_id=current_user_id).first()
    if not alert:
        return jsonify({'message': 'Alert not found'}), 404
    
    alert.read = True
    db.session.commit()
    
    return jsonify(AlertSchema().dump(alert)), 200

@alerts_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_alert_prefs():
    current_user_id = get_jwt_identity()
    
    prefs = AlertPrefs.query.filter_by(user_id=current_user_id).first()
    if not prefs:
        # Create default preferences if they don't exist
        prefs = AlertPrefs(
            user_id=current_user_id,
            low_balance=True,
            low_balance_threshold=100.00,
            large_tx=True,
            large_tx_threshold=1000.00,
            card_change=True,
            email_enabled=True
        )
        db.session.add(prefs)
        db.session.commit()
    
    return jsonify(AlertPrefsSchema().dump(prefs)), 200

@alerts_bp.route('/preferences', methods=['PATCH'])
@jwt_required()
def update_alert_prefs():
    current_user_id = get_jwt_identity()
    data = validate_request(AlertPrefsSchema, request.get_json())
    
    prefs = AlertPrefs.query.filter_by(user_id=current_user_id).first()
    if not prefs:
        prefs = AlertPrefs(user_id=current_user_id)
        db.session.add(prefs)
    
    # Update preferences
    if 'low_balance' in data:
        prefs.low_balance = data['low_balance']
    if 'low_balance_threshold' in data:
        prefs.low_balance_threshold = data['low_balance_threshold']
    if 'large_tx' in data:
        prefs.large_tx = data['large_tx']
    if 'large_tx_threshold' in data:
        prefs.large_tx_threshold = data['large_tx_threshold']
    if 'card_change' in data:
        prefs.card_change = data['card_change']
    if 'email_enabled' in data:
        prefs.email_enabled = data['email_enabled']
    
    db.session.commit()
    
    # Log the preferences update
    audit_log = AuditLog(
        user_id=current_user_id,
        action='alert_prefs_updated',
        entity='alert_prefs',
        entity_id=prefs.id,
        metadata=data
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify(AlertPrefsSchema().dump(prefs)), 200