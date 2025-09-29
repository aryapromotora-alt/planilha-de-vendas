from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from models.user import User

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")  # ou configure manualmente

    db.init_app(app)

    # 🔐 Inicializa o LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app