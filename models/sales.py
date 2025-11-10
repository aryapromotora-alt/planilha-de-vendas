from .user import db

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(100), nullable=False)
    day = db.Column(db.String(10), nullable=False)
    value = db.Column(db.Float, default=0.0)
    sheet_type = db.Column(db.String(20), default='portabilidade')  # Nova linha!

    # Atualize a UniqueConstraint para incluir sheet_type
    __table_args__ = (
        db.UniqueConstraint('employee_name', 'day', 'sheet_type', name='uq_employee_day_sheet'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'employee_name': self.employee_name,
            'day': self.day,
            'value': self.value,
            'sheet_type': self.sheet_type  # Nova linha!
        }