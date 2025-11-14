from extensions import db
from datetime import datetime, timezone

class CRBReport(db.Model):
    __tablename__ = 'crb_report'
    
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key should point to the `loans` table (plural) to match `Loan.__tablename__`
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'))
    national_id = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    
    # CRB Data Fields
    credit_score = db.Column(db.Integer)
    active_loans = db.Column(db.Integer, default=0)
    default_history = db.Column(db.Integer, default=0)
    credit_utilization = db.Column(db.Float, default=0.0)
    payment_pattern = db.Column(db.String(50))
    blacklist_status = db.Column(db.Boolean, default=False)
    days_arrears = db.Column(db.Integer, default=0)
    credit_rating = db.Column(db.String(20))
    crb_bureau = db.Column(db.String(50), default='Simulated')
    
    # Timestamps
    report_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'credit_score': self.credit_score,
            'active_loans': self.active_loans,
            'default_history': self.default_history,
            'credit_utilization': self.credit_utilization,
            'payment_pattern': self.payment_pattern,
            'blacklist_status': self.blacklist_status,
            'days_arrears': self.days_arrears,
            'credit_rating': self.credit_rating,
            'crb_bureau': self.crb_bureau,
            'report_date': self.report_date.isoformat()
        }