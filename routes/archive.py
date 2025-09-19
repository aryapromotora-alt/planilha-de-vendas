from flask import Blueprint, jsonify, current_app, request, render_template
from datetime import datetime, timedelta, date
from sqlalchemy import extract
from calendar import monthrange
from collections import defaultdict
from models.user import db
from models.archive import DailySales, ResumoHistory
from routes.data import load_data, save_data

# Blueprint unificado
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# ---------------------------
# Filtro local para formato brasileiro
# ---------------------------
def format_brl(value):
    try:
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"

# ---------------------------
# Salvar vendas diárias no banco
# ---------------------------
@dashboard_bp.route('/api/daily-save', methods=['POST'])
def daily_save():
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
# Arquivar semana
# ---------------------------
@dashboard_bp.route('/api/resumo-archive', methods=['POST'])
def resumo_archive():
    secret = current_app.config.get('RESUMO_ARCHIVE_SECRET')
    header = request.headers.get('X-SECRET-KEY')
    if secret and header != secret:
        return jsonify({"error": "unauthorized"}), 401

    data = load_data()
    spreadsheet = data.get("spreadsheetData", {})

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

    now = datetime.utcnow()
    start = now - timedelta(days=now.weekday())
    end = start + timedelta(days=4)
    week_label = f"{start.date()} a {end.date()}"

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
        for day in ["monday","tuesday","wednesday","thursday","friday"]:
            valores[day] = 0
    save_data(data)

    return jsonify({"status": "ok", "resumo": week_label, "total": format_brl(total)})

# ---------------------------
# Histórico diário JSON
# ---------------------------
@dashboard_bp.route('/api/daily-history', methods=['GET'])
def get_daily_history():
    records = DailySales.query.order_by(DailySales.created_at.desc()).all()
    return jsonify([r.to_dict() for r in records])

# ---------------------------
# Histórico semanal JSON
# ---------------------------
@dashboard_bp.route('/api/resumo-history', methods=['GET'])
def get_resumo_history():
    history = ResumoHistory.query.order_by(ResumoHistory.created_at.desc()).all()
    return jsonify([h.to_dict() for h in history])

# ---------------------------
# Dashboard HTML
# ---------------------------
@dashboard_bp.route('/resumo', methods=['GET'])
def resumo_page():
    hoje = datetime.utcnow().date()
    ano = hoje.year
    mes = hoje.month

    # Totais do dia
    registros_hoje = DailySales.query.filter_by(dia=hoje).all()
    total_dia = sum(r.total for r in registros_hoje)

    # Totais semana (Seg-Sex)
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=4)
    registros_semana = DailySales.query.filter(
        DailySales.dia >= inicio_semana,
        DailySales.dia <= fim_semana
    ).all()
    total_semana = sum(r.total for r in registros_semana)

    # Totais do mês
    registros_mes = DailySales.query.filter(
        extract("month", DailySales.dia) == mes,
        extract("year", DailySales.dia) == ano
    ).all()
    total_mes = sum(r.total for r in registros_mes)

    # Histórico diário
    dias_labels = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
    historico_diario = {}
    for i, label in enumerate(dias_labels):
        dia_atual = inicio_semana + timedelta(days=i)
        registros_dia = DailySales.query.filter_by(dia=dia_atual).all()
        historico_diario[label] = sum(r.total for r in registros_dia)

    # Totais semanais do mês
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, monthrange(ano, mes)[1])
    dias_no_mes = (ultimo_dia - primeiro_dia).days + 1
    num_semanas = ((dias_no_mes + primeiro_dia.weekday()) // 7) + 1

    totais_mes = [0 for _ in range(num_semanas)]
    for r in registros_mes:
        semana_index = ((r.dia.day + primeiro_dia.weekday() - 1) // 7)
        if 0 <= semana_index < num_semanas:
            totais_mes[semana_index] += r.total

    mes_atual = f"{ano}-{mes:02d}"

    # Histórico mensal completo
    historico_mensal = defaultdict(float)
    for r in DailySales.query.all():
        chave = f"{r.dia.year}-{r.dia.month:02d}"
        historico_mensal[chave] += r.total
    historico_mensal = dict(sorted(historico_mensal.items()))

    anos_disponiveis = list(range(2025, 2031))
    meses_nomes = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    return render_template(
        "resumo.html",
        hoje=hoje,
        total_dia=format_brl(total_dia),
        total_semana=format_brl(total_semana),
        total_mes=format_brl(total_mes),
        total_seg=format_brl(historico_diario.get("Segunda", 0)),
        total_ter=format_brl(historico_diario.get("Terça", 0)),
        total_qua=format_brl(historico_diario.get("Quarta", 0)),
        total_qui=format_brl(historico_diario.get("Quinta", 0)),
        total_sex=format_brl(historico_diario.get("Sexta", 0)),
        totais_mes=[format_brl(v) for v in totais_mes],
        num_semanas=num_semanas,
        mes_atual=mes_atual,
        historico_mensal={k: format_brl(v) for k, v in historico_mensal.items()},
        anos_disponiveis=anos_disponiveis,
        meses_nomes=meses_nomes
    )
