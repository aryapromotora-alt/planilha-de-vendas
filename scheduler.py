from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

# imports sem src/
from routes.data import load_data
from models.user import db

scheduler = BackgroundScheduler()

# ✅ Filtro para formato brasileiro
def format_brl(value):
    try:
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"

def salvar_resumo_diario(app):
    """
    Salva um resumo diário das vendas:
      - Tenta salvar no modelo DailySales (se existir)
      - Se não existir, salva no ResumoHistory como fallback
    """
    with app.app_context():
        try:
            data = load_data()
            spreadsheet = data.get("spreadsheetData", {})

            total_dia = 0
            breakdown = {}

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

def start_scheduler(app):
    # agenda diária às 23:59 no horário de Brasília
    scheduler.add_job(
        lambda: salvar_resumo_diario(app),
        "cron",
        hour=23,
        minute=59,
        timezone=timezone("America/Sao_Paulo")
    )
    scheduler.start()