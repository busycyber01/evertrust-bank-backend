from app import db
from datetime import datetime
import bcrypt
from sqlalchemy.dialects.postgresql import JSONB

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    accounts = db.relationship('Account', backref='user', lazy=True)
    cards = db.relationship('Card', backref='user', lazy=True)
    alerts = db.relationship('Alert', backref='user', lazy=True)
    alert_prefs = db.relationship('AlertPrefs', backref='user', uselist=False)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # Checking, Savings, etc.
    number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Numeric(15, 2), default=0.00)
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='account', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # Deposit, Withdrawal, Transfer
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text)
    counterparty = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Completed')  # Pending, Completed, Failed

class ExternalTransfer(db.Model):
    __tablename__ = 'external_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    beneficiary_name = db.Column(db.String(100), nullable=False)
    beneficiary_account = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    fee = db.Column(db.Numeric(10, 2), default=0.00)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Biller(db.Model):
    __tablename__ = 'billers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    account_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bill(db.Model):
    __tablename__ = 'bills'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    biller_id = db.Column(db.Integer, db.ForeignKey('billers.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    due_date = db.Column(db.Date)
    paid_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    biller = db.relationship('Biller', backref='bills')

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    kind = db.Column(db.String(50), nullable=False)  # bill_payment, transfer
    payload = db.Column(JSONB, nullable=False)  # JSON data for the scheduled task
    next_run_at = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Card(db.Model):
    __tablename__ = 'cards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    last4 = db.Column(db.String(4), nullable=False)
    brand = db.Column(db.String(20), nullable=False)  # Visa, MasterCard, etc.
    is_frozen = db.Column(db.Boolean, default=False)
    per_tx_limit = db.Column(db.Numeric(10, 2), default=5000.00)
    daily_limit = db.Column(db.Numeric(10, 2), default=10000.00)
    expires = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Cheque(db.Model):
    __tablename__ = 'cheques'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    request_status = db.Column(db.String(20), default='Requested')  # Requested, Processed, Shipped, Received, Canceled
    leaves = db.Column(db.Integer, default=25)  # Number of cheque leaves
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    canceled_at = db.Column(db.DateTime)

class MobileDeposit(db.Model):
    __tablename__ = 'mobile_deposits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Processed, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # low_balance, large_tx, card_change
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

class AlertPrefs(db.Model):
    __tablename__ = 'alert_prefs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    low_balance = db.Column(db.Boolean, default=True)
    low_balance_threshold = db.Column(db.Numeric(15, 2), default=100.00)
    large_tx = db.Column(db.Boolean, default=True)
    large_tx_threshold = db.Column(db.Numeric(15, 2), default=1000.00)
    card_change = db.Column(db.Boolean, default=True)
    email_enabled = db.Column(db.Boolean, default=True)

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    entity = db.Column(db.String(50), nullable=False)  # account, transaction, card, etc.
    entity_id = db.Column(db.Integer)
    metadata = db.Column(JSONB)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)