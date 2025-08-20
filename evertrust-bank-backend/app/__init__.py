from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
import os
from datetime import timedelta

db = SQLAlchemy()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db').replace('postgres://', 'postgresql://')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # CORS configuration
    CORS(app, origins=os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(','))
    
    # Rate limiting
    limiter.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.accounts import accounts_bp
    from app.routes.transactions import transactions_bp
    from app.routes.cards import cards_bp
    from app.routes.bills import bills_bp
    from app.routes.cheques import cheques_bp
    from app.routes.deposits import deposits_bp
    from app.routes.statements import statements_bp
    from app.routes.alerts import alerts_bp
    from app.routes.utilities import utilities_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(accounts_bp, url_prefix='/api/v1/accounts')
    app.register_blueprint(transactions_bp, url_prefix='/api/v1/transactions')
    app.register_blueprint(cards_bp, url_prefix='/api/v1/cards')
    app.register_blueprint(bills_bp, url_prefix='/api/v1/bills')
    app.register_blueprint(cheques_bp, url_prefix='/api/v1/cheques')
    app.register_blueprint(deposits_bp, url_prefix='/api/v1/deposits')
    app.register_blueprint(statements_bp, url_prefix='/api/v1/statements')
    app.register_blueprint(alerts_bp, url_prefix='/api/v1/alerts')
    app.register_blueprint(utilities_bp, url_prefix='/api/v1')
    
    return app