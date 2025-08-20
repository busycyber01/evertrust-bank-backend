import pytest
import json
from app import create_app, db
from app.models import User

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_user_registration(client):
    """Test user registration endpoint"""
    response = client.post('/api/v1/auth/signup', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'phone': '+1234567890'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'access_token' in data
    assert data['user']['email'] == 'test@example.com'

def test_user_login(client):
    """Test user login endpoint"""
    # First create a user
    client.post('/api/v1/auth/signup', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # Then test login
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data

def test_invalid_login(client):
    """Test login with invalid credentials"""
    response = client.post('/api/v1/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401