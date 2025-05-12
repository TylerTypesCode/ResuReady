from .instances import login_manager, migrate, db
from .routes.jobapps import job_app_bp
from .routes.resume import resume_bp
from .routes.main import main_bp
from .routes.auth import auth_bp
from .routes.user import user_bp
from dotenv import load_dotenv
from flask import Flask
import os

load_dotenv()

def create_app():
    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    login_manager.init_app(app)
    migrate.init_app(app, db)
    db.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(resume_bp)
    app.register_blueprint(job_app_bp)

    with app.app_context():
        db.create_all()

    return app

