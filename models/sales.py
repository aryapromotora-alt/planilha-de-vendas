from .user import db
from datetime import datetime, date

class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(100), nullable=False)
    day = db.Column(db.String(10), nullable=False)  # Ex: "monday"
    value = db.Column(db.Float, default=0.0)
    reference_date = db.Column(db.Date, nullable=False)  # Ex: data da semana
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('employee_name', 'day', 'reference_date', name='uq_employee_day_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'employee_name': self.employee_name,
            'day': self.day,
            'value': self.value,
            'reference_date': self.reference_date.isoformat(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }