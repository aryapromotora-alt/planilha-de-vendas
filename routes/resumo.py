# routes/resumo.py
from flask import Blueprint, render_template
from datetime import datetime, timedelta
from models.archive import DailySales
from sqlalchemy import extract

# Nome do blueprint deve ser o mesmo usado no app.register_blueprint()
resumo_bp = Blueprint("resumo", __name__)

@resumo_bp.route("/resumo")
def resumo_page():
    hoje = datetime.utcnow().date()

    # --- Totais do dia ---
    registros_hoje = DailySales.query.filter_by(dia=hoje).all()
    total_dia = sum(r.total for r in registros_hoje)

    # --- Totais da semana ---
    inicio_semana = hoje - timedelta(days=hoje.weekday())   # segunda
    fim_semana = inicio_semana + timedelta(days=4)          # sexta
    registros_semana = DailySales.query.filter(
        DailySales.dia >= inicio_semana,
        DailySales.dia <= fim_semana
    ).all()
    total_semana = sum(r.total for r in registros_semana)

    # --- Totais do mês ---
    mes_atual = hoje.month
    ano_atual = hoje.year
    registros_mes = DailySales.query.filter(
        extract("month", DailySales.dia) == mes_atual,
        extract("year", DailySales.dia) == ano_atual
    ).all()
    total_mes = sum(r.total for r in registros_mes)

    # --- Histórico diário (últimos 5 dias úteis da semana) ---
    dias_labels = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
    historico_diario = {}
    for i, label in enumerate(dias_labels):
        dia_atual = inicio_semana + timedelta(days=i)
        registros_dia = DailySales.query.filter_by(dia=dia_atual).all()
        historico_diario[label] = sum(r.total for r in registros_dia)

    # --- Totais semanais do mês ---
    totais_semanais = [0, 0, 0, 0]  # 4 semanas
    for r in registros_mes:
        semana_num = (r.dia.day - 1) // 7  # divisão inteira
        if semana_num < 4:
            totais_semanais[semana_num] += r.total

    return render_template(
        "resumo.html",
        hoje=hoje,
        total_dia=total_dia,
        total_semana=total_semana,
        total_mes=total_mes,
        total_seg=historico_diario.get("Segunda", 0),
        total_ter=historico_diario.get("Terça", 0),
        total_qua=historico_diario.get("Quarta", 0),
        total_qui=historico_diario.get("Quinta", 0),
        total_sex=historico_diario.get("Sexta", 0),
        total_sem1=totais_semanais[0],
        total_sem2=totais_semanais[1],
        total_sem3=totais_semanais[2],
        total_sem4=totais_semanais[3],
    )
