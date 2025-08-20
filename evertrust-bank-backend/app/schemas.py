from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from datetime import datetime

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    phone = fields.Str(validate=validate.Length(min=10, max=20))
    address = fields.Str()
    created_at = fields.DateTime(dump_only=True)

class AccountSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    type = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    number = fields.Str(dump_only=True)
    balance = fields.Decimal(as_string=True, dump_only=True)
    currency = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class TransactionSchema(Schema):
    id = fields.Int(dump_only=True)
    account_id = fields.Int(required=True)
    type = fields.Str(required=True, validate=validate.OneOf(['Deposit', 'Withdrawal', 'Transfer']))
    amount = fields.Decimal(required=True, places=2, validate=validate.Range(min=0.01))
    description = fields.Str(validate=validate.Length(max=500))
    counterparty = fields.Str(validate=validate.Length(max=100))
    created_at = fields.DateTime(dump_only=True)
    status = fields.Str(dump_only=True)

class ExternalTransferSchema(Schema):
    id = fields.Int(dump_only=True)
    from_account_id = fields.Int(required=True)
    bank_name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    beneficiary_name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    beneficiary_account = fields.Str(required=True, validate=validate.Length(min=5, max=50))
    amount = fields.Decimal(required=True, places=2, validate=validate.Range(min=0.01))
    fee = fields.Decimal(places=2, dump_only=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class BillerSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    category = fields.Str(validate=validate.Length(max=50))
    account_number = fields.Str(validate=validate.Length(max=50))
    created_at = fields.DateTime(dump_only=True)

class BillSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    biller_id = fields.Int(required=True)
    account_id = fields.Int(required=True)
    amount = fields.Decimal(required=True, places=2, validate=validate.Range(min=0.01))
    status = fields.Str(dump_only=True)
    due_date = fields.Date()
    paid_date = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class CardSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    last4 = fields.Str(dump_only=True)
    brand = fields.Str(dump_only=True)
    is_frozen = fields.Bool()
    per_tx_limit = fields.Decimal(places=2, validate=validate.Range(min=1, max=10000))
    daily_limit = fields.Decimal(places=2, validate=validate.Range(min=10, max=50000))
    expires = fields.Date(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class ChequeSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    account_id = fields.Int(required=True)
    request_status = fields.Str(dump_only=True)
    leaves = fields.Int(validate=validate.Range(min=1, max=100))
    requested_at = fields.DateTime(dump_only=True)
    canceled_at = fields.DateTime(dump_only=True)

class MobileDepositSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    account_id = fields.Int(required=True)
    filename = fields.Str(dump_only=True)
    amount = fields.Decimal(required=True, places=2, validate=validate.Range(min=0.01))
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    processed_at = fields.DateTime(dump_only=True)

class AlertSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    type = fields.Str(dump_only=True)
    message = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    read = fields.Bool()

class AlertPrefsSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    low_balance = fields.Bool()
    low_balance_threshold = fields.Decimal(places=2, validate=validate.Range(min=0))
    large_tx = fields.Bool()
    large_tx_threshold = fields.Decimal(places=2, validate=validate.Range(min=0))
    card_change = fields.Bool()
    email_enabled = fields.Bool()

# Auth schemas
class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))

class RegisterSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    phone = fields.Str(validate=validate.Length(min=10, max=20))
    address = fields.Str()

class ChangePasswordSchema(Schema):
    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=6))