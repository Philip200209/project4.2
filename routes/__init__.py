from extensions import db
from datetime import datetime

# Use canonical models from the models package to avoid duplicate SQLAlchemy metadata
from models import User, CRBReport

# LoanApplication remains here (application-specific); it references the canonical User and CRBReport models
class LoanApplication(db.Model):
    __tablename__ = 'loan_applications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    amount = db.Column(db.Float, nullable=True)
    purpose = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # === NEW FIELDS FOR CRB INTEGRATION ===
    national_id = db.Column(db.String(20))
    crb_checked = db.Column(db.Boolean, default=False)
    crb_report_id = db.Column(db.Integer, db.ForeignKey('crb_report.id'))
    risk_score = db.Column(db.Float)

    # Relationships (use string names to avoid import cycles)
    user = db.relationship('User', backref=db.backref('loan_applications', lazy=True))
    crb_report = db.relationship('CRBReport', backref='loan_application', foreign_keys=[crb_report_id])

    def __repr__(self):
        return f'<LoanApplication {self.id} - {self.status}>'

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), default='medium')
    resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # === NEW FIELD FOR CRB ALERTS ===
    alert_type = db.Column(db.String(50), default='general')  # 'crb_blacklist', 'credit_score', etc.

    # Relationship
    user = db.relationship('User', backref=db.backref('alerts', lazy=True))

    def __repr__(self):
        return f'<Alert {self.id} - {self.severity}>'

# NOTE: CRBReport is imported from models above to keep a single canonical definition