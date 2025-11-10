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
    
    # 2. Agrupar e somar os totais de todos os vendedores por dia
    daily_totals_map = defaultdict(float)
    for r in registros_mes:
        daily_totals_map[r.dia] += r.total
        
    # 3. Mapear os totais por dia da semana (0=Segunda, 4=Sexta)
    # Usamos 5 posições para Segunda a Sexta
    daily_totals = [0.0] * 5 
    
    for dia, total_dia in daily_totals_map.items():
        dia_semana = dia.weekday() # 0=Segunda, 4=Sexta
        
        # Considerar apenas dias úteis (Segunda a Sexta)
        if 0 <= dia_semana <= 4:
            daily_totals[dia_semana] += total_dia
            
    # 4. Retornar os totais na ordem correta (Segunda a Sexta)
    return daily_totals

def get_weekly_totals_for_month(ano, mes):
    """Calcula os totais semanais para um determinado mês e ano."""
    try:
        primeiro_dia = date(ano, mes, 1)
        ultimo_dia = date(ano, mes, monthrange(ano, mes)[1])
    except ValueError:
        # Lida com meses/anos inválidos
        return []
    
    # 1. Obter todos os registros do mês
    registros_mes = DailySales.query.filter(
        DailySales.dia >= primeiro_dia,
        DailySales.dia <= ultimo_dia
    ).all()
    
    # Mapeia os totais diários para fácil acesso, somando os totais de todos os vendedores para o mesmo dia
    daily_totals_map = defaultdict(float)
    for r in registros_mes:
        daily_totals_map[r.dia] += r.total
    
    dias_no_mes = (ultimo_dia - primeiro_dia).days + 1
    primeiro_dia_weekday = primeiro_dia.weekday() # 0=Segunda, 6=Domingo
    
    # Calcula o número de semanas (lógica compatível com o frontend)
    # A semana começa na segunda-feira (weekday 0)
    num_semanas = ((dias_no_mes + primeiro_dia_weekday) // 7)
    if (dias_no_mes + primeiro_dia_weekday) % 7 != 0:
         num_semanas += 1
    
    # Inicializa os totais semanais
    totais_mes = [0.0] * num_semanas
    
    # Preenche os totais semanais
    for dia_do_mes in range(1, dias_no_mes + 1):
        current_date = date(ano, mes, dia_do_mes)
        
        # Calcula o índice da semana: (dia do mês + dia da semana do dia 1 - 1) // 7
        semana_index = ((current_date.day + primeiro_dia_weekday - 1) // 7)
        
        if 0 <= semana_index < num_semanas:
            # Adiciona o total do dia ao total da semana
            total_do_dia = daily_totals_map.get(current_date, 0.0)
            totais_mes[semana_index] += total_do_dia
            
    return totais_mes

@resumo_bp.route("/api/dias/<int:ano>/<int:mes>")
def api_dias(ano, mes):
    """Endpoint para retornar os totais diários (segunda a sexta) para um mês/ano específico."""
    try:
        totais_diarios = get_daily_totals_for_month(ano, mes)
        return jsonify(totais_diarios), 200
    except Exception as e:
        # Adicionando um log mais detalhado para depuração
        print(f"ERRO FATAL na API de dias ({ano}/{mes}): {e}")
        return jsonify({"error": "Erro ao carregar dados diários"}), 500

@resumo_bp.route("/api/semanas/<int:ano>/<int:mes>")
def api_semanas(ano, mes):
    """Endpoint para retornar os totais semanais para um mês/ano específico."""
    try:
        totais_semanais = get_weekly_totals_for_month(ano, mes)
        return jsonify(totais_semanais), 200
    except Exception as e:
        # Adicionando um log mais detalhado para depuração
        print(f"ERRO FATAL na API de semanas ({ano}/{mes}): {e}")
        return jsonify({"error": "Erro ao carregar dados semanais"}), 500

@resumo_bp.route("/resumo")
def resumo_page():
    hoje = datetime.utcnow().date()
    ano = hoje.year
    mes = hoje.month

    # --- Carga inicial para a semana atual (resumo diário) ---
    # Para garantir que a carga inicial reflita o mês/ano atual, usamos as novas funções.
    historico_diario_semana_atual = get_daily_totals_for_month(ano, mes)
    
    # Mapeia os totais para as variáveis do template
    totais_diarios_map = {
        "Segunda": historico_diario_semana_atual[0] if len(historico_diario_semana_atual) > 0 else 0,
        "Terça": historico_diario_semana_atual[1] if len(historico_diario_semana_atual) > 1 else 0,
        "Quarta": historico_diario_semana_atual[2] if len(historico_diario_semana_atual) > 2 else 0,
        "Quinta": historico_diario_semana_atual[3] if len(historico_diario_semana_atual) > 3 else 0,
        "Sexta": historico_diario_semana_atual[4] if len(historico_diario_semana_atual) > 4 else 0,
    }

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
        total_seg=totais_diarios_map.get("Segunda", 0),
        total_ter=totais_diarios_map.get("Terça", 0),
        total_qua=totais_diarios_map.get("Quarta", 0),
        total_qui=totais_diarios_map.get("Quinta", 0),
        total_sex=totais_diarios_map.get("Sexta", 0),
        totais_mes=totais_mes,
        num_semanas=num_semanas,
        mes_nome=mes_nome,
        mes_atual=mes_atual,
        historico_mensal=historico_mensal,
        anos_disponiveis=anos_disponiveis,
        meses_nomes=meses_nomes
    )
