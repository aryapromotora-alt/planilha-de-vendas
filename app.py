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
    # ✅ Define explicitamente onde estão os templates
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    )
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "asdf#FGSgvasgf$5$WGT")

    # Configurações para ambientes de produção com proxy reverso (Northflank)
    # Garante que os cookies de sessão funcionem corretamente em HTTPS
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PREFERRED_URL_SCHEME"] = "https"

    # Configuração para lidar com cabeçalhos de proxy (necessário para o Northflank)
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # ---------------------------
    # Configuração do banco de dados
    # ---------------------------
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith(("postgresql://", "postgres://")):
        parsed = urllib.parse.urlparse(db_url)
        safe_password = urllib.parse.quote_plus(parsed.password or "")
        db_url = f"{parsed.scheme}://{parsed.username}:{safe_password}@{parsed.hostname}:{parsed.port}{parsed.path}"
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
        print(f"🔗 Conectando ao banco PostgreSQL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    else:
        # Usar SQLite como padrão
        db_path = os.path.join(os.path.dirname(__file__), "database", "app.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        print(f"🔗 Usando banco SQLite: {app.config['SQLALCHEMY_DATABASE_URI']}")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Ativar logs SQL
    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    # Inicializa banco
    db.init_app(app)

    # 🔑 Cria as tabelas e garante que a coluna 'password' exista
    with app.app_context():
        # Primeiro, cria as tabelas se não existirem
        db.create_all()
        
        # Depois, garante que a coluna 'password' exista na tabela 'user'
        from sqlalchemy import text
        try:
            # Verifica se a coluna 'password' já existe
            result = db.session.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'password';
            """))
            if not result.fetchone():
                # Adiciona a coluna se não existir
                db.session.execute(text('ALTER TABLE "user" ADD COLUMN password VARCHAR(128) NOT NULL DEFAULT \'\';'))
                db.session.commit()
                print("✅ Coluna 'password' adicionada à tabela 'user'.")
            else:
                print("✅ Coluna 'password' já existe.")
        except Exception as e:
            print(f"⚠️ Erro ao verificar/criar coluna 'password': {e}")
        
        print("✅ Tabelas do banco verificadas/criadas com sucesso.")

    # ---------------------------
    # CORS
    # ---------------------------
    CORS(app, supports_credentials=True)

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
    # Rota pública /tv para exibição em telão (PORTABILIDADE)
    # ---------------------------
    @app.route("/tv")
    def tv():
        try:
            from models.sales import Sale  # Importa dentro da rota para evitar problemas de ciclo
            from models.user import User
            dados = []
            employees_from_db = User.query.filter_by(role='user').all()
            for emp in employees_from_db:
                nome = emp.username
                sales = Sale.query.filter_by(employee_name=nome).all()
                day_values = {s.day: s.value for s in sales}
                linha = {
                    "nome": nome,
                    "seg": day_values.get("monday", 0),
                    "ter": day_values.get("tuesday", 0),
                    "qua": day_values.get("wednesday", 0),
                    "qui": day_values.get("thursday", 0),
                    "sex": day_values.get("friday", 0),
                    "total": (
                        day_values.get("monday", 0) +
                        day_values.get("tuesday", 0) +
                        day_values.get("wednesday", 0) +
                        day_values.get("thursday", 0) +
                        day_values.get("friday", 0)
                    )
                }
                dados.append(linha)

            totais_diarios = {
                "seg": sum(linha["seg"] for linha in dados),
                "ter": sum(linha["ter"] for linha in dados),
                "qua": sum(linha["qua"] for linha in dados),
                "qui": sum(linha["qui"] for linha in dados),
                "sex": sum(linha["sex"] for linha in dados),
            }

            return render_template("tv.html", dados=dados, totais_diarios=totais_diarios)
        except Exception as e:
            # Em caso de erro de banco de dados ou outro erro, retorna uma mensagem de erro
            print(f"Erro ao carregar dados para /tv: {e}")
            return f"Erro Interno do Servidor ao carregar dados: {e}", 500

    # ---------------------------
    # Rota pública /tv/novo para exibição da planilha NOVO em telão
    # ---------------------------
    @app.route("/tv/novo")
    def tv_novo():
        try:
            from models.sales import Sale
            from models.user import User
            dados = []
            employees_from_db = User.query.filter_by(role='user').all()
            for emp in employees_from_db:
                nome = emp.username
                # ⚠️ FILTRO ESSENCIAL: só carrega dados da planilha NOVO
                sales = Sale.query.filter_by(employee_name=nome, sheet_type='novo').all()
                day_values = {s.day: s.value for s in sales}
                linha = {
                    "nome": nome,
                    "seg": day_values.get("monday", 0),
                    "ter": day_values.get("tuesday", 0),
                    "qua": day_values.get("wednesday", 0),
                    "qui": day_values.get("thursday", 0),
                    "sex": day_values.get("friday", 0),
                    "total": (
                        day_values.get("monday", 0) +
                        day_values.get("tuesday", 0) +
                        day_values.get("wednesday", 0) +
                        day_values.get("thursday", 0) +
                        day_values.get("friday", 0)
                    )
                }
                dados.append(linha)

            totais_diarios = {
                "seg": sum(linha["seg"] for linha in dados),
                "ter": sum(linha["ter"] for linha in dados),
                "qua": sum(linha["qua"] for linha in dados),
                "qui": sum(linha["qui"] for linha in dados),
                "sex": sum(linha["sex"] for linha in dados),
            }

            return render_template("tv_novo.html", dados=dados, totais_diarios=totais_diarios)
        except Exception as e:
            print(f"Erro ao carregar dados para /tv/novo: {e}")
            return f"Erro Interno do Servidor ao carregar dados: {e}", 500

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
            return send_from_directory(static_folder_path, "index.html")

    # ---------------------------
    # Rota para extração de dados
    # ---------------------------
    @app.route("/export_table")
    def export_table():
        try:
            from models.sales import Sale
            from models.user import User
            dados = []
            employees_from_db = User.query.filter_by(role='user').all()
            for emp in employees_from_db:
                nome = emp.username
                sales = Sale.query.filter_by(employee_name=nome).all()
                day_values = {s.day: s.value for s in sales}
                linha = {
                    "nome": nome,
                    "seg": day_values.get("monday", 0),
                    "ter": day_values.get("tuesday", 0),
                    "qua": day_values.get("wednesday", 0),
                    "qui": day_values.get("thursday", 0),
                    "sex": day_values.get("friday", 0),
                    "total": (
                        day_values.get("monday", 0) +
                        day_values.get("tuesday", 0) +
                        day_values.get("wednesday", 0) +
                        day_values.get("thursday", 0) +
                        day_values.get("friday", 0)
                    )
                }
                dados.append(linha)

            totais_diarios = {
                "seg": sum(linha["seg"] for linha in dados),
                "ter": sum(linha["ter"] for linha in dados),
                "qua": sum(linha["qua"] for linha in dados),
                "qui": sum(linha["qui"] for linha in dados),
                "sex": sum(linha["sex"] for linha in dados),
            }

            total_geral = (
                totais_diarios["seg"] +
                totais_diarios["ter"] +
                totais_diarios["qua"] +
                totais_diarios["qui"] +
                totais_diarios["sex"]
            )

            return render_template(
                "tabela_para_extracao.html",
                dados=dados,
                totais_diarios=totais_diarios,
                total_geral=total_geral
            )
        except Exception as e:
            # Em caso de erro de banco de dados ou outro erro, retorna uma mensagem de erro
            print(f"Erro ao carregar dados para /export_table: {e}")
            return f"Erro Interno do Servidor ao carregar dados: {e}", 500

    # ---------------------------
    # FINAL: retorna a aplicação
    # ---------------------------
    return app