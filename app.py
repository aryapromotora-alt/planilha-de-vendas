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
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PREFERRED_URL_SCHEME"] = "https"

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
        db_path = os.path.join(os.path.dirname(__file__), "database", "app.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        print(f"🔗 Usando banco SQLite: {app.config['SQLALCHEMY_DATABASE_URI']}")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        from sqlalchemy import text
        try:
            result = db.session.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'password';
            """))
            if not result.fetchone():
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
    app.register_blueprint(archive_bp, url_prefix="/archive")
    app.register_blueprint(resumo_bp)

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
    # Rota pública /tv (PORTABILIDADE)
    # ---------------------------
    @app.route("/tv")
    def tv():
        try:
            from models.sales import Sale
            from models.user import User
            employees = User.query.filter_by(role='user').all()
            dados = []
            for emp in employees:
                nome = emp.username
                sales = Sale.query.filter_by(employee_name=nome, sheet_type='portabilidade').all()
                day_values = {s.day: s.value for s in sales}
                linha = {
                    "nome": nome,
                    "seg": day_values.get("monday", 0),
                    "ter": day_values.get("tuesday", 0),
                    "qua": day_values.get("wednesday", 0),
                    "qui": day_values.get("thursday", 0),
                    "sex": day_values.get("friday", 0),
                    "total": sum(day_values.get(d, 0) for d in ["monday", "tuesday", "wednesday", "thursday", "friday"])
                }
                dados.append(linha)

            totais_diarios = {
                "seg": sum(l["seg"] for l in dados),
                "ter": sum(l["ter"] for l in dados),
                "qua": sum(l["qua"] for l in dados),
                "qui": sum(l["qui"] for l in dados),
                "sex": sum(l["sex"] for l in dados),
            }

            return render_template("tv.html", dados=dados, totais_diarios=totais_diarios)
        except Exception as e:
            print(f"Erro ao carregar dados para /tv: {e}")
            return f"Erro Interno do Servidor: {e}", 500

    # ---------------------------
    # Rota pública /tv/novo (NOVO)
    # ---------------------------
    @app.route("/tv/novo")
    def tv_novo():
        try:
            from models.sales import Sale
            from models.user import User
            employees = User.query.filter_by(role='user').all()
            dados = []
            for emp in employees:
                nome = emp.username
                sales = Sale.query.filter_by(employee_name=nome, sheet_type='novo').all()
                day_values = {s.day: s.value for s in sales}
                linha = {
                    "nome": nome,
                    "seg": day_values.get("monday", 0),
                    "ter": day_values.get("tuesday", 0),
                    "qua": day_values.get("wednesday", 0),
                    "qui": day_values.get("thursday", 0),
                    "sex": day_values.get("friday", 0),
                    "total": sum(day_values.get(d, 0) for d in ["monday", "tuesday", "wednesday", "thursday", "friday"])
                }
                dados.append(linha)

            totais_diarios = {
                "seg": sum(l["seg"] for l in dados),
                "ter": sum(l["ter"] for l in dados),
                "qua": sum(l["qua"] for l in dados),
                "qui": sum(l["qui"] for l in dados),
                "sex": sum(l["sex"] for l in dados),
            }

            return render_template("tv_novo.html", dados=dados, totais_diarios=totais_diarios)
        except Exception as e:
            print(f"Erro ao carregar dados para /tv/novo: {e}")
            return f"Erro Interno do Servidor: {e}", 500

    # ---------------------------
    # Rota pública /meta-feriado (META FERIADO 21/11)
    # ---------------------------
    @app.route("/meta-feriado")
    def meta_feriado():
        try:
            from models.sales import Sale
            from models.user import User
            
            META_TOTAL = 1500000
            DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            
            # Dicionário para armazenar os dados dos vendedores
            sellers_data = {}
            team_total = 0
            
            # Buscar dados de JEMIMA, MAIANY e NADIA
            for seller_name in ['jemima', 'maiany', 'nadia']:
                # Buscar dados de Portabilidade
                sales_port = Sale.query.filter_by(
                    employee_name=seller_name,
                    sheet_type='portabilidade'
                ).all()
                day_values_port = {s.day: s.value for s in sales_port}
                total_port = sum(day_values_port.get(d, 0) for d in DAYS)
                
                # Buscar dados de Novo
                sales_novo = Sale.query.filter_by(
                    employee_name=seller_name,
                    sheet_type='novo'
                ).all()
                day_values_novo = {s.day: s.value for s in sales_novo}
                total_novo = sum(day_values_novo.get(d, 0) for d in DAYS)
                
                # Total geral do vendedor
                total_geral = total_port + total_novo
                team_total += total_geral
                
                sellers_data[seller_name] = {
                    'portabilidade': total_port,
                    'novo': total_novo,
                    'total': total_geral
                }
            
            # Calcular meta restante e percentual
            meta_remaining = max(0, META_TOTAL - team_total)
            progress_percentage = min(100, (team_total / META_TOTAL) * 100)
            
            # Formatar valores em moeda
            def format_currency(value):
                return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            return render_template(
                'meta_feriado.html',
                jemima_portabilidade=format_currency(sellers_data['jemima']['portabilidade']),
                jemima_novo=format_currency(sellers_data['jemima']['novo']),
                jemima_total=format_currency(sellers_data['jemima']['total']),
                maiany_portabilidade=format_currency(sellers_data['maiany']['portabilidade']),
                maiany_novo=format_currency(sellers_data['maiany']['novo']),
                maiany_total=format_currency(sellers_data['maiany']['total']),
                nadia_portabilidade=format_currency(sellers_data['nadia']['portabilidade']),
                nadia_novo=format_currency(sellers_data['nadia']['novo']),
                nadia_total=format_currency(sellers_data['nadia']['total']),
                team_total=format_currency(team_total),
                meta_remaining=format_currency(meta_remaining),
                progress_percentage=round(progress_percentage, 2)
            )
        except Exception as e:
            print(f"Erro ao carregar dados para /meta-feriado: {e}")
            return f"Erro Interno do Servidor: {e}", 500

    # ---------------------------
    # Rota para extração de dados (PORTABILIDADE + NOVO)
    # ---------------------------
    @app.route("/export_table")
    def export_table():
        try:
            from models.sales import Sale
            from models.user import User
            employees = User.query.filter_by(role='user').all()

            # --- PORTABILIDADE ---
            dados_port = []
            for emp in employees:
                nome = emp.username
                sales = Sale.query.filter_by(employee_name=nome, sheet_type='portabilidade').all()
                day_values = {s.day: s.value for s in sales}
                linha = {
                    "nome": nome,
                    "seg": day_values.get("monday", 0),
                    "ter": day_values.get("tuesday", 0),
                    "qua": day_values.get("wednesday", 0),
                    "qui": day_values.get("thursday", 0),
                    "sex": day_values.get("friday", 0),
                    "total": sum(day_values.get(d, 0) for d in ["monday", "tuesday", "wednesday", "thursday", "friday"])
                }
                dados_port.append(linha)

            totais_port = {d: sum(l[d] for l in dados_port) for d in ["seg", "ter", "qua", "qui", "sex"]}

            # --- NOVO ---
            dados_novo = []
            for emp in employees:
                nome = emp.username
                sales = Sale.query.filter_by(employee_name=nome, sheet_type='novo').all()
                day_values = {s.day: s.value for s in sales}
                linha = {
                    "nome": nome,
                    "seg": day_values.get("monday", 0),
                    "ter": day_values.get("tuesday", 0),
                    "qua": day_values.get("wednesday", 0),
                    "qui": day_values.get("thursday", 0),
                    "sex": day_values.get("friday", 0),
                    "total": sum(day_values.get(d, 0) for d in ["monday", "tuesday", "wednesday", "thursday", "friday"])
                }
                dados_novo.append(linha)

            totais_novo = {d: sum(l[d] for l in dados_novo) for d in ["seg", "ter", "qua", "qui", "sex"]}

            return render_template(
                "tabela_para_extracao.html",
                dados_port=dados_port,
                totais_port=totais_port,
                dados_novo=dados_novo,
                totais_novo=totais_novo
            )
        except Exception as e:
            print(f"Erro ao carregar dados para /export_table: {e}")
            return f"Erro Interno do Servidor: {e}", 500

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

    return app