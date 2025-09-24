from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

# imports diretos sem src/
from routes.data import load_data
from models.user import db

# Scheduler global
scheduler = BackgroundScheduler()

# ---------------------------
# Filtro para moeda brasileira
# ---------------------------
def format_brl(value):
    try:
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"

# ---------------------------
# Função que salva resumo diário
# ---------------------------
def salvar_resumo_diario(app):
    """
    Salva um resumo diário das vendas:
    - Salva apenas o valor do dia atual da semana
    - Não mistura dados de diferentes dias
    - Mantém fallback para ResumoHistory
    """
    with app.app_context():
        try:
            data = load_data()
            spreadsheet = data.get("spreadsheetData", {})
            
            # Mapeamento de dias da semana (0=segunda, 4=sexta)
            dias_semana = ["monday", "tuesday", "wednesday", "thursday", "friday"]
            nomes_dias = ["segunda", "terca", "quarta", "quinta", "sexta"]
            
            # Pega o dia da semana atual (0=segunda, 1=terça, etc.)
            hoje = datetime.now(timezone("America/Sao_Paulo"))
            dia_semana = hoje.weekday()  # 0=segunda, 1=terça, ..., 4=sexta
            
            # Verifica se é fim de semana
            if dia_semana >= 5:  # sábado=5, domingo=6
                print(f"[INFO] Fim de semana ({hoje.date()}) — não salva resumo diário")
                return
            
            # Pega o campo correspondente ao dia atual
            campo_dia = dias_semana[dia_semana]
            nome_dia = nomes_dias[dia_semana]
            
            print(f"[INFO] Salvando resumo diário para {nome_dia} ({hoje.date()})")
            
            today = hoje.date()
            total_dia = 0
            breakdown = {}

            # Processa cada vendedor
            for nome, valores in spreadsheet.items():
                valor_dia = float(valores.get(campo_dia, 0) or 0)
                breakdown[nome] = valor_dia
                total_dia += valor_dia

            try:
                # Tenta usar DailySales
                from models.archive import DailySales
                for nome, valores in spreadsheet.items():
                    valor_dia = float(valores.get(campo_dia, 0) or 0)
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
            except Exception as e:
                # Fallback para ResumoHistory
                print(f"[FALLBACK] Erro ao usar DailySales: {e}")
                from models.archive import ResumoHistory
                registro = ResumoHistory(
                    week_label=f"Auto {today} - {nome_dia}",
                    started_at=hoje,
                    ended_at=hoje,
                    total=total_dia,
                    breakdown=breakdown,
                    created_at=hoje
                )
                db.session.add(registro)

            db.session.commit()
            print(f"[OK] Resumo diário salvo em {hoje} — Total: R$ {format_brl(total_dia)}")

        except Exception as e:
            print(f"[ERRO] salvar_resumo_diario: {e}")

# ---------------------------
# Inicializa o scheduler
# ---------------------------
def start_scheduler(app):
    """
    Agenda diária às 18:20 no horário de Brasília
    """
    # Evita múltiplas instâncias do scheduler
    if not scheduler.get_jobs():
        scheduler.add_job(
            func=lambda: salvar_resumo_diario(app),
            trigger="cron",
            hour=18,
            minute=20,
            timezone=timezone("America/Sao_Paulo")
        )
        scheduler.start()
        print("[INFO] Scheduler iniciado para resumo diário às 18:20 (Horário de Brasília)")