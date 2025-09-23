from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
import requests

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
    - Prioriza DailySales
    - Se não existir, usa ResumoHistory como fallback
    """
    with app.app_context():
        try:
            data = load_data()
            spreadsheet = data.get("spreadsheetData", {})

            total_dia = 0
            breakdown = {}

            # Soma por vendedor
            for nome, valores in spreadsheet.items():
                vendedor_total = sum([
                    valores.get("monday", 0) or 0,
                    valores.get("tuesday", 0) or 0,
                    valores.get("wednesday", 0) or 0,
                    valores.get("thursday", 0) or 0,
                    valores.get("friday", 0) or 0,
                ])
                breakdown[nome] = vendedor_total
                total_dia += vendedor_total

            today = datetime.utcnow().date()

            try:
                # Tenta usar DailySales
                from models.archive import DailySales
                for nome, valores in spreadsheet.items():
                    record = DailySales(
                        vendedor=nome,
                        dia=today,
                        segunda=valores.get("monday", 0) or 0,
                        terca=valores.get("tuesday", 0) or 0,
                        quarta=valores.get("wednesday", 0) or 0,
                        quinta=valores.get("thursday", 0) or 0,
                        sexta=valores.get("friday", 0) or 0,
                        total=breakdown[nome]
                    )
                    db.session.add(record)
            except Exception as e:
                # Fallback para ResumoHistory
                print(f"[FALLBACK] Erro ao usar DailySales: {e}")
                from models.archive import ResumoHistory
                registro = ResumoHistory(
                    week_label=f"Auto {today}",
                    started_at=datetime.utcnow(),
                    ended_at=datetime.utcnow(),
                    total=total_dia,
                    breakdown=breakdown,
                    created_at=datetime.utcnow()
                )
                db.session.add(registro)

            db.session.commit()
            print(f"[OK] Resumo diário salvo em {datetime.utcnow()} — Total: R$ {format_brl(total_dia)}")

        except Exception as e:
            print(f"[ERRO] salvar_resumo_diario: {e}")

# ---------------------------
# Função que fecha a semana
# ---------------------------
def fechar_semana(app):
    """
    Chama a rota /api/resumo-archive para fechar a semana
    """
    with app.app_context():
        try:
            url = "http://localhost:5000/api/resumo-archive"
            secret = app.config.get("RESUMO_ARCHIVE_SECRET")
            headers = {"X-SECRET-KEY": secret}

            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                print(f"[OK] Fechamento semanal executado em {datetime.utcnow()}")
            else:
                print(f"[ERRO] Fechamento semanal falhou: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"[ERRO] fechar_semana: {e}")

# ---------------------------
# Inicializa o scheduler
# ---------------------------
def start_scheduler(app):
    """
    Agenda:
    - Diário às 18:00 (save)
    - Semanal às 18:00 de sexta-feira (fechamento + zera planilha)
    """
    # Evita múltiplas instâncias do scheduler
    if not scheduler.get_jobs():
        # 🔥 Save diário às 18:00
        scheduler.add_job(
            func=lambda: salvar_resumo_diario(app),
            trigger="cron",
            hour=18,
            minute=0,
            timezone=timezone("America/Sao_Paulo"),
            id="daily_save"
        )

        # 🔥 Fechamento semanal (sexta-feira às 18:00)
        scheduler.add_job(
            func=lambda: fechar_semana(app),
            trigger="cron",
            day_of_week="fri",
            hour=18,
            minute=0,
            timezone=timezone("America/Sao_Paulo"),
            id="weekly_close"
        )

        scheduler.start()
        print("[INFO] Scheduler iniciado:")
        print(" - Save diário: 18:00 todos os dias")
        print(" - Fechamento semanal: 18:00 toda sexta-feira (Horário de Brasília)")