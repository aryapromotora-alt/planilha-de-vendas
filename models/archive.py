from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON

from .user import db  # usa o mesmo db inicializado

class WeeklyHistory(db.Model):
    __tablename__ = "weekly_history"

    id = db.Column(db.Integer, primary_key=True)
    week_label = db.Column(db.String(50), nullable=False)  # ex: "2025-09-08 a 2025-09-12"
    started_at = db.Column(db.Date, nullable=False)
    ended_at = db.Column(db.Date, nullable=False)
    total = db.Column(db.Float, nullable=False)
    breakdown = db.Column(JSON, nullable=False)  # [{seller: "João", total: 123}, ...]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WeeklyHistory {self.week_label} - Total {self.total}>"

    def to_dict(self):
        return {
            "id": self.id,
            "week_label": self.week_label,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "total": self.total,
            "breakdown": self.breakdown,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
