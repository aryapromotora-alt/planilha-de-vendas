from flask import Blueprint, jsonify, current_app, request, render_template
from datetime import datetime, timedelta, date
from models.user import db
from models.archive import ResumoHistory, DailySales
from routes.data import load_data, save_data
from pytz import timezone  # ✅ Import necessário para timezone

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
    Salva apenas o valor do dia atual da semana.
    """
    data = load_data()
    spreadsheet = data.get("spreadsheetData", {})
    
    # Mapeamento de dias da semana (0=segunda, 4=sexta)
    dias_semana = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    nomes_dias = ["segunda", "terca", "quarta", "quinta", "sexta"]
    
    # Pega o dia da semana atual (0=segunda, 1=terça, etc.)
    hoje = datetime.now(timezone("America/Sao_Paulo"))
    dia_semana = hoje.weekday()  # 0=segunda, 1=terça, ..., 4=sexta
    today = hoje.date()
    
    # Verifica se é fim de semana
    if dia_semana >= 5:  # sábado=5, domingo=6
        return jsonify({"status": "weekend", "message": "Fim de semana - não salva"}), 200
    
    # Pega o campo correspondente ao dia atual
    campo_dia = dias_semana[dia_semana]
    nome_dia = nomes_dias[dia_semana]
    
    print(f"[INFO] Salvando daily-save para {nome_dia} ({today})")
    
    total_dia = 0
    for nome, valores in spreadsheet.items():
        valor_dia = float(valores.get(campo_dia, 0) or 0)
        total_dia += valor_dia
        
        record = DailySales(
            vendedor=nome,
            dia=today,
            segunda=valor_dia if nome_dia == "segunda" else 0,
            terca=valor_dia if nome_dia == "terca" else 0,
            quarta=valor_dia if nome_dia == "quarta" else 0,
            quinta=valor_dia if nome_dia == "quinta" else 0,
            sexta=valor_dia if nome_dia == "sexta" else 0,
            total=valor_dia
        )
        db.session.add(record)

    db.session.commit()
    return jsonify({
        "status": "ok", 
        "date": today.isoformat(),
        "day": nome_dia,
        "total": format_brl(total_dia)
    })

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