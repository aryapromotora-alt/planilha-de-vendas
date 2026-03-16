import os
import logging
import urllib.parse
from flask import Flask, send_from_directory, render_template, session
from flask_cors import CORS

# Imports dos blueprints
from models.user import db
from routes.user import user_bp
from routes.data import data_bp
from routes.archive import archive_bp
from routes.resumo import resumo_bp  # dashboard
from routes.tv import tv_bp


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
    app.register_blueprint(tv_bp)

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
            employees = User.query.filter_by(role='user').order_by(User.order.asc(), User.id.asc()).all()
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
            employees = User.query.filter_by(role='user').order_by(User.order.asc(), User.id.asc()).all()
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
            from datetime import date
            
            META_TOTAL = 1500000
            DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            
            # Dicionário para armazenar os dados dos vendedores
            sellers_data = {}
            team_total = 0
            
            from models.archive import DailySales
            hoje = date.today()
            ano = hoje.year
            mes = hoje.month
            start_date = date(ano, mes, 3)
            end_date = date(ano, mes, 20)
            
            for seller_name in ['Jemima', 'Maiany', 'Nadia']:
                daily_sales = DailySales.query.filter(
                    DailySales.vendedor == seller_name,
                    DailySales.dia >= start_date,
                    DailySales.dia < hoje
                ).all()
                
                total_consolidado = sum(ds.total for ds in daily_sales)
                
                today_weekday = hoje.strftime('%A').lower()
                
                current_sale = Sale.query.filter_by(
                    employee_name=seller_name,
                    day=today_weekday,
                    sheet_type='portabilidade'
                ).first()
                
                valor_hoje = current_sale.value if current_sale else 0.0
                total_geral = total_consolidado + valor_hoje
                
                total_port = total_geral 
                total_novo = 0 
                
                team_total += total_geral
                
                sellers_data[seller_name] = {
                    'portabilidade': total_port,
                    'novo': total_novo,
                    'total': total_geral
                }
            
            meta_remaining = max(0, META_TOTAL - team_total)
            progress_percentage = min(100, (team_total / META_TOTAL) * 100)
            
            def format_currency(value):
                return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            return render_template(
                'meta_feriado.html',
                jemima_portabilidade=format_currency(sellers_data['Jemima']['portabilidade']),
                jemima_novo=format_currency(sellers_data['Jemima']['novo']),
                jemima_total=format_currency(sellers_data['Jemima']['total']),
                maiany_portabilidade=format_currency(sellers_data['Maiany']['portabilidade']),
                maiany_novo=format_currency(sellers_data['Maiany']['novo']),
                maiany_total=format_currency(sellers_data['Maiany']['total']),
                nadia_portabilidade=format_currency(sellers_data['Nadia']['portabilidade']),
                nadia_novo=format_currency(sellers_data['Nadia']['novo']),
                nadia_total=format_currency(sellers_data['Nadia']['total']),
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
            from models.archive import DailySales
            from flask import request
            from datetime import datetime, timedelta

            # Parâmetro de semana (formato YYYY-MM-DD da segunda-feira)
            week_start_str = request.args.get('week')
            
            employees = User.query.filter_by(role='user').order_by(User.order.asc(), User.id.asc()).all()
            
            # Buscar todas as semanas disponíveis no histórico
            available_weeks_raw = db.session.query(DailySales.dia).distinct().order_by(DailySales.dia.desc()).all()
            available_weeks = []
            seen_weeks = set()
            
            for d in available_weeks_raw:
                # Encontrar a segunda-feira daquela semana
                monday = d[0] - timedelta(days=d[0].weekday())
                if monday not in seen_weeks:
                    friday = monday + timedelta(days=4)
                    available_weeks.append({
                        "start": monday.isoformat(),
                        "label": f"{monday.strftime('%d/%m/%Y')} a {friday.strftime('%d/%m/%Y')}"
                    })
                    seen_weeks.add(monday)

            is_history = False
            selected_week_label = "Semana Atual"

            if week_start_str:
                try:
                    week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
                    week_end = week_start + timedelta(days=4)
                    is_history = True
                    selected_week_label = f"{week_start.strftime('%d/%m/%Y')} a {week_end.strftime('%d/%m/%Y')}"
                    
                    # Carregar dados do histórico (DailySales)
                    def get_history_data(s_type):
                        history_dados = []
                        for emp in employees:
                            # Buscar registros da semana para este vendedor e tipo
                            records = DailySales.query.filter(
                                DailySales.vendedor == emp.username,
                                DailySales.sheet_type == s_type,
                                DailySales.dia >= week_start,
                                DailySales.dia <= week_end
                            ).all()
                            
                            # Consolidar valores da semana (pode haver múltiplos registros por dia se salvou várias vezes, 
                            # mas a lógica do daily_save agora atualiza)
                            linha = {"nome": emp.username, "seg": 0, "ter": 0, "qua": 0, "qui": 0, "sex": 0, "total": 0}
                            for r in records:
                                linha["seg"] = max(linha["seg"], r.segunda)
                                linha["ter"] = max(linha["ter"], r.terca)
                                linha["qua"] = max(linha["qua"], r.quarta)
                                linha["qui"] = max(linha["qui"], r.quinta)
                                linha["sex"] = max(linha["sex"], r.sexta)
                            
                            linha["total"] = linha["seg"] + linha["ter"] + linha["qua"] + linha["qui"] + linha["sex"]
                            history_dados.append(linha)
                        return history_dados

                    dados_port = get_history_data('portabilidade')
                    dados_novo = get_history_data('novo')
                except Exception as e:
                    print(f"Erro ao processar data histórica: {e}")
                    week_start_str = None # Fallback para atual

            if not week_start_str:
                # Lógica original para semana atual (dados em tempo real)
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

            totais_port = {d: sum(l[d] for l in dados_port) for d in ["seg", "ter", "qua", "qui", "sex"]}
            totais_novo = {d: sum(l[d] for l in dados_novo) for d in ["seg", "ter", "qua", "qui", "sex"]}

            return render_template(
                "tabela_para_extracao.html",
                dados_port=dados_port,
                totais_port=totais_port,
                dados_novo=dados_novo,
                totais_novo=totais_novo,
                available_weeks=available_weeks,
                current_week=week_start_str,
                is_history=is_history,
                selected_week_label=selected_week_label
            )
        except Exception as e:
            print(f"Erro ao carregar dados para /export_table: {e}")
            return f"Erro Interno do Servidor: {e}", 500

    # ---------------------------
    # 🔧 ROTA TEMPORÁRIA PARA CORRIGIR A TABELA 'sales' — NOVO
    # ---------------------------
    @app.route("/fix-sales-table")
    def fix_sales_table():
        if 'user' not in session:
            return "❌ Acesso negado: faça login primeiro.", 403

        from sqlalchemy import text
        try:
            db.session.execute(text("""
                ALTER TABLE sales ADD COLUMN IF NOT EXISTS sheet_type VARCHAR(20) DEFAULT 'portabilidade';
            """))
            db.session.execute(text("""
                ALTER TABLE sales DROP CONSTRAINT IF EXISTS uq_employee_day;
            """))
            db.session.execute(text("""
                ALTER TABLE sales ADD CONSTRAINT uq_employee_day_sheet 
                UNIQUE (employee_name, day, sheet_type);
            """))
            db.session.commit()
            return """
            ✅ Sucesso! A tabela 'sales' foi atualizada.<br>
            • Coluna 'sheet_type' adicionada.<br>
            • Restrição única corrigida.<br>
            Agora a planilha 'NOVO' vai persistir os dados!<br>
            <a href="/">← Voltar</a>
            """, 200
        except Exception as e:
            db.session.rollback()
            return f"❌ Erro ao corrigir a tabela: {str(e)}", 500

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