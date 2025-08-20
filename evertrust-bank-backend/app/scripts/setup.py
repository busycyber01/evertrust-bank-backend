#!/usr/bin/env python3
"""
Database setup script for EverTrust Bank
Run this to initialize the database and create default data
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import User, Account, AlertPrefs
import random
from datetime import datetime

def setup_database():
    """Initialize the database with default data"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Create demo user if it doesn't exist
        demo_user = User.query.filter_by(email='demo@evertrust.com').first()
        
        if not demo_user:
            print("Creating demo user...")
            demo_user = User(
                name='Demo User',
                email='demo@evertrust.com',
                phone='+1234567890',
                address='123 Demo Street, Demo City, DC 12345'
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.commit()
            print(f"Created demo user with ID: {demo_user.id}")
        
        # Create accounts for demo user
        accounts = Account.query.filter_by(user_id=demo_user.id).all()
        
        if not accounts:
            print("Creating demo accounts...")
            
            checking = Account(
                user_id=demo_user.id,
                type='Checking',
                number=''.join(random.choices('0123456789', k=12)),
                balance=12560.75,
                currency='USD'
            )
            
            savings = Account(
                user_id=demo_user.id,
                type='Savings',
                number=''.join(random.choices('0123456789', k=12)),
                balance=42380.20,
                currency='USD'
            )
            
            db.session.add(checking)
            db.session.add(savings)
            db.session.commit()
            print("Created checking and savings accounts")
        
        # Create alert preferences
        alert_prefs = AlertPrefs.query.filter_by(user_id=demo_user.id).first()
        
        if not alert_prefs:
            print("Creating alert preferences...")
            alert_prefs = AlertPrefs(
                user_id=demo_user.id,
                low_balance=True,
                low_balance_threshold=100.00,
                large_tx=True,
                large_tx_threshold=1000.00,
                card_change=True,
                email_enabled=True
            )
            db.session.add(alert_prefs)
            db.session.commit()
            print("Created alert preferences")
        
        print("Database setup completed successfully!")
        print(f"Demo credentials: demo@evertrust.com / demo123")

if __name__ == '__main__':
    setup_database()