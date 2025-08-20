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
            # Create a test user
            user = User(name='Test User', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
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

def test_get_accounts(client):
    """Test getting user accounts"""
    token = get_auth_token(client)
    
    response = client.get('/api/v1/accounts', headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_create_account(client):
    """Test creating a new account"""
    token = get_auth_token(client)
    
    response = client.post('/api/v1/accounts', json={
        'type': 'Savings'
    }, headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['type'] == 'Savings'