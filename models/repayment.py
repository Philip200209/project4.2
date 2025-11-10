from extensions import db
from datetime import datetime, timezone

class Repayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer)  # REMOVE foreign key
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # REMOVE this relationship
    # loan = db.relationship('Loan', backref=db.backref('repayment_schedule', lazy=True))
    
    def __repr__(self):
        return f'<Repayment {self.id} for Loan {self.loan_id}>'