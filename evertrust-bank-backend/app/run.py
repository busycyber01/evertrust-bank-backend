#!/usr/bin/env python3
"""
Development server entry point for EverTrust Bank
"""

from app import create_app
from flask_migrate import Migrate
import os

app = create_app()
migrate = Migrate(app, app.db)

@app.cli.command("create-db")
def create_db():
    """Create database tables"""
    with app.app_context():
        app.db.create_all()
    print("Database tables created successfully")

@app.cli.command("seed-db")
def seed_db():
    """Seed database with sample data"""
    from scripts.seed_database import seed_database
    seed_database()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])