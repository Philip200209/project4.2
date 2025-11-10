from extensions import db
from datetime import datetime, timezone

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    employment_status = db.Column(db.String(50))
    monthly_income = db.Column(db.Float, default=0.0)
    credit_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # REMOVE this relationship - it's causing the error
    # loans = db.relationship('Loan', backref='client', lazy=True)
    
    def __repr__(self):
        return f'<Client {self.name}>'