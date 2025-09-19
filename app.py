import os
import logging
import urllib.parse
from flask import Flask, send_from_directory, render_template
from flask_cors import CORS

# Imports dos blueprints
from models.user import db
from routes.user import user_bp
from routes.data import data_bp
from routes.archive import archive_bp
from routes.resumo import resumo_bp  # dashboard

def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), 'static')
    )
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "asdf#FGSgvasgf$5$WGT")

    # ---------------------------
    # Configuração do banco de dados
    # ---------------------------
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        parsed = urllib.parse.urlparse(db_url)
        safe_password = urllib.parse.quote_plus(parsed.password or "")
        db_url = f"{parsed.scheme}://{parsed.username}:{safe_password}@{parsed.hostname}:{parsed.port}{parsed.path}"
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
        print(f"🔗 Conectando ao banco: {app.config['SQLALCHEMY_DATABASE_URI']}")
    else:
        raise RuntimeError("DATABASE_URL não configurado — verifique variáveis de ambiente.")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Ativar logs SQL
    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    # Inicializa banco
    db.init_app(app)

    # ---------------------------
    # CORS
    # ---------------------------
    CORS(app)

    # ---------------------------
    # Registrar blueprints
    # ---------------------------
    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(data_bp, url_prefix="/api")
    app.register_blueprint(archive_bp, url_prefix="/archive")  # API de arquivamento
    app.register_blueprint(resumo_bp)  # Dashboard /resumo

    # ---------------------------
    # Filtro Jinja moeda brasileira
    # ---------------------------
    @app.template_filter('format_brl')
    def format_brl(value):
        try:
            return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return "0,00"

    # ---------------------------
    # Rota para verificar banco
    # ---------------------------
    @app.route("/db-check")
    def db_check():
        return f"Banco em uso: {app.config['SQLALCHEMY_DATABASE_URI']}"

    # ---------------------------
    # Rotas estáticas / SPA
    # ---------------------------
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve(path):
        static_folder_path = app.static_folder
        if not static_folder_path:
            return "Static folder not configured", 404

        full_path = os.path.join(static_folder_path, path)
        if path and os.path.exists(full_path):
            return send_from_directory(static_folder_path, path)
