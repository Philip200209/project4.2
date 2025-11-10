from datetime import datetime, timedelta
from flask import current_app

class InterventionService:
    def __init__(self, email_service):
        self.email_service = email_service
    
    def check_due_reminders(self):
        """Check and send due date reminders"""
        if not current_app.config.get('INTERVENTION_EMAILS_ENABLED', True):
            print("📧 Email interventions are disabled")
            return
        
        try:
            # Try to import models
            from models import LoanApplication, Client
            
            # Check if models have the required attributes
            if not hasattr(LoanApplication, 'status') or not hasattr(LoanApplication, 'next_due_date'):
                print("⚠️ LoanApplication model doesn't have required attributes")
                return
                
            due_soon_loans = LoanApplication.query.filter(
                LoanApplication.status == 'active',
                LoanApplication.next_due_date <= datetime.now() + timedelta(days=7),
                LoanApplication.next_due_date >= datetime.now()
            ).all()
            
            print(f"🔍 Found {len(due_soon_loans)} loans due soon")
            
            for loan in due_soon_loans:
                days_until_due = (loan.next_due_date - datetime.now()).days
                if days_until_due in current_app.config.get('REMINDER_DAYS_BEFORE_DUE', [7, 3, 1]):
                    client = Client.query.get(loan.client_id)
                    if client and hasattr(client, 'email') and client.email:
                        self.email_service.send_payment_reminder(
                            client.email,
                            client.name,
                            {
                                'loan_amount': getattr(loan, 'amount', 0),
                                'due_date': loan.next_due_date,
                                'outstanding_balance': getattr(loan, 'outstanding_balance', getattr(loan, 'amount', 0))
                            },
                            days_until_due
                        )
                        print(f"✅ Sent reminder for {client.name}, due in {days_until_due} days")
                    else:
                        print(f"⚠️ No email for client {getattr(client, 'name', 'Unknown')}")
        except Exception as e:
            print(f"❌ Error in due reminders: {e}")
    
    def monitor_high_risk(self):
        """Monitor and alert on high-risk loans"""
        if not current_app.config.get('INTERVENTION_EMAILS_ENABLED', True):
            return
        
        try:
            from models import LoanApplication, Client
            
            # Check if risk_score attribute exists
            if not hasattr(LoanApplication, 'risk_score'):
                print("⚠️ LoanApplication model doesn't have risk_score attribute")
                return
                
            high_risk_loans = LoanApplication.query.filter(
                LoanApplication.risk_score >= current_app.config.get('HIGH_RISK_ALERT_THRESHOLD', 0.7),
                LoanApplication.status.in_(['active', 'pending'])
            ).all()
            
            print(f"🔍 Found {len(high_risk_loans)} high-risk loans")
            
            for loan in high_risk_loans:
                client = Client.query.get(loan.client_id)
                if client:
                    # Alert loan officer
                    self.email_service.send_risk_alert(
                        'admin@crimap.com',  # Replace with actual officer email
                        client.name,
                        loan.risk_score,
                        getattr(loan, 'amount', 0)
                    )
                    print(f"✅ Sent risk alert for {client.name}, score: {loan.risk_score}")
        except Exception as e:
            print(f"❌ Error in high risk monitoring: {e}")
    
    def run_daily_interventions(self):
        """Run all daily intervention checks"""
        print("🔄 Running daily interventions...")
        self.check_due_reminders()
        self.monitor_high_risk()
        print("✅ Daily interventions completed")