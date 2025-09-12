import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, render_template, request, session, redirect
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.data import data_bp, load_data  # importa a função que carrega os dados reais
from src.routes.archive import archive_bp

# Inicializa o app
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Configurar CORS
CORS(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(data_bp, url_prefix='/api')
app.register_blueprint(archive_bp, url_prefix='/api')

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

# Rotas
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/tv')
def tv_page():
    data = load_data()
    spreadsheet = data.get("spreadsheetData", {})

    dados = []
    totais_diarios = {
        "seg": 0,
        "ter": 0,
        "qua": 0,
        "qui": 0,
        "sex": 0
    }

    for nome, valores in spreadsheet.items():
        seg = valores.get("monday", 0)
        ter = valores.get("tuesday", 0)
        qua = valores.get("wednesday", 0)
        qui = valores.get("thursday", 0)
        sex = valores.get("friday", 0)
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

    # ordena dinamicamente pela ordem definida no painel
    dados = sorted(dados, key=lambda x: x["ordem"])

    return render_template('tv.html', dados=dados, totais_diarios=totais_diarios)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
