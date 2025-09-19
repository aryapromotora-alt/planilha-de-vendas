from flask import Blueprint, jsonify, current_app, request, render_template
from datetime import datetime, timedelta, date
from models.user import db
from models.archive import ResumoHistory, DailySales
from routes.data import load_data, save_data

archive_bp = Blueprint('archive', __name__)

# ✅ Filtro local para formato brasileiro
def format_brl(value):
    try:
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"

# ---------------------------
# Rota para arquivar semana (Resumo)
# ---------------------------
@archive_bp.route('/api/resumo-archive', methods=['POST'])
def resumo_archive():
    """
    Fecha a semana (Resumo):
    - Salva totais no banco
    - Zera a planilha
    """
    secret = current_app.config.get('RESUMO_ARCHIVE_SECRET')
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
            valores.get("monday", 0) or 0,
            valores.get("tuesday", 0) or 0,
            valores.get("wednesday", 0) or 0,
            valores.get("thursday", 0) or 0,
            valores.get("friday", 0) or 0,
        ])
        total += soma
        per_seller.append({"seller": nome, "total": soma})

    # intervalo da semana (seg a sex)
    now = datetime.utcnow()
    start = now - timedelta(days=now.weekday())   # segunda
    end = start + timedelta(days=4)               # sexta
    week_label = f"{start.date()} a {end.date()}"

    # salva no banco
    history = ResumoHistory(
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

    return jsonify({
        "status": "ok",
        "resumo": week_label,
        "total": format_brl(total)  # ✅ formato brasileiro aplicado
    })

# ---------------------------
# Rota para salvar vendas diárias no banco
# ---------------------------
@archive_bp.route('/api/daily-save', methods=['POST'])
def daily_save():
    """
    Salva o estado atual da planilha no banco (DailySales).
    Pode ser chamado 1x por dia (scheduler) ou manualmente.
    """
    data = load_data()
    spreadsheet = data.get("spreadsheetData", {})

    today = date.today()
    for nome, valores in spreadsheet.items():
        record = DailySales(
            vendedor=nome,
            dia=today,
            segunda=valores.get("monday", 0) or 0,
            terca=valores.get("tuesday", 0) or 0,
            quarta=valores.get("wednesday", 0) or 0,
            quinta=valores.get("thursday", 0) or 0,
            sexta=valores.get("friday", 0) or 0,
            total=(valores.get("monday", 0) or 0) +
                  (valores.get("tuesday", 0) or 0) +
                  (valores.get("wednesday", 0) or 0) +
                  (valores.get("thursday", 0) or 0) +
                  (valores.get("friday", 0) or 0),
        )
        db.session.add(record)

    db.session.commit()
    return jsonify({"status": "ok", "date": today.isoformat()})

# ---------------------------
# Rota para consultar histórico diário em JSON
# ---------------------------
@archive_bp.route('/api/daily-history', methods=['GET'])
def get_daily_history():
    """
    Retorna o histórico diário salvo no banco
    """
    records = DailySales.query.order_by(DailySales.created_at.desc()).all()
    return jsonify([r.to_dict() for r in records])

# ---------------------------
# Página HTML com histórico (Resumo)
# ---------------------------
@archive_bp.route('/resumo', methods=['GET'])
def resumo_page():
    history = ResumoHistory.query.order_by(ResumoHistory.created_at.desc()).all()
    return render_template("resumo.html", history=history)

# ---------------------------
# Rota JSON do histórico (Resumo)
# ---------------------------
@archive_bp.route('/api/resumo-history', methods=['GET'])
def get_resumo_history():
    history = ResumoHistory.query.order_by(ResumoHistory.created_at.desc()).all()
    return jsonify([h.to_dict() for h in history])