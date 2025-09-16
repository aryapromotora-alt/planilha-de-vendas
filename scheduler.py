# scheduler.py
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# imports sem src/
from routes.data import load_data
from models.user import db

scheduler = BackgroundScheduler()

def salvar_resumo_diario(app):
    with app.app_context():
        try:
            data = load_data()
            spreadsheet = data.get("spreadsheetData", {})

            # Total do dia e breakdown por vendedor
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

            # tenta usar DailySales se existir, senão salva um registro único em WeeklyHistory como fallback
            try:
                from models.archive import DailySales
                today = datetime.utcnow().date()
                for nome, valores in spreadsheet.items():
                    vendedor_total = sum([
                        valores.get("monday", 0) or 0,
                        valores.get("tuesday", 0) or 0,
                        valores.get("wednesday", 0) or 0,
                        valores.get("thursday", 0) or 0,
                        valores.get("friday", 0) or 0,
                    ])
                    record = DailySales(
                        vendedor=nome,
                        dia=today,
                        segunda=valores.get("monday", 0) or 0,
                        terca=valores.get("tuesday", 0) or 0,
                        quarta=valores.get("wednesday", 0) or 0,
                        quinta=valores.get("thursday", 0) or 0,
                        sexta=valores.get("friday", 0) or 0,
                        total=vendedor_total
                    )
                    db.session.add(record)
            except Exception:
                # fallback: salva um registro único em WeeklyHistory (usado apenas para garantir persistência)
                from models.archive import WeeklyHistory
                registro = WeeklyHistory(
                    week_label=f"Auto {datetime.utcnow().date()}",
                    started_at=datetime.utcnow(),
                    ended_at=datetime.utcnow(),
                    total=total_dia,
                    breakdown=breakdown,
                    created_at=datetime.utcnow()
                )
                db.session.add(registro)

            db.session.commit()
            print(f"[OK] Resumo diário salvo em {datetime.utcnow()}")

        except Exception as e:
            print("[ERRO] salvar_resumo_diario:", e)


def start_scheduler(app):
    # agenda diária às 23:59 UTC (ajuste conforme sua necessidade)
    scheduler.add_job(lambda: salvar_resumo_diario(app), "cron", hour=23, minute=59)
    scheduler.start()
