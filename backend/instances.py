from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

login_manager = LoginManager()

@login_manager.user_loader
def user_loader(user_id):
    if user_id:
        return None
    return None

migrate = Migrate()
db = SQLAlchemy()
