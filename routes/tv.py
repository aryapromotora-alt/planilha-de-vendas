from flask import Blueprint, render_template
from models.user import User
from models.sales import Sale  # Usa o modelo Sale (com sheet_type)
from datetime import date

tv_bp = Blueprint('tv', __name__)

@tv_bp.route('/tv')
def tv_view():
    """Exibe a planilha PORTABILIDADE na TV (sem login)"""
    employees = User.query.filter_by(role='user').all()
    dados = []
    totais_diarios = {"seg": 0.0, "ter": 0.0, "qua": 0.0, "qui": 0.0, "sex": 0.0}

    for emp in employees:
        sales = Sale.query.filter_by(
            employee_name=emp.username,
            sheet_type='portabilidade'
        ).all()
        day_values = {sale.day: sale.value for sale in sales}

        seg = day_values.get('monday', 0)
        ter = day_values.get('tuesday', 0)
        qua = day_values.get('wednesday', 0)
        qui = day_values.get('thursday', 0)
        sex = day_values.get('friday', 0)
        total = seg + ter + qua + qui + sex

        dados.append({
            "nome": emp.username,
            "seg": seg,
            "ter": ter,
            "qua": qua,
            "qui": qui,
            "sex": sex,
            "total": total
        })

        totais_diarios["seg"] += seg
        totais_diarios["ter"] += ter
        totais_diarios["qua"] += qua
        totais_diarios["qui"] += qui
        totais_diarios["sex"] += sex

    return render_template('tv.html', dados=dados, totais_diarios=totais_diarios)


@tv_bp.route('/tv/novo')
def tv_novo_view():
    """Exibe a planilha NOVO na TV (sem login)"""
    employees = User.query.filter_by(role='user').all()
    dados = []
    totais_diarios = {"seg": 0.0, "ter": 0.0, "qua": 0.0, "qui": 0.0, "sex": 0.0}

    for emp in employees:
        sales = Sale.query.filter_by(
            employee_name=emp.username,
            sheet_type='novo'  # ← Apenas muda aqui!
        ).all()
        day_values = {sale.day: sale.value for sale in sales}

        seg = day_values.get('monday', 0)
        ter = day_values.get('tuesday', 0)
        qua = day_values.get('wednesday', 0)
        qui = day_values.get('thursday', 0)
        sex = day_values.get('friday', 0)
        total = seg + ter + qua + qui + sex

        dados.append({
            "nome": emp.username,
            "seg": seg,
            "ter": ter,
            "qua": qua,
            "qui": qui,
            "sex": sex,
            "total": total
        })

        totais_diarios["seg"] += seg
        totais_diarios["ter"] += ter
        totais_diarios["qua"] += qua
        totais_diarios["qui"] += qui
        totais_diarios["sex"] += sex

    return render_template('tv_novo.html', dados=dados, totais_diarios=totais_diarios)