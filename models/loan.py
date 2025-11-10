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

    # REMOVE these foreign keys - they're causing the error
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # client_id = db.Column(db.Integer, db.ForeignKey('client.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'amount': self.amount,
            'term': self.term,
            'status': self.status,
            'risk_score': self.risk_score,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'purpose': self.purpose,
            'behavior_score': self.behavior_score,
            'payments_missed': self.payments_missed,
            'is_flagged': self.is_flagged
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
            return True
        
        return False

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

    def __repr__(self):
        return f'<Loan {self.id} - {self.client_name} - {self.status}>'