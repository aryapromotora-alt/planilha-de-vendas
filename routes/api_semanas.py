from flask import Blueprint, jsonify
from models.archive import DailySales
from datetime import date
from calendar import monthrange
from sqlalchemy import extract

api_semanas_bp = Blueprint("api_semanas", __name__)

@api_semanas_bp.route("/api/semanas/<int:ano>/<int:mes>")
def semanas_por_mes(ano, mes):
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, monthrange(ano, mes)[1])
    dias_no_mes = (ultimo_dia - primeiro_dia).days + 1
    num_semanas = ((dias_no_mes + primeiro_dia.weekday()) // 7) + 1

    totais = [0 for _ in range(num_semanas)]

    registros = DailySales.query.filter(
        extract("year", DailySales.dia) == ano,
        extract("month", DailySales.dia) == mes
    ).all()

    for r in registros:
        semana_index = ((r.dia.day + primeiro_dia.weekday() - 1) // 7)
        if 0 <= semana_index < num_semanas:
            totais[semana_index] += r.total

    return jsonify(totais)