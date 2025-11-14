from extensions import db
from datetime import datetime, timezone

class Intervention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer)
    type = db.Column(db.String(50))
    message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='sent')
    
    @property
    def loan(self):
        """Get the loan object without a formal relationship"""
        from .loan import Loan
        return Loan.query.get(self.loan_id)
    
    def __repr__(self):
        return f'<Intervention {self.type} for Loan {self.loan_id}>'