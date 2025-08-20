import pytest
import json
from app import create_app, db
from app.models import User, Account

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create test user and account
            user = User(name='Test User', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, type='Checking', number='1234567890', balance=1000.00)
            db.session.add(account)
            db.session.commit()
        yield client

def get_auth_token(client):
    """Helper to get authentication token"""
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    data = json.loads(response.data)
    return data['access_token']

def test_deposit_transaction(client):
    """Test deposit transaction"""
    token = get_auth_token(client)
    
    response = client.post('/api/v1/transactions/deposit', json={
        'account_id': 1,
        'amount': 500.00,
        'description': 'Test deposit'
    }, headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['type'] == 'Deposit'
    assert data['amount'] == '500.00'

def test_insufficient_funds(client):
    """Test withdrawal with insufficient funds"""
    token = get_auth_token(client)
    
    response = client.post('/api/v1/transactions/withdraw', json={
        'account_id': 1,
        'amount': 2000.00,
        'description': 'Large withdrawal'
    }, headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Insufficient funds' in data['message']