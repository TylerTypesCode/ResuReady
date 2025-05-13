from .instances import login_manager, migrate, db
from .routes.subscription import subscription_bp, init_stripe
from .routes.interview import interview_bp
from .routes.jobapps import job_app_bp
from .routes.resume import resume_bp
from .routes.main import main_bp
from .routes.auth import auth_bp
from .routes.user import user_bp
from dotenv import load_dotenv
from flask import Flask
import os
from flask_login import current_user

load_dotenv()

def check_subscription_status():
    """Middleware to check subscription status on each request"""
    if current_user.is_authenticated:
        current_user.check_subscription_status()

def create_app():
    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    
    # Load configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')
    app.config['STRIPE_PUBLISHABLE_KEY'] = os.getenv('STRIPE_PUBLISHABLE_KEY')
    app.config['STRIPE_WEBHOOK_SECRET'] = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Initialize Stripe
    init_stripe(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(job_app_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(subscription_bp)
    
    app.before_request(check_subscription_status)
    
    return app

