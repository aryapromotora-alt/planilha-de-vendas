from flask import Blueprint, render_template
from models.sales import DailySales  # ajuste o caminho se necessário
from sqlalchemy import func
from datetime import date

tv_bp = Blueprint('tv', __name__)

@tv_bp.route(tv)
def tv_view()
    # Busca todas as vendas do dia atual
    hoje = date.today()
    vendas_hoje = DailySales.query.filter_by(dia=hoje).all()

    dados = []
    totais_diarios = {
        seg 0.0,
        ter 0.0,
        qua 0.0,
        qui 0.0,
        sex 0.0
    }

    for venda in vendas_hoje
        linha = {
            nome venda.vendedor,
            seg venda.segunda,
            ter venda.terca,
            qua venda.quarta,
            qui venda.quinta,
            sex venda.sexta,
            total venda.total
        }
        dados.append(linha)

        totais_diarios[seg] += venda.segunda
        totais_diarios[ter] += venda.terca
        totais_diarios[qua] += venda.quarta
        totais_diarios[qui] += venda.quinta
        totais_diarios[sex] += venda.sexta

    return render_template(tv.html, dados=dados, totais_diarios=totais_diarios)