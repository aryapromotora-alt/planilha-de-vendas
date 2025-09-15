import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, render_template
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.data import data_bp, load_data
from src.routes.archive import archive_bp

# ==========================
# Inicializa o app Flask
# ==========================
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "asdf#FGSgvasgf$5$WGT")

# Configurar CORS
CORS(app)

# ==========================
# Configuração do banco
# ==========================
db_url = os.getenv("DATABASE_URL")  # Render cria essa variável automaticamente

if db_url:
    # Render usa postgres://, mas SQLAlchemy espera postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
    # fallback para SQLite em desenvolvimento local
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializa banco
db.init_app(app)
with app.app_context():
    db.create_all()

# ==========================
# Registrar Blueprints
# ==========================
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(data_bp, url_prefix='/api')
app.register_blueprint(archive_bp, url_prefix='/api')

# ==========================
# Rotas
# ==========================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve arquivos estáticos ou index.html"""
    static_folder_path = app.static_folder
    if not static_folder_path:
        return "Static folder not configured", 404

    if path and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)

    index_path = os.path.join(static_folder_path, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(static_folder_path, 'index.html')
    return "index.html not found", 404


@app.route('/tv')
def tv_page():
    """Página de TV com totais diários"""
    data = load_data()
    spreadsheet = data.get("spreadsheetData", {})

    dados = []
    totais_diarios = {"seg": 0, "ter": 0, "qua": 0, "qui": 0, "sex": 0}

    for nome, valores in spreadsheet.items():
        seg = valores.get("monday", 0) or 0
        ter = valores.get("tuesday", 0) or 0
        qua = valores.get("wednesday", 0) or 0
        qui = valores.get("thursday", 0) or 0
        sex = valores.get("friday", 0) or 0
        total = seg + ter + qua + qui + sex

        try:
            ordem = int(valores.get("ordem", 999))
        except (ValueError, TypeError):
            ordem = 999

        dados.append({
            "nome": nome,
            "seg": seg,
            "ter": ter,
            "qua": qua,
            "qui": qui,
            "sex": sex,
            "total": total,
            "ordem": ordem
        })

        totais_diarios["seg"] += seg
        totais_diarios["ter"] += ter
        totais_diarios["qua"] += qua
        totais_diarios["qui"] += qui
        totais_diarios["sex"] += sex

    # Ordena pela ordem definida
    dados = sorted(dados, key=lambda x: x["ordem"])

    return render_template('tv.html', dados=dados, totais_diarios=totais_diarios)


# ==========================
# Rota pública /weekly
# ==========================
@app.route('/weekly')
def weekly_page():
    try:
        from src.models.archive import WeeklyHistory  # importa dentro da função

        records = WeeklyHistory.query.order_by(WeeklyHistory.created_at.desc()).all()

        history = []
        for r in records:
            history.append({
                "week_label": r.week_label,
                "started_at": r.started_at.isoformat() if r.started_at else "",
                "ended_at": r.ended_at.isoformat() if r.ended_at else "",
                "total": r.total,
                "breakdown": r.breakdown,
                "created_at": r.created_at.isoformat() if r.created_at else ""
            })

        # Dados padrão para não quebrar os gráficos
        vendedores = []
        totais_semana = []
        semanas_mes = ["Semana 1", "Semana 2", "Semana 3", "Semana 4"]
        totais_mes = [0, 0, 0, 0]
        total_dia = 0

        return render_template(
            "weekly.html",
            history=history,
            vendedores=vendedores,
            totais_semana=totais_semana,
            semanas_mes=semanas_mes,
            totais_mes=totais_mes,
            total_dia=total_dia
        )

    except Exception:
        import traceback
        return f"<h2>Erro ao renderizar /weekly</h2><pre>{traceback.format_exc()}</pre>", 500


# ==========================
# Main
# ==========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=True)
