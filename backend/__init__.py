from .instances import login_manager, migrate, db
from .routes.main import main_bp
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

    with app.app_context():
        db.create_all()

    return app

