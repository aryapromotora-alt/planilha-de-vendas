from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import JSON  # ✅ Use PostgreSQL JSON se estiver usando PostgreSQL

from .user import db  # Usa o mesmo db inicializado em app.py

# Histórico semanal consolidado
class ResumoHistory(db.Model):
    __tablename__ = "resumo_history"

    id = db.Column(db.Integer, primary_key=True)
    week_label = db.Column(db.String(50), nullable=False)  # Ex: "2025-09-08 a 2025-09-12"
    started_at = db.Column(db.Date, nullable=False)
    ended_at = db.Column(db.Date, nullable=False)
    total = db.Column(db.Float, nullable=False)
    breakdown = db.Column(JSON, nullable=False)  # Ex: [{"seller": "João", "total": 123.45}]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ResumoHistory {self.week_label} - Total {self.total:.2f}>"

    def to_dict(self):
        return {
            "id": self.id,
            "week_label": self.week_label,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "total": self.total,
            "breakdown": self.breakdown,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

# Vendas diárias por vendedor
class DailySales(db.Model):
    __tablename__ = "daily_sales"

    id = db.Column(db.Integer, primary_key=True)
    vendedor = db.Column(db.String(100), nullable=False)
    dia = db.Column(db.Date, default=date.today, nullable=False)

    segunda = db.Column(db.Float, default=0.0)
    terca = db.Column(db.Float, default=0.0)
    quarta = db.Column(db.Float, default=0.0)
    quinta = db.Column(db.Float, default=0.0)
    sexta = db.Column(db.Float, default=0.0)

    total = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DailySales {self.vendedor} - {self.dia} - Total {self.total:.2f}>"

    def to_dict(self):
        return {
            "id": self.id,
            "vendedor": self.vendedor,
            "dia": self.dia.isoformat(),
            "segunda": self.segunda,
            "terca": self.terca,
            "quarta": self.quarta,
            "quinta": self.quinta,
            "sexta": self.sexta,
            "total": self.total,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }