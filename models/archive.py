from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
from src.models.user import db  # aproveita a mesma instância do db

class WeeklyHistory(db.Model):
    __tablename__ = "weekly_history"

    id = db.Column(db.Integer, primary_key=True)
    week_label = db.Column(db.String(50), nullable=False)  # Ex: "2025-09-08 a 2025-09-12"
    started_at = db.Column(db.Date, nullable=False)
    ended_at = db.Column(db.Date, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    breakdown = db.Column(JSON, nullable=False)  # lista de vendedores e totais
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "week_label": self.week_label,
            "started_at": str(self.started_at),
            "ended_at": str(self.ended_at),
            "total": self.total,
            "breakdown": self.breakdown,
            "created_at": self.created_at.isoformat()
        }
