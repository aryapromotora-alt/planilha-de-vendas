import os
import json
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
    # ✅ Define explicitamente onde estão os templates
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    )
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "asdf#FGSgvasgf$5$WGT")

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
        raise RuntimeError(
            "DATABASE_URL não configurado — verifique variáveis de ambiente."
        )

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
    @app.template_filter("format_brl")
    def format_brl(value):
        try:
            return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace(
                "X", "."
            )
        except (ValueError, TypeError):
            return "0,00"

    # ---------------------------
    # Rota para verificar banco
    # ---------------------------
    @app.route("/db-check")
    def db_check():
        return f"Banco em uso: {app.config['SQLALCHEMY_DATABASE_URI']}"

    # ---------------------------
    # Função para carregar dados da planilha (copiada de routes/data.py)
    # ---------------------------
    def load_spreadsheet_data():
        DATA_FILE = os.path.join(os.path.dirname(__file__), "database", "planilha_data.json")
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Gerar campo 'ordem' com base na posição dos nomes em employees
                    ordem_map = {emp["name"]: i for i, emp in enumerate(data.get("employees", []), start=1)}
                    for nome, valores in data.get("spreadsheetData", {}).items():
                        valores["ordem"] = ordem_map.get(nome, 999)

                    return data
            except (json.JSONDecodeError, IOError):
                pass

        # Dados padrão se o arquivo não existir ou estiver corrompido
        # ❌ NÃO inclui "admin" aqui porque ele não é vendedor
        default_employees = [
            {"name": "Anderson", "password": "123"},
            {"name": "Vitoria", "password": "123"},
            {"name": "Jemima", "password": "123"},
            {"name": "Maiany", "password": "123"},
            {"name": "Fernanda", "password": "123"},
            {"name": "Nadia", "password": "123"},
            {"name": "Giovana", "password": "123"}
        ]

        spreadsheet = {
            emp["name"]: {
                "monday": 0,
                "tuesday": 0,
                "wednesday": 0,
                "thursday": 0,
                "friday": 0,
                "ordem": i + 1
            }
            for i, emp in enumerate(default_employees)
        }

        return {
            "employees": default_employees,
            "spreadsheetData": spreadsheet
        }

    # ---------------------------
    # Rota pública /tv para exibição em telão
    # ---------------------------
    @app.route("/tv")
    def tv():
        # Carrega dados reais do arquivo JSON
        data = load_spreadsheet_data()

        # Transforma os dados para o formato esperado pelo template tv.html
        dados = []
        for emp in data.get("employees", []):
            nome = emp["name"]
            valores = data["spreadsheetData"].get(nome, {})
            linha = {
                "nome": nome,
                "seg": valores.get("monday", 0),
                "ter": valores.get("tuesday", 0),
                "qua": valores.get("wednesday", 0),
                "qui": valores.get("thursday", 0),
                "sex": valores.get("friday", 0),
                "total": (
                    valores.get("monday", 0) +
                    valores.get("tuesday", 0) +
                    valores.get("wednesday", 0) +
                    valores.get("thursday", 0) +
                    valores.get("friday", 0)
                )
            }
            dados.append(linha)

        # Calcula totais diários
        totais_diarios = {
            "seg": sum(linha["seg"] for linha in dados),
            "ter": sum(linha["ter"] for linha in dados),
            "qua": sum(linha["qua"] for linha in dados),
            "qui": sum(linha["qui"] for linha in dados),
            "sex": sum(linha["sex"] for linha in dados),
        }

        return render_template("tv.html", dados=dados, totais_diarios=totais_diarios)

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
        else:
            # sempre renderiza o index.html da SPA
            return send_from_directory(static_folder_path, "index.html")

    # ---------------------------
    # FINAL: retorna a aplicação
    # ---------------------------
    return app