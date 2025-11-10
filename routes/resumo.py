from flask import Blueprint, render_template, jsonify
from datetime import datetime, timedelta, date
from models.archive import DailySales
from sqlalchemy.sql import extract
from calendar import monthrange
from collections import defaultdict

resumo_bp = Blueprint("resumo", __name__)

def get_daily_totals_for_month(ano, mes):
    """Calcula os totais diários (soma de todas as segundas, terças, etc.) para um determinado mês e ano."""
    
    # 1. Obter todos os registros do mês
    registros_mes = DailySales.query.filter(
        extract("month", DailySales.dia) == mes,
        extract("year", DailySales.dia) == ano
    ).all()

    # 2. Mapear os totais por dia da semana (0=Segunda, 4=Sexta)
    daily_totals = {i: 0.0 for i in range(5)} # 0: Segunda, 1: Terça, ..., 4: Sexta
    
    for r in registros_mes:
        dia_semana = r.dia.weekday()
        
        # Considerar apenas dias úteis (Segunda a Sexta)
        if 0 <= dia_semana <= 4:
            # Assumindo que r.total é o total de vendas daquele dia
            daily_totals[dia_semana] += r.total
            
    # 3. Retornar os totais na ordem correta (Segunda a Sexta)
    return [daily_totals[i] for i in range(5)]

def get_weekly_totals_for_month(ano, mes):
    """Calcula os totais semanais para um determinado mês e ano."""
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, monthrange(ano, mes)[1])
    
    # 1. Obter todos os registros do mês
    registros_mes = DailySales.query.filter(
        DailySales.dia >= primeiro_dia,
        DailySales.dia <= ultimo_dia
    ).all()
    
    dias_no_mes = (ultimo_dia - primeiro_dia).days + 1
    primeiro_dia_weekday = primeiro_dia.weekday()
    
    # Calcula o número de semanas (lógica compatível com o frontend)
    num_semanas = ((dias_no_mes + primeiro_dia_weekday) // 7)
    if (dias_no_mes + primeiro_dia_weekday) % 7 != 0:
         num_semanas += 1
    
    # Inicializa os totais semanais
    totais_mes = [0.0 for _ in range(num_semanas)]
    
    # Preenche os totais semanais
    for r in registros_mes:
        # Calcula o índice da semana: (dia do mês + dia da semana do dia 1 - 1) // 7
        semana_index = ((r.dia.day + primeiro_dia_weekday - 1) // 7)
        
        if 0 <= semana_index < num_semanas:
            totais_mes[semana_index] += r.total
            
    return totais_mes

@resumo_bp.route("/api/dias/<int:ano>/<int:mes>")
def api_dias(ano, mes):
    """Endpoint para retornar os totais diários (segunda a sexta) para um mês/ano específico."""
    try:
        totais_diarios = get_daily_totals_for_month(ano, mes)
        return jsonify(totais_diarios), 200
    except Exception as e:
        print(f"Erro na API de dias: {e}")
        return jsonify({"error": "Erro ao carregar dados diários"}), 500

@resumo_bp.route("/api/semanas/<int:ano>/<int:mes>")
def api_semanas(ano, mes):
    """Endpoint para retornar os totais semanais para um mês/ano específico."""
    try:
        totais_semanais = get_weekly_totals_for_month(ano, mes)
        return jsonify(totais_semanais), 200
    except Exception as e:
        print(f"Erro na API de semanas: {e}")
        return jsonify({"error": "Erro ao carregar dados semanais"}), 500

@resumo_bp.route("/resumo")
def resumo_page():
    hoje = datetime.utcnow().date()
    ano = hoje.year
    mes = hoje.month

    # --- Carga inicial para a semana atual (resumo diário) ---
    # O resumo diário na carga inicial deve mostrar os valores da semana atual.
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    
    historico_diario_semana_atual = {}
    dias_labels = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
    
    for i, label in enumerate(dias_labels):
        dia_atual = inicio_semana + timedelta(days=i)
        registros_dia = DailySales.query.filter_by(dia=dia_atual).all()
        # Assumindo que r.total é o total de vendas do dia
        valor_dia = sum(r.total for r in registros_dia)
        historico_diario_semana_atual[label] = valor_dia

    # --- Carga inicial para o mês atual (resumo semanal) ---
    totais_mes = get_weekly_totals_for_month(ano, mes)
    num_semanas = len(totais_mes)
    
    mes_nome = hoje.strftime("%B").capitalize()
    mes_atual = f"{ano}-{mes:02d}"

    # --- Histórico mensal completo para o <select> ---
    historico_mensal = defaultdict(float)
    for r in DailySales.query.all():
        chave = f"{r.dia.year}-{r.dia.month:02d}"
        historico_mensal[chave] += r.total
    historico_mensal = dict(sorted(historico_mensal.items()))

    # --- Lista de anos e meses ---
    anos_disponiveis = list(range(2025, 2031))
    meses_nomes = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    return render_template(
        "resumo.html",
        hoje=hoje,
        total_seg=historico_diario_semana_atual.get("Segunda", 0),
        total_ter=historico_diario_semana_atual.get("Terça", 0),
        total_qua=historico_diario_semana_atual.get("Quarta", 0),
        total_qui=historico_diario_semana_atual.get("Quinta", 0),
        total_sex=historico_diario_semana_atual.get("Sexta", 0),
        totais_mes=totais_mes,
        num_semanas=num_semanas,
        mes_nome=mes_nome,
        mes_atual=mes_atual,
        historico_mensal=historico_mensal,
        anos_disponiveis=anos_disponiveis,
        meses_nomes=meses_nomes
    )
