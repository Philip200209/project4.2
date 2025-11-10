from extensions import db
from datetime import datetime, timezone

class Intervention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer)  # Just store the ID, no foreign key
    type = db.Column(db.String(50))
    message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='sent')
    
    # NO relationships - keep it simple
    
    def __repr__(self):
        return f'<Intervention {self.type} for Loan {self.loan_id}>'