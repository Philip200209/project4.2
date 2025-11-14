from extensions import db
from datetime import datetime, timedelta
import json

class Loan(db.Model):
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(120))
    client_phone = db.Column(db.String(20))
    amount = db.Column(db.Float, nullable=False)
    term = db.Column(db.Integer, nullable=False)
    interest_rate = db.Column(db.Float, default=12.0)
    purpose = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    risk_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Client financial information
    monthly_income = db.Column(db.Float)
    employment_status = db.Column(db.String(50))
    credit_history = db.Column(db.String(20))
    
    # === NEW BEHAVIOR MONITORING FIELDS ===
    payments_missed = db.Column(db.Integer, default=0)
    total_paid = db.Column(db.Float, default=0.0)
    next_payment_date = db.Column(db.Date)
    last_payment_date = db.Column(db.Date)
    behavior_score = db.Column(db.Float, default=100.0)
    risk_flags = db.Column(db.Text)  # Store as JSON string for MySQL compatibility
    is_flagged = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.String(200))

    # === NEW CRB INTEGRATION FIELDS ===
    national_id = db.Column(db.String(20))
    crb_checked = db.Column(db.Boolean, default=False)
    crb_report_id = db.Column(db.Integer, db.ForeignKey('crb_report.id'))
    
    # Risk level based on comprehensive scoring
    risk_level = db.Column(db.String(20), default='Medium')  # Low, Medium, High, Critical

    # REMOVE these foreign keys - they're causing the error
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # client_id = db.Column(db.Integer, db.ForeignKey('client.id'))

    # Relationship to CRBReport
    crb_report = db.relationship('CRBReport', backref='loan', foreign_keys=[crb_report_id])

    def to_dict(self):
        return {
            'id': self.id,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'amount': self.amount,
            'term': self.term,
            'status': self.status,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'purpose': self.purpose,
            'behavior_score': self.behavior_score,
            'payments_missed': self.payments_missed,
            'is_flagged': self.is_flagged,
            'national_id': self.national_id,
            'crb_checked': self.crb_checked,
            'crb_report_id': self.crb_report_id
        }

    def get_risk_flags(self):
        """Get risk flags as Python list"""
        if self.risk_flags:
            return json.loads(self.risk_flags)
        return []

    def set_risk_flags(self, flags_list):
        """Set risk flags from Python list"""
        self.risk_flags = json.dumps(flags_list)

    def add_risk_flag(self, flag_type, severity='medium', message=''):
        """Add a risk flag to the loan"""
        flags = self.get_risk_flags()
        
        new_flag = {
            'type': flag_type,
            'date': datetime.utcnow().isoformat(),
            'severity': severity,
            'message': message
        }
        
        flags.append(new_flag)
        self.set_risk_flags(flags)
        self.is_flagged = True
        self.flag_reason = message

    def calculate_next_payment_date(self):
        """Calculate next payment date when loan is approved"""
        if self.status == 'approved' and not self.next_payment_date:
            self.next_payment_date = datetime.utcnow().date() + timedelta(days=30)

    def record_payment(self, amount, payment_date=None):
        """Record a payment and update behavior metrics"""
        if not payment_date:
            payment_date = datetime.utcnow().date()
        
        # Update payment totals
        self.total_paid += amount
        self.last_payment_date = payment_date
        
        # Reset missed payments counter if payment is made
        if self.payments_missed > 0:
            self.payments_missed = max(0, self.payments_missed - 1)
        
        # Calculate next payment date
        self.next_payment_date = payment_date + timedelta(days=30)
        
        # Update behavior score positively
        self.behavior_score = min(100, self.behavior_score + 5)
        
        # Update risk level based on improved behavior
        self.update_risk_level()
        
        return True

    def check_missed_payment(self):
        """Check if payment is missed and update flags"""
        if not self.next_payment_date or self.status != 'approved':
            return False
            
        today = datetime.utcnow().date()
        if today > self.next_payment_date:
            self.payments_missed += 1
            self.behavior_score = max(0, self.behavior_score - 10)
            
            # Add risk flag for missed payment
            days_overdue = (today - self.next_payment_date).days
            self.add_risk_flag(
                flag_type='missed_payment',
                severity='high' if self.payments_missed > 2 else 'medium',
                message=f'Payment missed - {days_overdue} days overdue'
            )
            
            # Move next payment date to avoid repeated alerts
            self.next_payment_date = today + timedelta(days=30)
            
            # Update risk level based on worsened behavior
            self.update_risk_level()
            
            return True
        
        return False

    def update_risk_level(self):
        """Update risk level based on comprehensive scoring"""
        if self.risk_score is None:
            return
            
        if self.risk_score >= 70:
            self.risk_level = 'Low'
        elif self.risk_score >= 50:
            self.risk_level = 'Medium'
        elif self.risk_score >= 30:
            self.risk_level = 'High'
        else:
            self.risk_level = 'Critical'

    def get_crb_insights(self):
        """Get insights based on CRB data if available"""
        if not self.crb_report:
            return "No CRB data available", "CRB check not performed", "secondary"
            
        crb_data = self.crb_report.to_dict() if hasattr(self.crb_report, 'to_dict') else {}
        
        if crb_data.get('blacklist_status'):
            return "Blacklisted", "Applicant is on CRB blacklist", "danger"
        elif crb_data.get('credit_score', 0) >= 700:
            return "Good Credit", "Favorable credit history", "success"
        elif crb_data.get('credit_score', 0) >= 550:
            return "Fair Credit", "Moderate credit history", "warning"
        else:
            return "Poor Credit", "Unfavorable credit history", "danger"

    def get_behavior_insights(self):
        """Get behavior insights and recommendations"""
        if self.behavior_score >= 80:
            return "Excellent", "Consistent payment behavior", "success"
        elif self.behavior_score >= 60:
            return "Good", "Generally reliable payments", "info"
        elif self.behavior_score >= 40:
            return "Needs Attention", "Some payment issues detected", "warning"
        else:
            return "High Risk", "Frequent payment problems", "danger"

    def get_comprehensive_risk_assessment(self):
        """Get comprehensive risk assessment combining all factors"""
        behavior_level, behavior_msg, behavior_color = self.get_behavior_insights()
        crb_level, crb_msg, crb_color = self.get_crb_insights()
        
        # Combine assessments
        if behavior_color == 'danger' or crb_color == 'danger':
            return "Critical Risk", "Multiple high-risk factors detected", "danger"
        elif behavior_color == 'warning' or crb_color == 'warning':
            return "Elevated Risk", "Several risk factors require monitoring", "warning"
        elif behavior_color == 'success' and crb_color == 'success':
            return "Low Risk", "Favorable risk profile", "success"
        else:
            return "Moderate Risk", "Standard risk monitoring required", "info"

    def can_approve_loan(self):
        """Check if loan can be approved based on comprehensive risk assessment"""
        if self.crb_report and hasattr(self.crb_report, 'blacklist_status'):
            if self.crb_report.blacklist_status:
                return False, "Applicant is blacklisted in CRB"
        
        if self.risk_score is not None and self.risk_score < 30:
            return False, "Risk score too low for approval"
            
        if self.behavior_score < 40 and self.status == 'approved':
            return False, "Poor behavior score for existing loan"
            
        return True, "Eligible for approval"

    def __repr__(self):
        return f'<Loan {self.id} - {self.client_name} - {self.status} - CRB: {self.crb_checked}>'