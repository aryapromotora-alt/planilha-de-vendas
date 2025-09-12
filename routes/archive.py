from flask import Blueprint, jsonify, current_app, request, render_template
from datetime import datetime, timedelta
from src.models.user import db  # já temos o db inicializado
from src.models.archive import WeeklyHistory  # model do histórico semanal
from .data import load_data, save_data

archive_bp = Blueprint('archive', __name__)


# ---------------------------
# Rota para arquivar semana
# ---------------------------
@archive_bp.route('/api/weekly-archive', methods=['POST'])
def weekly_archive():
    """
    Fecha a semana:
    - Salva totais no banco
    - Zera a planilha
    """
    # segurança opcional com secret key
    secret = current_app.config.get('WEEKLY_ARCHIVE_SECRET')
    header = request.headers.get('X-SECRET-KEY')
    if secret and header != secret:
        return jsonify({"error": "unauthorized"}), 401

    data = load_data()
    spreadsheet = data.get("spreadsheetData", {})

    # total por vendedor
    per_seller = []
    total = 0
    for nome, valores in spreadsheet.items():
        soma = sum([
            valores.get("monday", 0),
            valores.get("tuesday", 0),
            valores.get("wednesday", 0),
            valores.get("thursday", 0),
            valores.get("friday", 0),
        ])
        total += soma
        per_seller.append({"seller": nome, "total": soma})

    # intervalo da semana (seg a sex)
    now = datetime.utcnow()
    start = now - timedelta(days=now.weekday())   # segunda
    end = start + timedelta(days=4)               # sexta
    week_label = f"{start.date()} a {end.date()}"

    # salva no banco
    history = WeeklyHistory(
        week_label=week_label,
        started_at=start.date(),
        ended_at=end.date(),
        total=total,
        breakdown=per_seller
    )
    db.session.add(history)
    db.session.commit()

    # zera planilha
    for nome, valores in spreadsheet.items():
        valores["monday"] = 0
        valores["tuesday"] = 0
        valores["wednesday"] = 0
        valores["thursday"] = 0
        valores["friday"] = 0
    save_data(data)

    return jsonify({"status": "ok", "week": week_label, "total": total})


# ---------------------------
# Rota para visualizar histórico no navegador (HTML)
# ---------------------------
@archive_bp.route('/weekly', methods=['GET'])
def weekly_page():
    """
    Mostra o histórico semanal em uma página HTML
    """
    history = WeeklyHistory.query.order_by(WeeklyHistory.created_at.desc()).all()
    return render_template("weekly.html", history=history)


# ---------------------------
# Rota para retornar histórico em JSON (API)
# ---------------------------
@archive_bp.route('/api/weekly-history', methods=['GET'])
def get_weekly_history():
    """
    Retorna o histórico semanal em formato JSON
    """
    history = WeeklyHistory.query.order_by(WeeklyHistory.created_at.desc()).all()
    return jsonify([h.to_dict() for h in history])
