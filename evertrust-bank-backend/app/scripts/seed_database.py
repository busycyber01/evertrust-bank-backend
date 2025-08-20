#!/usr/bin/env python3
"""
Database seeding script for EverTrust Bank
Adds sample transactions and data for testing
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import User, Account, Transaction, Alert
from decimal import Decimal
from datetime import datetime, timedelta
import random

def seed_database():
    """Add sample data to the database"""
    app = create_app()
    
    with app.app_context():
        print("Seeding database with sample data...")
        
        # Get demo user
        demo_user = User.query.filter_by(email='demo@evertrust.com').first()
        
        if not demo_user:
            print("Demo user not found. Run setup.py first.")
            return
        
        # Get user accounts
        accounts = Account.query.filter_by(user_id=demo_user.id).all()
        
        if not accounts:
            print("No accounts found for demo user. Run setup.py first.")
            return
        
        checking_account = next((acc for acc in accounts if acc.type == 'Checking'), None)
        savings_account = next((acc for acc in accounts if acc.type == 'Savings'), None)
        
        # Create sample transactions
        transactions = Transaction.query.filter_by(account_id=checking_account.id).all()
        
        if not transactions:
            print("Creating sample transactions...")
            
            # Sample transactions for the past 30 days
            transaction_types = ['Deposit', 'Withdrawal', 'Transfer']
            descriptions = [
                'Salary Deposit', 'Grocery Store', 'Online Shopping',
                'Restaurant Payment', 'Utility Bill', 'Mobile Recharge',
                'Coffee Shop', 'Book Store', 'Gas Station', 'Movie Tickets'
            ]
            
            for i in range(30):
                transaction_date = datetime.now() - timedelta(days=random.randint(0, 30))
                transaction_type = random.choice(transaction_types)
                
                if transaction_type == 'Deposit':
                    amount = Decimal(random.uniform(100, 5000))
                else:
                    amount = Decimal(random.uniform(10, 500))
                
                transaction = Transaction(
                    account_id=checking_account.id,
                    type=transaction_type,
                    amount=amount,
                    description=random.choice(descriptions),
                    counterparty='Sample Merchant' if transaction_type != 'Deposit' else 'Employer Inc.',
                    created_at=transaction_date
                )
                
                db.session.add(transaction)
            
            db.session.commit()
            print("Created 30 sample transactions")
        
        # Create sample alerts
        alerts = Alert.query.filter_by(user_id=demo_user.id).all()
        
        if not alerts:
            print("Creating sample alerts...")
            
            alert_messages = [
                'Low balance alert: Your checking account balance is below $100',
                'Large transaction: A withdrawal of $450.00 was made',
                'Security alert: New login from unknown device',
                'Account update: Your contact information was changed',
                'Payment reminder: Credit card payment due in 3 days'
            ]
            
            for i in range(5):
                alert_date = datetime.now() - timedelta(days=random.randint(1, 7))
                alert = Alert(
                    user_id=demo_user.id,
                    type=random.choice(['low_balance', 'large_tx', 'security']),
                    message=alert_messages[i],
                    created_at=alert_date,
                    read=random.choice([True, False])
                )
                
                db.session.add(alert)
            
            db.session.commit()
            print("Created 5 sample alerts")
        
        print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()