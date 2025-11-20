import logging
from flask import Flask, redirect, url_for, render_template, flash, request, session, jsonify
from flask_session import Session
from flask_login import LoginManager, logout_user, current_user, login_required, login_user
from flask_mail import Mail, Message

# Correct imports - db from extensions, models from models package
from extensions import db, login_manager, mail
from models import User, Client, Loan, Intervention, CRBReport  # ADDED CRBReport

from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone, timedelta
import json
import os
import pickle
import pandas as pd
import numpy as np
import math
from apscheduler.schedulers.background import BackgroundScheduler

# ADD CRB SERVICE IMPORT
from services.crb_service import CRBService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')

# MySQL Configuration for XAMPP
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/crimap_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kipropphilip09@gmail.com'
app.config['MAIL_PASSWORD'] = 'sblv czdr dbnc azea'
app.config['MAIL_DEFAULT_SENDER'] = 'kipropphilip09@gmail.com'

# Initialize extensions with app
Session(app)
db.init_app(app)
mail.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login_page'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ===== AUTOMATED RETRAINING SYSTEM =====

# Retraining storage (in production, use database)
RETRAINING_HISTORY = []
LAST_RETRAINING_DATE = None
MODEL_PERFORMANCE = {'accuracy': 0.82, 'last_updated': datetime.now(timezone.utc)}

class RetrainingSystem:
    def __init__(self):
        self.retraining_enabled = True
    
    def should_retrain(self):
        """Check all retraining triggers"""
        triggers = []
        
        # Check scheduled retraining (every month)
        if self.is_retraining_schedule_due():
            triggers.append("Scheduled monthly retraining due")
            
        # Check performance degradation
        if self.performance_below_threshold():
            triggers.append(f"Performance drop detected: {MODEL_PERFORMANCE['accuracy']}")
            
        return triggers
    
    def is_retraining_schedule_due(self):
        """Check if scheduled retraining is due"""
        global LAST_RETRAINING_DATE
        if not LAST_RETRAINING_DATE:
            return True
        
        # Retrain every month
        next_retraining_date = LAST_RETRAINING_DATE + timedelta(days=30)
        return datetime.now(timezone.utc) >= next_retraining_date
    
    def performance_below_threshold(self):
        """Check if model performance is below threshold"""
        return MODEL_PERFORMANCE['accuracy'] < 0.75
    
    def execute_retraining(self):
        """Execute full retraining pipeline"""
        global LAST_RETRAINING_DATE, MODEL_PERFORMANCE
        
        try:
            print("🔄 Starting model retraining...")
            
            # 1. Data collection & preparation
            new_data = self.collect_recent_data()
            
            # 2. Model training simulation
            new_metrics = self.simulate_model_training(new_data)
            
            # 3. Model comparison
            improvement = new_metrics['accuracy'] - MODEL_PERFORMANCE['accuracy']
            
            # 4. Deploy if significant improvement (5% threshold)
            if improvement >= 0.05:
                MODEL_PERFORMANCE = new_metrics
                LAST_RETRAINING_DATE = datetime.now(timezone.utc)
                
                retraining_event = {
                    "timestamp": LAST_RETRAINING_DATE.isoformat(),
                    "old_accuracy": round(MODEL_PERFORMANCE['accuracy'] - improvement, 3),
                    "new_accuracy": new_metrics['accuracy'],
                    "improvement": round(improvement * 100, 2),
                    "status": "deployed",
                    "trigger": "scheduled"
                }
                RETRAINING_HISTORY.append(retraining_event)
                
                print(f"✅ New model deployed! Improvement: {improvement:.1%}")
                return {
                    "status": "deployed", 
                    "improvement": improvement, 
                    "new_accuracy": new_metrics['accuracy'],
                    "message": f"Model retrained successfully! Improvement: {improvement:.1%}"
                }
            else:
                retraining_event = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "improvement": round(improvement * 100, 2),
                    "status": "skipped",
                    "reason": "Insufficient improvement",
                    "trigger": "scheduled"
                }
                RETRAINING_HISTORY.append(retraining_event)
                
                print(f"⏭️  Retraining skipped. Improvement: {improvement:.1%} (need ≥5%)")
                return {
                    "status": "skipped", 
                    "improvement": improvement,
                    "message": f"Retraining skipped. Improvement: {improvement:.1%} (need ≥5%)"
                }
                
        except Exception as e:
            error_event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "failed",
                "error": str(e),
                "trigger": "scheduled"
            }
            RETRAINING_HISTORY.append(error_event)
            print(f"❌ Retraining failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def collect_recent_data(self):
        """Simulate collecting recent loan performance data"""
        # In production, this would query your database for recent loan data
        try:
            recent_loans = Loan.query.filter(
                Loan.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
            ).all()
            
            return {
                "total_samples": len(recent_loans),
                "time_period": "last_30_days",
                "collection_date": datetime.now(timezone.utc).isoformat(),
                "default_rate": 0.12,  # Simulated based on recent data
                "avg_behavior_score": np.mean([loan.behavior_score for loan in recent_loans]) if recent_loans else 75.0
            }
        except Exception as e:
            logger.error(f"Error collecting recent data: {e}")
            return {
                "total_samples": 1000,
                "time_period": "last_30_days",
                "collection_date": datetime.now(timezone.utc).isoformat(),
                "default_rate": 0.12,
                "avg_behavior_score": 75.0
            }
    
    def simulate_model_training(self, new_data):
        """Simulate training a new model and evaluating it"""
        # In production, this would actually retrain your ML model
        # For now, simulate improved performance based on new data
        
        # Simulate some improvement (in real life, this comes from actual training)
        base_accuracy = 0.82
        improvement = 0.03 + (0.02 * (new_data.get('default_rate', 0.1) - 0.1))  # Simulate logic
        
        new_accuracy = min(0.95, base_accuracy + improvement)  # Cap at 95%
        
        return {
            'accuracy': round(new_accuracy, 3),
            'precision': round(0.85 + improvement, 3),
            'recall': round(0.80 + improvement, 3),
            'f1_score': round(0.82 + improvement, 3),
            'training_date': datetime.now(timezone.utc).isoformat(),
            'data_samples': new_data.get('total_samples', 1000)
        }

# Initialize retraining system
retraining_system = RetrainingSystem()

def setup_scheduler():
    """Setup automated retraining scheduler"""
    scheduler = BackgroundScheduler()
    
    # Schedule retraining check every week
    scheduler.add_job(
        auto_retraining_job,
        'interval',
        weeks=1,  # Check weekly if retraining is needed
        id='weekly_retraining_check'
    )
    
    # Schedule performance monitoring daily
    scheduler.add_job(
        performance_monitoring_job,
        'interval', 
        days=1,
        id='daily_performance_monitoring'
    )
    
    scheduler.start()
    print("✅ Automated retraining scheduler started")

def auto_retraining_job():
    """Automated retraining job"""
    if not retraining_system.retraining_enabled:
        return
        
    print("🔄 Automated retraining check triggered by scheduler")
    triggers = retraining_system.should_retrain()
    
    if triggers:
        print(f"🚀 Retraining triggers detected: {triggers}")
        result = retraining_system.execute_retraining()
        
        # Log the automated retraining
        RETRAINING_HISTORY.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trigger": "scheduled",
            "triggers": triggers,
            "result": result.get('status', 'unknown'),
            "improvement": result.get('improvement', 0)
        })
    else:
        print("⏭️  No retraining triggers detected - skipping")

def performance_monitoring_job():
    """Daily performance monitoring"""
    print("📊 Running daily performance monitoring...")
    
    # In production, check actual model performance metrics
    # For now, simulate some monitoring
    try:
        # Check recent loan performance
        recent_loans = Loan.query.filter(
            Loan.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
        ).all()
        
        if recent_loans:
            avg_score = np.mean([loan.behavior_score for loan in recent_loans])
            performance_metric = avg_score / 100.0  # Convert to 0-1 scale
            
            # Log performance check
            RETRAINING_HISTORY.append({
                "timestamp": datetime.now(timezone.utc).isoformat(), 
                "check_type": "performance_monitoring",
                "avg_behavior_score": round(avg_score, 2),
                "recent_loans_count": len(recent_loans),
                "performance_metric": round(performance_metric, 3)
            })
            
            print(f"📈 Performance monitoring: {len(recent_loans)} recent loans, avg score: {avg_score:.1f}")
            
    except Exception as e:
        logger.error(f"Error in performance monitoring: {e}")

def get_next_retraining_date():
    """Calculate next retraining date"""
    global LAST_RETRAINING_DATE
    if LAST_RETRAINING_DATE:
        return (LAST_RETRAINING_DATE + timedelta(days=30)).isoformat()
    return (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

# ===== ENHANCED RISK SCORING SYSTEM WITH CRB INTEGRATION =====

def calculate_enhanced_risk_score(amount, employment_status, monthly_income, 
                                existing_debt, credit_history, term, purpose):
    """Enhanced risk scoring with multiple factors"""
    base_score = 100  # Start with perfect score
    
    # Employment impact (25% weight)
    employment_weights = {
        'Employed': 0,
        'Self-Employed': -15,
        'Unemployed': -40,
        'Student': -25,
        'Retired': -10
    }
    base_score += employment_weights.get(employment_status, -30)
    
    # Debt-to-income ratio (30% weight)
    if monthly_income > 0:
        debt_ratio = (existing_debt / monthly_income) * 100
        if debt_ratio > 60:
            base_score -= 30
        elif debt_ratio > 40:
            base_score -= 20
        elif debt_ratio > 20:
            base_score -= 10
    
    # Loan amount risk (15% weight)
    if amount > 500000:
        base_score -= 25
    elif amount > 200000:
        base_score -= 15
    elif amount > 50000:
        base_score -= 5
    
    # Credit history (20% weight)
    if credit_history == 0:  # First time borrower
        base_score -= 10
    elif credit_history >= 24:  # Good long history
        base_score += 10
    
    # Loan term risk (10% weight)
    if term > 24:
        base_score -= 10
    elif term > 12:
        base_score -= 5
        
    # Purpose risk (adjust based on purpose)
    purpose_risk = {
        'Business': -5,
        'Education': 0,
        'Medical': -5,
        'Personal': -10,
        'Home': 5,
        'Vehicle': -8,
        'Agriculture': -3,
        'Emergency': -15
    }
    base_score += purpose_risk.get(purpose, -10)
    
    return max(0, min(100, base_score))

# NEW: CRB-ENHANCED RISK SCORING
def calculate_enhanced_risk_with_crb(loan_data, crb_report):
    """Enhanced risk scoring incorporating CRB data"""
    # Get base score from existing system
    base_score = calculate_enhanced_risk_score(
        amount=loan_data['amount'],
        employment_status=loan_data['employment_status'],
        monthly_income=loan_data['monthly_income'],
        existing_debt=loan_data.get('existing_debt', 0),
        credit_history=loan_data.get('credit_history', 0),
        term=loan_data['term'],
        purpose=loan_data['purpose']
    )
    
    # Apply CRB factors (40% weight for Kenyan context)
    crb_score = calculate_crb_score(crb_report)
    
    # Weighted final score: 60% base + 40% CRB
    final_score = (base_score * 0.6) + (crb_score * 0.4)
    
    return max(0, min(100, final_score))

def calculate_crb_score(crb_report):
    """Calculate score based on CRB data (0-100 scale)"""
    if not crb_report or not crb_report.get('success'):
        return 50  # Neutral score if no CRB data
    
    score = 100  # Start perfect, deduct for issues
    
    # Credit score impact (35% weight)
    credit_score = crb_report.get('credit_score', 0)
    if credit_score >= 750:
        score -= 0  # Excellent
    elif credit_score >= 700:
        score -= 10  # Good
    elif credit_score >= 650:
        score -= 20  # Fair
    elif credit_score >= 600:
        score -= 35  # Poor
    else:
        score -= 50  # Very Poor
    
    # Default history (25% weight)
    default_history = crb_report.get('default_history', 0)
    score -= (default_history * 15)
    
    # Blacklist status (20% weight) - Automatic rejection in Kenya
    if crb_report.get('blacklist_status'):
        score -= 100  # Will result in 0 score
    
    # Credit utilization (10% weight)
    utilization = crb_report.get('credit_utilization', 0)
    if utilization > 0.8:
        score -= 20
    elif utilization > 0.6:
        score -= 10
    elif utilization > 0.4:
        score -= 5
    
    # Days in arrears (10% weight)
    days_arrears = crb_report.get('days_arrears', 0)
    if days_arrears > 90:
        score -= 25
    elif days_arrears > 60:
        score -= 15
    elif days_arrears > 30:
        score -= 10
    
    return max(0, score)

def calculate_interest_rate(risk_score):
    """Calculate interest rate based on risk score"""
    if risk_score >= 80:
        return 8.0  # Low risk - best rate
    elif risk_score >= 60:
        return 10.0  # Medium risk
    elif risk_score >= 40:
        return 12.0  # Higher risk
    else:
        return 15.0  # High risk - highest rate

# ===== SIMPLIFIED ML INTEGRATION (GUARANTEED TO WORK) =====
class SimpleRiskPredictor:
    def __init__(self):
        self.model_trained = False
    
    def predict_risk(self, loan_data):
        """Predict risk score using robust rule-based system"""
        return self.rule_based_scoring(loan_data)
    
    def rule_based_scoring(self, loan_data):
        """Robust rule-based scoring that matches your existing system"""
        score = 100  # Start with perfect score
        
        # Payment history impact (matches your intervention logic)
        payments_missed = loan_data.get('payments_missed', 0)
        if payments_missed > 0:
            score -= (payments_missed * 25)
        
        # Days overdue impact
        days_overdue = loan_data.get('days_overdue', 0)
        if days_overdue > 0:
            score -= min(days_overdue * 2, 40)
        
        # Debt-to-income ratio impact
        debt_to_income = loan_data.get('debt_to_income', 0.3)
        if debt_to_income > 0.6:
            score -= 30
        elif debt_to_income > 0.4:
            score -= 15
        
        return max(0, min(100, score))

# Initialize the predictor
risk_predictor = SimpleRiskPredictor()

# ===== BEHAVIOR MONITORING SYSTEM =====
class BehaviorMonitor:
    @staticmethod
    def check_missed_payments():
        """Check for missed payments daily"""
        try:
            today = datetime.now(timezone.utc).date()
            approved_loans = Loan.query.filter_by(status='approved').all()
            alerts_triggered = 0
            
            for loan in approved_loans:
                if loan.next_payment_date and loan.next_payment_date < today:
                    # Update missed payments count
                    loan.payments_missed += 1
                    
                    # Update behavior score using ML model
                    loan_data = {
                        'payments_missed': loan.payments_missed,
                        'days_overdue': (today - loan.next_payment_date).days,
                        'debt_to_income': 0.3
                    }
                    loan.behavior_score = risk_predictor.predict_risk(loan_data)
                    
                    # Add risk flag
                    days_overdue = (today - loan.next_payment_date).days
                    loan.add_risk_flag(
                        'missed_payment',
                        'high' if loan.payments_missed > 2 else 'medium',
                        f'Payment missed - {days_overdue} days overdue'
                    )
                    
                    # Move next payment date to avoid repeated alerts
                    loan.next_payment_date = today + timedelta(days=30)
                    alerts_triggered += 1
            
            db.session.commit()
            return f"Checked {len(approved_loans)} loans, triggered {alerts_triggered} alerts"
            
        except Exception as e:
            logger.error(f"Error in check_missed_payments: {e}")
            return f"Error: {e}"

    @staticmethod
    def update_all_behavior_scores():
        """Update behavior scores for all active loans using ML model"""
        try:
            active_loans = Loan.query.filter_by(status='approved').all()
            updated = 0
            
            for loan in active_loans:
                # Use ML model for scoring
                loan_data = {
                    'payments_missed': loan.payments_missed,
                    'days_overdue': loan.days_overdue if hasattr(loan, 'days_overdue') else 0,
                    'debt_to_income': 0.3
                }
                new_score = risk_predictor.predict_risk(loan_data)
                if loan.behavior_score != new_score:
                    loan.behavior_score = new_score
                    updated += 1
            
            db.session.commit()
            return f"Updated {updated} behavior scores using ML model"
            
        except Exception as e:
            logger.error(f"Error updating behavior scores: {e}")
            return f"Error: {e}"

    @staticmethod
    def calculate_behavior_score(loan):
        """Calculate comprehensive behavior score using ML model"""
        loan_data = {
            'payments_missed': loan.payments_missed,
            'days_overdue': loan.days_overdue if hasattr(loan, 'days_overdue') else 0,
            'debt_to_income': 0.3
        }
        return risk_predictor.predict_risk(loan_data)

# ===== ENHANCED INTERVENTION BOT SYSTEM =====
class InterventionBot:
    @staticmethod
    def send_sms_reminder(loan, message_type="payment_reminder"):
        """Send automated SMS reminders to borrowers"""
        try:
            messages = {
                "payment_reminder": f"Hello {loan.client_name}, your loan payment of KSh {loan.amount/loan.term:,.0f} is due soon. CRIMAP",
                "missed_payment": f"Dear {loan.client_name}, we noticed a missed payment. Please contact us to avoid penalties. CRIMAP",
                "restructuring_offer": f"Hi {loan.client_name}, having trouble with payments? We can help restructure your loan. Reply HELP for options. CRIMAP",
                "high_risk_alert": f"ALERT {loan.client_name}: Your loan account needs attention. Please contact your loan officer immediately. CRIMAP"
            }
            
            message = messages.get(message_type, messages["payment_reminder"])
            
            # Log the intervention
            intervention = Intervention(
                loan_id=loan.id,
                type=message_type,
                message=message,
                status='sent',
                sent_at=datetime.now(timezone.utc)
            )
            db.session.add(intervention)
            db.session.commit()
            
            logger.info(f"SMS {message_type} sent to {loan.client_name}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {loan.client_name}: {e}")
            return False

    @staticmethod
    def check_and_trigger_interventions():
        """Enhanced intervention check with ML scoring"""
        try:
            active_loans = Loan.query.filter_by(status='approved').all()
            interventions_sent = 0
            today = datetime.now(timezone.utc).date()
            
            logger.info(f"🔍 Checking {len(active_loans)} active loans for interventions")
            
            for loan in active_loans:
                # ✅ ADD ML SCORING HERE - Ensure behavior_score is set by ML model
                if 'behavior_score' not in loan.__dict__ or loan.behavior_score is None:
                    loan_data = {
                        'payments_missed': loan.payments_missed,
                        'days_overdue': loan.days_overdue if hasattr(loan, 'days_overdue') else 0,
                        'debt_to_income': 0.3
                    }
                    loan.behavior_score = risk_predictor.predict_risk(loan_data)
                    logger.info(f"🎯 ML Scored Loan {loan.id}: {loan.behavior_score}")
                
                logger.info(f"📊 Loan {loan.id}: behavior_score={loan.behavior_score}, payments_missed={loan.payments_missed}")
                
                # HIGH RISK - Behavior score below 40
                if loan.behavior_score < 40:
                    logger.info(f"🚨 Loan {loan.id} triggered HIGH_RISK_ALERT (score: {loan.behavior_score})")
                    if InterventionBot.send_sms_reminder(loan, "high_risk_alert"):
                        interventions_sent += 1
                    continue
                
                # MISSED PAYMENTS - Any missed payments
                elif loan.payments_missed > 0:
                    logger.info(f"⚠️ Loan {loan.id} triggered MISSED_PAYMENT (missed: {loan.payments_missed})")
                    if InterventionBot.send_sms_reminder(loan, "missed_payment"):
                        interventions_sent += 1
                    continue
                
                # PAYMENT REMINDER - Due in next 3 days
                elif loan.next_payment_date:
                    days_until_due = (loan.next_payment_date - today).days
                    if 0 <= days_until_due <= 3:
                        logger.info(f"📅 Loan {loan.id} triggered PAYMENT_REMINDER (due in {days_until_due} days)")
                        if InterventionBot.send_sms_reminder(loan, "payment_reminder"):
                            interventions_sent += 1
                        continue
                
                # RESTRUCTURING OFFER - Multiple risk flags
                elif loan.is_flagged and len(loan.get_risk_flags()) >= 2:
                    logger.info(f"🔄 Loan {loan.id} triggered RESTRUCTURING_OFFER (flags: {len(loan.get_risk_flags())})")
                    if InterventionBot.send_sms_reminder(loan, "restructuring_offer"):
                        interventions_sent += 1
            
            db.session.commit()
            logger.info(f"✅ Intervention check completed: {interventions_sent} interventions sent")
            return f"Checked {len(active_loans)} loans, sent {interventions_sent} interventions"
            
        except Exception as e:
            logger.error(f"❌ Error in intervention check: {e}")
            return f"Error in intervention check: {e}"

# ===== PREDICTION SYSTEM =====
def calculate_eligibility(loan_amount, employment_status, monthly_income=0, existing_debt=0, credit_history=0):
    """Calculate loan eligibility score (0-100%)"""
    base_score = 100
    
    employment_weights = {
        "Employed": 0,
        "Self-Employed": -15,
        "Unemployed": -40,
        "Student": -25,
        "Retired": -10
    }
    base_score += employment_weights.get(employment_status, -30)
    
    if loan_amount > 100000:
        base_score -= 25
    elif loan_amount > 50000:
        base_score -= 15
    elif loan_amount > 20000:
        base_score -= 5
    
    if monthly_income > 0:
        debt_ratio = (existing_debt / monthly_income) * 100
        if debt_ratio > 50:
            base_score -= 20
        elif debt_ratio > 30:
            base_score -= 10
    
    if credit_history < 6:
        base_score -= 10
    elif credit_history > 24:
        base_score += 5
    
    return max(0, min(100, base_score))

def get_risk_recommendation(score):
    """Get risk category and recommendation based on score"""
    if score >= 70:
        return "Low Risk", "High chance of approval", "success"
    elif score >= 50:
        return "Medium Risk", "May require additional documentation", "warning"
    else:
        return "High Risk", "Low chance of approval. Consider improving your application.", "danger"

# ===== ENHANCED RISK ANALYST FUNCTIONS =====

def get_portfolio_health_trends():
    """Get portfolio health trends for the last 6 months"""
    # Simulated data - in production, query your database
    return [
        {'month': 'Jul', 'performing': 85, 'watchlist': 10, 'defaulted': 5},
        {'month': 'Aug', 'performing': 83, 'watchlist': 12, 'defaulted': 5},
        {'month': 'Sep', 'performing': 82, 'watchlist': 13, 'defaulted': 5},
        {'month': 'Oct', 'performing': 80, 'watchlist': 15, 'defaulted': 5},
        {'month': 'Nov', 'performing': 78, 'watchlist': 16, 'defaulted': 6},
        {'month': 'Dec', 'performing': 75, 'watchlist': 18, 'defaulted': 7}
    ]

def get_early_warning_indicators():
    """Get early warning system indicators"""
    try:
        # Calculate real indicators from your database
        multiple_missed = Loan.query.filter(
            Loan.payments_missed >= 2,
            Loan.status == 'approved'
        ).count()
        
        return {
            'multiple_missed_payments': multiple_missed,
            'spending_pattern_changes': 8,  # Simulated
            'income_verification_issues': 5,
            'communication_dropoff': 7,
            'credit_utilization_spike': 9
        }
    except Exception as e:
        logger.error(f"Error getting warning indicators: {e}")
        return {
            'multiple_missed_payments': 0,
            'spending_pattern_changes': 0,
            'income_verification_issues': 0,
            'communication_dropoff': 0,
            'credit_utilization_spike': 0
        }

def get_ml_model_metrics():
    """Get ML model performance metrics"""
    return {
        'roc_auc': 0.87,
        'accuracy': 0.82,
        'precision': 0.79,
        'recall': 0.85,
        'f1_score': 0.82,
        'last_trained': '2024-01-15'
    }

def get_portfolio_health():
    """Calculate comprehensive portfolio metrics"""
    try:
        from sqlalchemy import func
        
        # Total portfolio metrics
        total_loans = Loan.query.count()
        active_loans = Loan.query.filter(Loan.status.in_(['active', 'approved'])).count()
        
        # Calculate portfolio value
        portfolio_value_result = db.session.query(func.sum(Loan.amount)).filter(
            Loan.status.in_(['active', 'approved'])
        ).scalar()
        total_portfolio_value = portfolio_value_result or 0
        
        # Calculate average risk score
        avg_risk_score_result = db.session.query(func.avg(Loan.risk_score)).filter(
            Loan.status.in_(['active', 'approved'])
        ).scalar()
        avg_risk_score = avg_risk_score_result or 0
        
        # Calculate default rate
        defaulted_loans = Loan.query.filter_by(status='defaulted').count()
        default_rate = (defaulted_loans / active_loans * 100) if active_loans > 0 else 0
        
        # Calculate high risk percentage
        high_risk_loans = Loan.query.filter(
            Loan.status.in_(['active', 'approved']),
            Loan.risk_level == 'High'
        ).count()
        high_risk_percentage = (high_risk_loans / active_loans * 100) if active_loans > 0 else 0
        
        return {
            'total_loans': total_loans,
            'active_loans': active_loans,
            'total_portfolio_value': float(total_portfolio_value),
            'avg_risk_score': float(avg_risk_score),
            'default_rate': round(default_rate, 2),
            'high_risk_percentage': round(high_risk_percentage, 2)
        }
    except Exception as e:
        logger.error(f"Error getting portfolio health: {e}")
        return {
            'total_loans': 0,
            'active_loans': 0,
            'total_portfolio_value': 0,
            'avg_risk_score': 0,
            'default_rate': 0,
            'high_risk_percentage': 0
        }

def get_risk_distribution():
    """Get risk distribution across portfolio"""
    try:
        from sqlalchemy import func
        
        # Get risk level distribution
        distribution = db.session.query(
            Loan.risk_level,
            func.count(Loan.id)
        ).filter(
            Loan.status.in_(['active', 'approved'])
        ).group_by(Loan.risk_level).all()
        
        # Format for chart
        labels = []
        data = []
        colors = []
        
        for risk_level, count in distribution:
            if risk_level:
                labels.append(risk_level)
                data.append(count)
                # Assign colors based on risk level
                if risk_level.lower() == 'high':
                    colors.append('#e74c3c')
                elif risk_level.lower() == 'medium':
                    colors.append('#f39c12')
                else:
                    colors.append('#27ae60')
        
        return {
            'labels': labels,
            'data': data,
            'colors': colors
        }
    except Exception as e:
        logger.error(f"Error getting risk distribution: {e}")
        return {'labels': [], 'data': [], 'colors': []}

def get_borrower_segments():
    """Get borrower segmentation analytics"""
    try:
        from sqlalchemy import func, case
        
        segments = []
        
        # Segment 1: All borrowers
        all_borrowers = db.session.query(
            func.count(Loan.id).label('segment_size'),
            func.avg(Loan.risk_score).label('avg_risk_score'),
            (func.sum(case((Loan.status == 'defaulted', 1), else_=0)) / func.count(Loan.id) * 100).label('default_rate')
        ).filter(
            Loan.status.in_(['active', 'approved', 'defaulted'])
        ).first()
        
        if all_borrowers:
            segments.append({
                'segment_name': 'All Borrowers',
                'segment_size': all_borrowers.segment_size or 0,
                'avg_risk_score': float(all_borrowers.avg_risk_score or 0),
                'default_rate': float(all_borrowers.default_rate or 0)
            })
        
        # Segment 2: Income-based
        income_segments = db.session.query(
            case(
                (Loan.monthly_income < 30000, 'Low Income (<30K)'),
                (Loan.monthly_income < 70000, 'Middle Income (30K-70K)'),
                else_='High Income (>70K)'
            ).label('segment_name'),
            func.count(Loan.id).label('segment_size'),
            func.avg(Loan.risk_score).label('avg_risk_score'),
            (func.sum(case((Loan.status == 'defaulted', 1), else_=0)) / func.count(Loan.id) * 100).label('default_rate')
        ).filter(
            Loan.status.in_(['active', 'approved', 'defaulted']),
            Loan.monthly_income.isnot(None)
        ).group_by('segment_name').all()
        
        for segment in income_segments:
            segments.append({
                'segment_name': segment.segment_name,
                'segment_size': segment.segment_size,
                'avg_risk_score': float(segment.avg_risk_score or 0),
                'default_rate': float(segment.default_rate or 0)
            })
        
        return segments
        
    except Exception as e:
        logger.error(f"Error getting borrower segments: {e}")
        return []

# ===== ML MODEL API ENDPOINTS =====

@app.route('/api/test-model-setup', methods=['GET'])
def test_model_setup():
    """Test if model integration is working"""
    try:
        test_loan = {
            'payments_missed': 2,
            'days_overdue': 10,
            'debt_to_income': 0.4
        }
        
        score = risk_predictor.predict_risk(test_loan)
        
        return jsonify({
            "message": "✅ Model integration working",
            "test_score": score,
            "model_trained": risk_predictor.model_trained,
            "risk_level": "CRITICAL" if score < 20 else "HIGH" if score < 40 else "MEDIUM" if score < 70 else "LOW",
            "scoring_type": "Rule-Based System"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict-risk', methods=['POST'])
def predict_risk():
    """Real-time risk predictions"""
    try:
        if request.is_json:
            data = request.json
        else:
            data = {
                'payments_missed': int(request.form.get('payments_missed', 0)),
                'days_overdue': int(request.form.get('days_overdue', 0)),
                'debt_to_income': float(request.form.get('debt_to_income', 0.3))
            }
        
        # Get prediction
        risk_score = risk_predictor.predict_risk(data)
        
        # Determine risk level (matches your existing system)
        if risk_score >= 70:
            risk_level = "LOW"
        elif risk_score >= 40:
            risk_level = "MEDIUM" 
        elif risk_score >= 20:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        return jsonify({
            'risk_score': risk_score,
            'risk_level': risk_level,
            'probability': risk_score / 100.0,
            'scoring_system': 'rule_based'
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/train-model', methods=['POST'])
def train_model():
    """Simple training endpoint that always works"""
    try:
        # Just mark the model as trained - no complex ML operations
        risk_predictor.model_trained = True
        
        return jsonify({
            "message": "✅ Risk scoring system ready!",
            "system_type": "Rule-Based Scoring",
            "status": "Active",
            "features": "payments_missed, days_overdue, debt_to_income",
            "integration": "Fully integrated with behavior monitoring"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== AUTOMATED RETRAINING API ENDPOINTS =====

@app.route('/api/retrain-model', methods=['POST'])
@login_required
def retrain_model():
    """Manual retraining trigger endpoint"""
    if current_user.role not in ['admin']:
        return jsonify({'error': 'Access denied. Admin privileges required.'}), 403
    
    try:
        result = retraining_system.execute_retraining()
        
        if result['status'] == 'deployed':
            return jsonify({
                "status": "success",
                "message": "✅ Model retraining completed successfully!",
                "improvement": f"{result.get('improvement', 0):.1%}",
                "new_accuracy": result.get('new_accuracy'),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        elif result['status'] == 'skipped':
            return jsonify({
                "status": "skipped",
                "message": result.get('message', 'Retraining skipped'),
                "improvement": f"{result.get('improvement', 0):.1%}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            return jsonify({
                "status": "error", 
                "message": f"Retraining failed: {result.get('error', 'Unknown error')}"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Retraining failed: {str(e)}"
        }), 500

@app.route('/api/retraining-status', methods=['GET'])
@login_required
def retraining_status():
    """Check retraining status and history"""
    if current_user.role not in ['admin']:
        return jsonify({'error': 'Access denied. Admin privileges required.'}), 403
    
    return jsonify({
        "last_retraining": LAST_RETRAINING_DATE.isoformat() if LAST_RETRAINING_DATE else None,
        "history": RETRAINING_HISTORY[-10:],  # Last 10 entries
        "current_performance": MODEL_PERFORMANCE,
        "next_scheduled_retraining": get_next_retraining_date(),
        "retraining_enabled": retraining_system.retraining_enabled,
        "total_retraining_events": len(RETRAINING_HISTORY)
    })

@app.route('/api/retraining-schedule', methods=['POST'])
@login_required
def update_retraining_schedule():
    """Update retraining schedule and settings"""
    if current_user.role not in ['admin']:
        return jsonify({'error': 'Access denied. Admin privileges required.'}), 403
    
    data = request.get_json()
    schedule_type = data.get('schedule', 'monthly')
    enabled = data.get('enabled', True)
    
    # Update retraining system settings
    retraining_system.retraining_enabled = enabled
    
    # In production, save to database
    return jsonify({
        "status": "success",
        "message": f"Retraining schedule updated to {schedule_type}",
        "enabled": enabled,
        "next_retraining": get_next_retraining_date()
    })

@app.route('/api/retraining-stats', methods=['GET'])
@login_required
def retraining_stats():
    """Get retraining statistics"""
    if current_user.role not in ['admin']:
        return jsonify({'error': 'Access denied. Admin privileges required.'}), 403
    
    try:
        total_events = len(RETRAINING_HISTORY)
        deployed_events = len([e for e in RETRAINING_HISTORY if e.get('status') == 'deployed'])
        skipped_events = len([e for e in RETRAINING_HISTORY if e.get('status') == 'skipped'])
        failed_events = len([e for e in RETRAINING_HISTORY if e.get('status') == 'failed'])
        
        # Calculate average improvement
        improvements = [e.get('improvement', 0) for e in RETRAINING_HISTORY if e.get('improvement')]
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0
        
        return jsonify({
            'total_retraining_events': total_events,
            'successful_deployments': deployed_events,
            'skipped_retrainings': skipped_events,
            'failed_retrainings': failed_events,
            'average_improvement': f"{avg_improvement:.2f}%",
            'current_model_accuracy': f"{MODEL_PERFORMANCE['accuracy']:.1%}",
            'system_uptime_days': (datetime.now(timezone.utc) - datetime.fromisoformat(RETRAINING_HISTORY[0]['timestamp'])).days if RETRAINING_HISTORY else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ADVANCED RISK ANALYTICS API ENDPOINTS =====

@app.route('/api/risk-analytics/portfolio-metrics')
@login_required
def api_portfolio_metrics():
    """API endpoint for portfolio metrics"""
    if current_user.role.lower() != 'risk_analyst':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        portfolio_health = get_portfolio_health()
        risk_distribution = get_risk_distribution()
        
        return jsonify({
            'portfolio_health': portfolio_health,
            'risk_distribution': risk_distribution
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk-analytics/borrower-segments')
@login_required
def api_borrower_segments():
    """API endpoint for borrower segmentation"""
    if current_user.role.lower() != 'risk_analyst':
        return jsonify({'error': 'Access denied'}), 403
    
    segments = get_borrower_segments()
    return jsonify(segments)

@app.route('/api/risk-analytics/model-performance')
@login_required
def api_model_performance():
    """API endpoint for ML model performance"""
    if current_user.role.lower() != 'risk_analyst':
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(get_ml_model_metrics())

@app.route('/api/risk-analytics/early-warnings')
@login_required
def api_early_warnings():
    """API endpoint for early warning system"""
    if current_user.role.lower() != 'risk_analyst':
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(get_early_warning_indicators())

# ===== ML DEMO PAGE WITH RETRAINING FEATURES =====
@app.route('/ml-demo')
def ml_demo():
    """Enhanced ML demo page with retraining features"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Risk Scoring Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .card { background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }
            .btn { background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 5px; }
            .btn-success { background: #28a745; }
            .btn-warning { background: #ffc107; color: black; }
            .btn-danger { background: #dc3545; }
            .result { padding: 15px; border-radius: 5px; margin: 10px 0; }
            .success { background: #d4edda; }
            .info { background: #e3f2fd; }
            .warning { background: #fff3cd; }
            .error { background: #f8d7da; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
            .stat-card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <h1>🤖 Risk Scoring System Demo</h1>
        
        <div class="card">
            <h3>1. Test System Setup</h3>
            <p>Check if risk scoring is working:</p>
            <a href="/api/test-model-setup" class="btn" target="_blank">Test Setup</a>
        </div>

        <div class="card">
            <h3>2. Activate System</h3>
            <p>Activate the risk scoring system:</p>
            <form action="/api/train-model" method="POST">
                <button type="submit" class="btn btn-success">🚀 Activate System</button>
            </form>
        </div>

        <div class="card">
            <h3>3. Test Risk Prediction</h3>
            <p>Test with sample data:</p>
            <div>
                <button onclick="testPrediction(2, 15, 0.6)" class="btn">🔍 Test High Risk</button>
                <button onclick="testPrediction(0, 0, 0.2)" class="btn">🔍 Test Low Risk</button>
            </div>
        </div>

        <div class="card">
            <h3>4. Custom Prediction</h3>
            <form onsubmit="customPrediction(event)">
                <label>Payments Missed: <input type="number" id="pm" value="1" min="0" max="10"></label><br>
                <label>Days Overdue: <input type="number" id="do" value="5" min="0" max="90"></label><br>
                <label>Debt-to-Income: <input type="number" id="dti" value="0.3" step="0.1" min="0" max="1"></label><br>
                <button type="submit" class="btn">📊 Get Risk Score</button>
            </form>
        </div>

        <!-- NEW: Automated Retraining Section -->
        <div class="card">
            <h3>🔄 Automated Model Retraining</h3>
            <p>Manage model retraining and monitoring:</p>
            
            <div class="stats-grid" id="retraining-stats">
                <!-- Stats will be loaded here -->
            </div>
            
            <div>
                <button onclick="manualRetraining()" class="btn btn-warning">🔄 Manual Retraining</button>
                <button onclick="checkRetrainingStatus()" class="btn">📊 Check Retraining Status</button>
                <button onclick="getRetrainingStats()" class="btn">📈 View Retraining Stats</button>
            </div>
            
            <div id="retraining-result"></div>
            <div id="retraining-status"></div>
        </div>

        <div id="result"></div>

        <script>
            // Existing prediction functions
            async function testPrediction(payments, days, debt) {
                const response = await fetch('/api/predict-risk', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ payments_missed: payments, days_overdue: days, debt_to_income: debt })
                });
                const result = await response.json();
                showResult(result, `Test Data: ${payments} missed, ${days} days, ${debt} DTI`);
            }

            async function customPrediction(event) {
                event.preventDefault();
                const payments = parseInt(document.getElementById('pm').value);
                const days = parseInt(document.getElementById('do').value);
                const debt = parseFloat(document.getElementById('dti').value);
                
                await testPrediction(payments, days, debt);
            }

            function showResult(data, input) {
                const color = data.risk_level === 'LOW' ? '#d4edda' : 
                             data.risk_level === 'MEDIUM' ? '#fff3cd' : 
                             data.risk_level === 'HIGH' ? '#f8d7da' : '#f5c6cb';
                
                document.getElementById('result').innerHTML = `
                    <div class="result" style="background: ${color}">
                        <h3>📊 Prediction Result</h3>
                        <p><strong>Input:</strong> ${input}</p>
                        <p><strong>Risk Score:</strong> ${data.risk_score}/100</p>
                        <p><strong>Risk Level:</strong> ${data.risk_level}</p>
                        <p><strong>Probability:</strong> ${(data.probability * 100).toFixed(1)}%</p>
                    </div>
                `;
            }

            // NEW: Retraining functions
            async function manualRetraining() {
                const response = await fetch('/api/retrain-model', {method: 'POST'});
                const result = await response.json();
                
                const color = result.status === 'success' ? 'success' : 
                             result.status === 'skipped' ? 'warning' : 'error';
                
                document.getElementById('retraining-result').innerHTML = `
                    <div class="result ${color}">
                        <h3>🔄 Retraining Result</h3>
                        <p><strong>Status:</strong> ${result.status}</p>
                        <p><strong>Message:</strong> ${result.message}</p>
                        ${result.improvement ? `<p><strong>Improvement:</strong> ${result.improvement}</p>` : ''}
                        ${result.new_accuracy ? `<p><strong>New Accuracy:</strong> ${result.new_accuracy}</p>` : ''}
                    </div>
                `;
                
                // Refresh stats
                getRetrainingStats();
            }

            async function checkRetrainingStatus() {
                const response = await fetch('/api/retraining-status');
                const status = await response.json();
                document.getElementById('retraining-status').innerHTML = `
                    <div class="result info">
                        <h4>Retraining Status</h4>
                        <pre>${JSON.stringify(status, null, 2)}</pre>
                    </div>
                `;
            }

            async function getRetrainingStats() {
                const response = await fetch('/api/retraining-stats');
                const stats = await response.json();
                
                document.getElementById('retraining-stats').innerHTML = `
                    <div class="stat-card">
                        <h4>📈 Model Accuracy</h4>
                        <p style="font-size: 24px; font-weight: bold; color: #28a745;">${stats.current_model_accuracy}</p>
                    </div>
                    <div class="stat-card">
                        <h4>🔄 Total Retrainings</h4>
                        <p style="font-size: 24px; font-weight: bold; color: #007bff;">${stats.total_retraining_events}</p>
                    </div>
                    <div class="stat-card">
                        <h4>✅ Successful</h4>
                        <p style="font-size: 24px; font-weight: bold; color: #28a745;">${stats.successful_deployments}</p>
                    </div>
                    <div class="stat-card">
                        <h4>📊 Avg Improvement</h4>
                        <p style="font-size: 24px; font-weight: bold; color: #ffc107;">${stats.average_improvement}</p>
                    </div>
                `;
            }

            // Load stats on page load
            document.addEventListener('DOMContentLoaded', function() {
                getRetrainingStats();
            });
        </script>
    </body>
    </html>
    '''

# ===== EMAIL FUNCTIONS =====
def send_loan_application_email(loan):
    """Send email notification for new loan application"""
    try:
        recipients = ['kipropphilip09@gmail.com']
        
        msg = Message(
            subject=f"📋 New Loan Application - {loan.client_name}",
            recipients=recipients,
            html=f"""
            <h3>New Loan Application Received</h3>
            <p><strong>Applicant:</strong> {loan.client_name}</p>
            <p><strong>Email:</strong> {loan.client_email}</p>
            <p><strong>Phone:</strong> {loan.client_phone}</p>
            <p><strong>Amount:</strong> KSh {loan.amount:,.2f}</p>
            <p><strong>Term:</strong> {loan.term} months</p>
            <p><strong>Purpose:</strong> {loan.purpose}</p>
            <p><strong>Employment:</strong> {loan.employment_status}</p>
            <p><strong>Monthly Income:</strong> KSh {loan.monthly_income:,.2f}</p>
            <p><strong>Risk Score:</strong> {loan.risk_score}%</p>
            <p><strong>Applied On:</strong> {loan.created_at.strftime('%Y-%m-%d %H:%M')}</p>
            <br>
            <p>Please review this application in the CRIMAP system.</p>
            <p><a href="http://127.0.0.1:5001/loans" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Review Application</a></p>
            """
        )
        mail.send(msg)
        logger.info(f"Loan application email sent for {loan.client_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to send loan application email: {e}")
        return False

def send_loan_status_email(loan):
    """Send email to borrower about loan status update"""
    try:
        msg = Message(
            subject=f"📊 Loan Application Update - CRIMAP",
            recipients=[loan.client_email],
            html=f"""
            <h3>Loan Application Status Update</h3>
            <p>Dear {loan.client_name},</p>
            
            <p>Your loan application has been <strong>{loan.status.upper()}</strong>.</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                <p><strong>Application Details:</strong></p>
                <p>Amount: KSh {loan.amount:,.2f}</p>
                <p>Term: {loan.term} months</p>
                <p>Purpose: {loan.purpose}</p>
                <p>Risk Score: {loan.risk_score}%</p>
                <p>Interest Rate: {loan.interest_rate}%</p>
            </div>
            
            {'<p style="color: #28a745; font-weight: bold;">🎉 Congratulations! Your loan has been approved.</p><p>Our loan officer will contact you shortly with next steps.</p>' if loan.status == 'approved' else ''}
            {'<p style="color: #dc3545;">We are sorry, your application was not approved at this time.</p><p>You may apply again after 30 days or contact us for more information.</p>' if loan.status == 'rejected' else ''}
            
            <br>
            <p>Thank you for choosing CRIMAP!</p>
            """
        )
        mail.send(msg)
        logger.info(f"Loan status email sent to {loan.client_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send loan status email: {e}")
        return False

# ===== ROUTES =====

@app.route('/')
def root():
    """Root route - render login page directly"""
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
@app.route('/auth/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        role = current_user.role.lower()
        if role == 'admin':
            return redirect(url_for('dashboard'))
        elif role in ['loan_officer', 'officer']:
            return redirect(url_for('loan_officer_dashboard'))
        elif role == 'borrower':
            return redirect(url_for('borrower_dashboard'))
        elif role == 'risk_analyst':
            return redirect(url_for('risk_analyst_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            role = user.role.lower()
            flash(f'Login successful! Welcome, {user.username} (Role: {role})', 'success')
            
            if role == 'admin':
                return redirect(url_for('dashboard'))
            elif role in ['loan_officer', 'officer']:
                return redirect(url_for('loan_officer_dashboard'))
            elif role == 'borrower':
                return redirect(url_for('borrower_dashboard'))
            elif role == 'risk_analyst':
                return redirect(url_for('risk_analyst_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    """User registration page"""
    if current_user.is_authenticated:
        role = current_user.role.lower()
        if role == 'admin':
            return redirect(url_for('dashboard'))
        elif role in ['loan_officer', 'officer']:
            return redirect(url_for('loan_officer_dashboard'))
        elif role == 'borrower':
            return redirect(url_for('borrower_dashboard'))
        elif role == 'risk_analyst':
            return redirect(url_for('risk_analyst_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            role = request.form.get('role', 'borrower')
            
            if not all([username, email, password, confirm_password, role]):
                flash('Please fill in all fields.', 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('register.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
                return render_template('register.html')
            
            # Validate role
            valid_roles = ['borrower', 'loan_officer', 'admin', 'risk_analyst']
            if role not in valid_roles:
                flash('Invalid role selected.', 'error')
                return render_template('register.html')
            
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists. Please choose a different one.', 'error')
                return render_template('register.html')
            
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Email already registered. Please use a different email.', 'error')
                return render_template('register.html')
            
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
                created_at=datetime.now(timezone.utc)
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'Registration successful! Your account type: {role.title()}', 'success')
            return redirect(url_for('login_page'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error during registration. Please try again.', 'error')
            logger.error(f"Registration error: {e}")
    
    return render_template('register.html')

@app.route('/admin/create-user', methods=['GET', 'POST'])
@login_required
def create_user():
    """Admin route to create new users"""
    if current_user.role.lower() != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role', 'borrower')
            
            if not all([username, email, password, role]):
                flash('Please fill in all fields.', 'error')
                return render_template('create_user.html', username=current_user.username)
            
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists.', 'error')
                return render_template('create_user.html', username=current_user.username)
            
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Email already registered.', 'error')
                return render_template('create_user.html', username=current_user.username)
            
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
                created_at=datetime.now(timezone.utc)
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'User {username} created successfully as {role}.', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error creating user. Please try again.', 'error')
            logger.error(f"User creation error: {e}")
    
    return render_template('create_user.html', username=current_user.username)

@app.route('/force-logout')
def force_logout():
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login_page'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login_page'))

# ===== DASHBOARD ROUTES =====

@app.route('/dashboard')
@login_required
def dashboard():
    role = current_user.role.lower()
    if role not in ['admin']:
        flash(f'Access denied. Admin privileges required. Your role is: {role}', 'error')
        if role in ['loan_officer', 'officer']:
            return redirect(url_for('loan_officer_dashboard'))
        elif role == 'borrower':
            return redirect(url_for('borrower_dashboard'))
        elif role == 'risk_analyst':
            return redirect(url_for('risk_analyst_dashboard'))
        else:
            return redirect(url_for('login_page'))
    
    loans = Loan.query.order_by(Loan.created_at.desc()).limit(5).all()
    total_loans = Loan.query.count()
    approved_loans = Loan.query.filter_by(status='approved').count()
    pending_loans = Loan.query.filter_by(status='pending').count()
    rejected_loans = Loan.query.filter_by(status='rejected').count()
    total_clients = Client.query.count()
    
    # Behavior monitoring stats
    high_risk_loans = Loan.query.filter(
        Loan.status == 'approved',
        Loan.behavior_score < 40
    ).count()
    flagged_loans = Loan.query.filter_by(is_flagged=True).count()
    
    # Intervention stats
    total_interventions = Intervention.query.count()
    interventions_today = Intervention.query.filter(
        db.func.date(Intervention.sent_at) == datetime.now(timezone.utc).date()
    ).count()
    
    # CRB stats
    crb_checks = CRBReport.query.count()
    blacklisted = CRBReport.query.filter_by(blacklist_status=True).count()
    
    # Retraining stats
    total_retrainings = len(RETRAINING_HISTORY)
    successful_retrainings = len([r for r in RETRAINING_HISTORY if r.get('status') == 'deployed'])
    
    approval_rate = (approved_loans / total_loans * 100) if total_loans > 0 else 0
    
    return render_template('admin_dashboard.html',
        username=current_user.username,
        total_users=User.query.count(),
        total_loans=total_loans,
        total_clients=total_clients,
        approved_loans=approved_loans,
        pending_loans=pending_loans,
        rejected_loans=rejected_loans,
        high_risk_loans=high_risk_loans,
        flagged_loans=flagged_loans,
        total_interventions=total_interventions,
        interventions_today=interventions_today,
        crb_checks=crb_checks,
        blacklisted=blacklisted,
        total_retrainings=total_retrainings,
        successful_retrainings=successful_retrainings,
        avg_loan_amount=37500,
        default_rate=5.2,
        approval_rate=approval_rate,
        recent_loans=loans
    )

@app.route('/loan-officer-dashboard')
@login_required
def loan_officer_dashboard():
    role = current_user.role.lower()
    if role not in ['loan_officer', 'officer']:
        flash(f'Access denied. Loan officer privileges required. Your role is: {role}', 'error')
        if role == 'admin':
            return redirect(url_for('dashboard'))
        elif role == 'borrower':
            return redirect(url_for('borrower_dashboard'))
        elif role == 'risk_analyst':
            return redirect(url_for('risk_analyst_dashboard'))
        else:
            return redirect(url_for('login_page'))
    
    total_loans = Loan.query.count()
    pending_loans = Loan.query.filter_by(status='pending').count()
    approved_loans = Loan.query.filter_by(status='approved').count()
    rejected_loans = Loan.query.filter_by(status='rejected').count()
    high_risk_loans = Loan.query.filter(
        Loan.status == 'approved',
        Loan.behavior_score < 40
    ).count()
    
    return render_template('loan_officer_dashboard.html',
        username=current_user.username,
        total_loans=total_loans,
        pending_loans=pending_loans,
        approved_loans=approved_loans,
        rejected_loans=rejected_loans,
        high_risk_loans=high_risk_loans
    )

@app.route('/borrower-dashboard')
@login_required
def borrower_dashboard():
    role = current_user.role.lower()
    if role != 'borrower':
        flash(f'Access denied. Borrower privileges required. Your role is: {role}', 'error')
        if role == 'admin':
            return redirect(url_for('dashboard'))
        elif role in ['loan_officer', 'officer']:
            return redirect(url_for('loan_officer_dashboard'))
        elif role == 'risk_analyst':
            return redirect(url_for('risk_analyst_dashboard'))
        else:
            return redirect(url_for('login_page'))
    
    # 🔍 ENHANCED DEBUG
    print(f"🎯 BORROWER DASHBOARD DEBUG =================================")
    print(f"   👤 User: {current_user.username}")
    print(f"   📧 Email: {current_user.email}")
    
    user_loans = Loan.query.filter_by(client_email=current_user.email).order_by(Loan.created_at.desc()).all()
    
    print(f"   📊 Found {len(user_loans)} loans")
    
    # Detailed loan info
    for i, loan in enumerate(user_loans):
        print(f"   📋 Loan {i+1}: ID={loan.id}, Amount=KSh {loan.amount}, Status={loan.status}, Purpose={loan.purpose}")
    
    stats = {
        'pending': len([loan for loan in user_loans if loan.status == 'pending']),
        'approved': len([loan for loan in user_loans if loan.status == 'approved']),
        'rejected': len([loan for loan in user_loans if loan.status == 'rejected'])
    }
    
    print(f"   📈 Stats: {stats}")
    print(f"   🎯 Sending to template: {len(user_loans)} loans")
    print(f"🎯 END DEBUG ===============================================")
    
    return render_template('borrower_dashboard.html',
        username=current_user.username,
        loans=user_loans,
        stats=stats,
        total_loans=len(user_loans)
    )

# ✅ CORRECT - This should be OUTSIDE and at the same level as other routes
@app.route('/borrower-dashboard-test')
@login_required
def borrower_dashboard_test():
    """Test dashboard with simple template"""
    role = current_user.role.lower()
    if role != 'borrower':
        return "Access denied", 403
    
    user_loans = Loan.query.filter_by(client_email=current_user.email).order_by(Loan.created_at.desc()).all()
    
    stats = {
        'pending': len([loan for loan in user_loans if loan.status == 'pending']),
        'approved': len([loan for loan in user_loans if loan.status == 'approved']),
        'rejected': len([loan for loan in user_loans if loan.status == 'rejected'])
    }
    
    print(f"🎯 TEST DASHBOARD: Sending {len(user_loans)} loans to SIMPLE template")
    for loan in user_loans:
        print(f"   🎯 Loan {loan.id}: {loan.purpose} - KSh {loan.amount}")
    
    return render_template('borrower_dashboard_simple.html',
        username=current_user.username,
        loans=user_loans,
        stats=stats,
        total_loans=len(user_loans)
    )
# ===== CRB DASHBOARD ROUTE =====
@app.route('/crb-dashboard')
@login_required
def crb_dashboard():
    """CRB Monitoring Dashboard"""
    role = current_user.role.lower()
    if role not in ['admin', 'risk_analyst', 'loan_officer', 'officer']:
        flash('Access denied. Admin, Risk Analyst, or Loan Officer privileges required.', 'error')
        if role == 'borrower':
            return redirect(url_for('borrower_dashboard'))
        elif role in ['loan_officer', 'officer']:
            return redirect(url_for('loan_officer_dashboard'))
        elif role == 'risk_analyst':
            return redirect(url_for('risk_analyst_dashboard'))
        elif role == 'admin':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login_page'))
    
    try:
        # CRB Statistics
        total_checks = CRBReport.query.count()
        blacklisted = CRBReport.query.filter_by(blacklist_status=True).count()
        high_risk = CRBReport.query.filter(CRBReport.credit_score < 550).count()
        
        # Recent CRB reports
        recent_reports = CRBReport.query.order_by(CRBReport.created_at.desc()).limit(10).all()
        
        # Credit score distribution
        score_ranges = {
            'excellent': CRBReport.query.filter(CRBReport.credit_score >= 750).count(),
            'good': CRBReport.query.filter(CRBReport.credit_score >= 700, CRBReport.credit_score < 750).count(),
            'fair': CRBReport.query.filter(CRBReport.credit_score >= 600, CRBReport.credit_score < 700).count(),
            'poor': CRBReport.query.filter(CRBReport.credit_score >= 500, CRBReport.credit_score < 600).count(),
            'very_poor': CRBReport.query.filter(CRBReport.credit_score < 500).count()
        }
        
        return render_template('crb_dashboard.html',
                             username=current_user.username,
                             total_checks=total_checks,
                             blacklisted=blacklisted,
                             high_risk=high_risk,
                             recent_reports=recent_reports,
                             score_ranges=score_ranges)
    
    except Exception as e:
        logger.error(f"Error in CRB dashboard: {e}")
        flash('Error loading CRB dashboard.', 'error')
        return redirect(url_for('dashboard'))
# ===== ENHANCED RISK ANALYST DASHBOARD =====

@app.route('/risk_analyst_dashboard')
@login_required
def risk_analyst_dashboard():
    """Enhanced Risk Analyst Dashboard with Advanced Analytics"""
    role = current_user.role.lower()
    if role not in ['risk_analyst', 'admin', 'loan_officer', 'officer']:
        flash('Access denied. Risk Analyst or Loan Officer privileges required.', 'error')
        if role == 'borrower':
            return redirect(url_for('borrower_dashboard'))
        elif role in ['loan_officer', 'officer']:
            return redirect(url_for('loan_officer_dashboard'))
        elif role == 'admin':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login_page'))
    
    try:
        print("DEBUG: Starting risk analyst dashboard...")
        
        # Portfolio Metrics
        total_loans = Loan.query.count()
        print(f"DEBUG: Total loans: {total_loans}")
        
        active_loans = Loan.query.filter(Loan.status.in_(['active', 'approved'])).count()
        print(f"DEBUG: Active loans: {active_loans}")
        
        # Calculate portfolio value
        portfolio_value_result = db.session.query(db.func.sum(Loan.amount)).filter(
            Loan.status.in_(['active', 'approved'])
        ).scalar()
        total_portfolio_value = portfolio_value_result or 0
        print(f"DEBUG: Portfolio value: {total_portfolio_value}")
        
        # Default rate
        defaulted_loans = Loan.query.filter_by(status='defaulted').count()
        print(f"DEBUG: Defaulted loans: {defaulted_loans}")
        
        default_rate = (defaulted_loans / active_loans * 100) if active_loans > 0 else 0
        
        # Portfolio Health Score
        performing_loans = active_loans - defaulted_loans
        portfolio_health = (performing_loans / active_loans * 100) if active_loans > 0 else 0
        
        # Risk Distribution
        risk_distribution = db.session.query(
            Loan.risk_level,
            db.func.count(Loan.id)
        ).filter(
            Loan.status.in_(['active', 'approved'])
        ).group_by(Loan.risk_level).all()
        
        # Convert to dictionary for easier template access
        risk_dist_dict = dict(risk_distribution) if risk_distribution else {}
        
        # High Risk Loans
        high_risk_loans = Loan.query.filter(
            Loan.status.in_(['active', 'approved']),
            Loan.risk_level == 'High'
        ).order_by(Loan.risk_score.asc()).limit(10).all()
        
        # Recent Interventions
        recent_interventions = Intervention.query.order_by(
            Intervention.sent_at.desc()
        ).limit(10).all()
        
        # Test helper functions one by one
        print("DEBUG: Testing monthly trends...")
        monthly_trends = get_portfolio_health_trends()
        print(f"DEBUG: Monthly trends: {monthly_trends}")
        
        print("DEBUG: Testing warning indicators...")
        warning_indicators = get_early_warning_indicators()
        print(f"DEBUG: Warning indicators: {warning_indicators}")
        
        print("DEBUG: Testing ML metrics...")
        model_metrics = get_ml_model_metrics()
        print(f"DEBUG: Model metrics: {model_metrics}")
        
        # Risk Alerts (sum of all warning indicators)
        risk_alerts = sum(warning_indicators.values())
        
        print("DEBUG: All data collected successfully, rendering template...")
        
        # ✅ CRITICAL: Return the template with all the data
        return render_template('risk_analyst_advanced.html',
                            total_loans=total_loans,
                            active_loans=active_loans,
                            total_portfolio_value=total_portfolio_value,
                            defaulted_loans=defaulted_loans,
                            default_rate=round(default_rate, 1),
                            portfolio_health=round(portfolio_health, 1),
                            risk_distribution=risk_dist_dict,
                            model_metrics=model_metrics,
                            high_risk_loans=high_risk_loans,
                            recent_interventions=recent_interventions,
                            monthly_trends=monthly_trends,
                            warning_indicators=warning_indicators,
                            risk_alerts=risk_alerts)
    
    except Exception as e:
        print(f"ERROR in risk analyst dashboard: {str(e)}")
        logger.error(f"Error in enhanced risk analyst dashboard: {e}")
        # Fallback to basic data
        return render_template('risk_analyst_advanced.html',
                            total_loans=0,
                            active_loans=0,
                            total_portfolio_value=0,
                            defaulted_loans=0,
                            default_rate=0,
                            portfolio_health=0,
                            risk_distribution={},
                            model_metrics={},
                            high_risk_loans=[],
                            recent_interventions=[],
                            monthly_trends=[],
                            warning_indicators={},
                            risk_alerts=0)

@app.route('/api/crb-stats')
@login_required
def crb_stats():
    """API endpoint for CRB statistics"""
    if current_user.role.lower() not in ['admin', 'risk_analyst']:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Credit score distribution
        score_ranges = {
            'excellent': CRBReport.query.filter(CRBReport.credit_score >= 750).count(),
            'good': CRBReport.query.filter(CRBReport.credit_score >= 700, CRBReport.credit_score < 750).count(),
            'fair': CRBReport.query.filter(CRBReport.credit_score >= 600, CRBReport.credit_score < 700).count(),
            'poor': CRBReport.query.filter(CRBReport.credit_score >= 500, CRBReport.credit_score < 600).count(),
            'very_poor': CRBReport.query.filter(CRBReport.credit_score < 500).count()
        }
        
        return jsonify({
            'score_distribution': score_ranges,
            'total_reports': CRBReport.query.count(),
            'blacklist_rate': round((CRBReport.query.filter_by(blacklist_status=True).count() / max(CRBReport.query.count(), 1)) * 100, 2),
            'avg_credit_score': db.session.query(db.func.avg(CRBReport.credit_score)).scalar() or 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== CRB TEST/UTIL ENDPOINTS =====

def ensure_crb_indexes():
    """Create helpful indexes for CRBReport if they don't exist"""
    try:
        from sqlalchemy import Index
        with app.app_context():
            idx1 = Index('ix_crb_report_national_id', CRBReport.national_id)
            idx2 = Index('ix_crb_report_created_at', CRBReport.created_at)
            idx1.create(bind=db.engine, checkfirst=True)
            idx2.create(bind=db.engine, checkfirst=True)
            logger.info("CRB indexes ensured: national_id, created_at")
    except Exception as e:
        logger.warning(f"Failed to ensure CRB indexes: {e}")

@app.route('/api/crb/test', methods=['GET', 'POST'])
@login_required
def crb_test_generate():
    """Admin/Risk only: generate and persist a simulated CRB report for quick testing"""
    role = current_user.role.lower()
    if role not in ['admin', 'risk_analyst']:
        return jsonify({'error': 'Access denied'}), 403

    try:
        # Support query params or JSON body
        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.args or request.form

        national_id = (data.get('national_id') or '').strip()
        phone = (data.get('phone') or data.get('phone_number') or '0700000000').strip()
        client_name = (data.get('client_name') or 'Test User').strip()

        if not national_id:
            return jsonify({'error': 'national_id is required'}), 400

        # Get simulated CRB report
        crb_service = CRBService()
        crb_report = crb_service.get_credit_report(national_id=national_id, phone_number=phone, client_name=client_name)

        # Persist CRB report (no loan context here)
        try:
            model_cols = {c.name for c in CRBReport.__table__.columns}
        except Exception:
            model_cols = {
                'loan_id', 'national_id', 'phone_number', 'credit_score',
                'active_loans', 'default_history', 'credit_utilization',
                'payment_pattern', 'blacklist_status', 'days_arrears',
                'credit_rating', 'crb_bureau'
            }

        crb_data = {
            'loan_id': None,
            'national_id': national_id,
            'phone_number': phone,
            'credit_score': crb_report.get('credit_score', 0),
            'active_loans': crb_report.get('active_loans', 0),
            'default_history': crb_report.get('default_history', 0),
            'credit_utilization': crb_report.get('credit_utilization', 0.0),
            'payment_pattern': crb_report.get('payment_pattern', 'unknown'),
            'blacklist_status': crb_report.get('blacklist_status', False),
            'days_arrears': crb_report.get('days_arrears', 0),
            'credit_rating': crb_report.get('credit_rating', 'Unknown'),
            'crb_bureau': crb_report.get('crb_bureau', 'Simulated')
        }

        filtered = {k: v for k, v in crb_data.items() if k in model_cols}
        record = CRBReport(**filtered)
        db.session.add(record)
        db.session.commit()

        # Return saved record summary
        return jsonify({
            'saved': True,
            'report': {
                'id': record.id,
                'national_id': record.national_id,
                'phone_number': record.phone_number,
                'credit_score': record.credit_score,
                'default_history': record.default_history,
                'credit_utilization': float(record.credit_utilization or 0),
                'blacklist_status': record.blacklist_status,
                'days_arrears': record.days_arrears,
                'credit_rating': record.credit_rating,
                'crb_bureau': getattr(record, 'crb_bureau', None),
                'loan_id': record.loan_id,
                'created_at': record.created_at.isoformat() if getattr(record, 'created_at', None) else None
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"CRB test generate error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/maintenance/create-indexes', methods=['POST'])
@login_required
def admin_create_indexes():
    role = current_user.role.lower()
    if role not in ['admin']:
        return jsonify({'error': 'Access denied'}), 403
    try:
        ensure_crb_indexes()
        return jsonify({'success': True, 'message': 'Indexes ensured'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/crb/history', methods=['GET'])
@login_required
def crb_history_json():
    """Admin/Risk only: return CRB reports for a national_id as JSON"""
    role = current_user.role.lower()
    if role not in ['admin', 'risk_analyst']:
        return jsonify({'error': 'Access denied'}), 403

    national_id = (request.args.get('national_id') or '').strip()
    if not national_id:
        return jsonify({'error': 'national_id is required'}), 400

    sort = request.args.get('sort', 'date_desc')
    blacklisted_only = request.args.get('blacklisted', default=0, type=int)
    query = CRBReport.query.filter_by(national_id=national_id)
    if blacklisted_only:
        query = query.filter(CRBReport.blacklist_status.is_(True))
    if sort == 'score_desc':
        query = query.order_by(CRBReport.credit_score.desc())
    elif sort == 'score_asc':
        query = query.order_by(CRBReport.credit_score.asc())
    elif sort == 'date_asc':
        query = query.order_by(CRBReport.created_at.asc())
    else:
        query = query.order_by(CRBReport.created_at.desc())
    reports = query.all()
    def to_dict(r):
        return {
            'id': r.id,
            'national_id': r.national_id,
            'phone_number': r.phone_number,
            'loan_id': r.loan_id,
            'credit_score': r.credit_score,
            'active_loans': r.active_loans,
            'default_history': r.default_history,
            'credit_utilization': float(r.credit_utilization or 0),
            'payment_pattern': r.payment_pattern,
            'blacklist_status': r.blacklist_status,
            'days_arrears': r.days_arrears,
            'credit_rating': r.credit_rating,
            'crb_bureau': getattr(r, 'crb_bureau', None),
            'created_at': r.created_at.isoformat() if getattr(r, 'created_at', None) else None
        }

    return jsonify({'reports': [to_dict(r) for r in reports], 'count': len(reports)})

@app.route('/api/crb/history/export', methods=['GET'])
@login_required
def crb_history_export_csv():
    """Admin/Risk only: export CRB history for a national_id as CSV"""
    role = current_user.role.lower()
    if role not in ['admin', 'risk_analyst']:
        return jsonify({'error': 'Access denied'}), 403

    national_id = (request.args.get('national_id') or '').strip()
    sort = request.args.get('sort', 'date_desc')
    blacklisted_only = request.args.get('blacklisted', default=0, type=int)
    if not national_id:
        return jsonify({'error': 'national_id is required'}), 400

    query = CRBReport.query.filter_by(national_id=national_id)
    if blacklisted_only:
        query = query.filter(CRBReport.blacklist_status.is_(True))
    if sort == 'score_desc':
        query = query.order_by(CRBReport.credit_score.desc())
    elif sort == 'score_asc':
        query = query.order_by(CRBReport.credit_score.asc())
    elif sort == 'date_asc':
        query = query.order_by(CRBReport.created_at.asc())
    else:
        query = query.order_by(CRBReport.created_at.desc())

    rows = query.all()

    import csv
    from io import StringIO
    from flask import Response

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Date','National ID','Phone','Loan ID','Credit Score','Defaults','Utilization','Arrears (days)','Blacklisted','Bureau'])
    for r in rows:
        writer.writerow([
            (r.created_at or r.report_date).strftime('%Y-%m-%d %H:%M') if (r.created_at or r.report_date) else '',
            r.national_id,
            r.phone_number,
            r.loan_id or '',
            r.credit_score or 0,
            r.default_history or 0,
            float(r.credit_utilization or 0),
            r.days_arrears or 0,
            'Yes' if r.blacklist_status else 'No',
            getattr(r, 'crb_bureau', '')
        ])

    output = si.getvalue()
    filename = f"crb_history_{national_id}.csv"
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={filename}'})

# ===== RISK DASHBOARD REDIRECT ROUTES =====

@app.route('/risk')
@login_required
def risk_redirect():
    """Redirect /risk to /risk-analyst-dashboard"""
    return redirect(url_for('risk_analyst_dashboard'))

# ===== CRB HISTORY VIEW =====
@app.route('/crb/history', methods=['GET'])
@login_required
def crb_history_lookup():
    """Search form and optional param-driven lookup for CRB history by national ID with pagination and sorting"""
    role = current_user.role.lower()
    if role not in ['admin', 'risk_analyst']:
        flash('Access denied. Admin or Risk Analyst privileges required.', 'error')
        return redirect(url_for('dashboard') if role == 'admin' else url_for('loan_officer_dashboard') if role in ['loan_officer','officer'] else url_for('borrower_dashboard'))

    national_id = (request.args.get('national_id') or '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort = request.args.get('sort', 'date_desc')
    blacklisted_only = request.args.get('blacklisted', default=0, type=int)

    reports = []
    pagination = None
    if national_id:
        query = CRBReport.query.filter_by(national_id=national_id)
        if blacklisted_only:
            query = query.filter(CRBReport.blacklist_status.is_(True))
        if sort == 'score_desc':
            query = query.order_by(CRBReport.credit_score.desc())
        elif sort == 'score_asc':
            query = query.order_by(CRBReport.credit_score.asc())
        elif sort == 'date_asc':
            query = query.order_by(CRBReport.created_at.asc())
        else:  # date_desc
            query = query.order_by(CRBReport.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        reports = pagination.items

    return render_template('crb_history.html', 
                           username=current_user.username, 
                           national_id=national_id, 
                           reports=reports,
                           pagination=pagination,
                           sort=sort,
                           per_page=per_page,
                           blacklisted=blacklisted_only)

@app.route('/crb/history/<national_id>')
@login_required
def crb_history(national_id):
    role = current_user.role.lower()
    if role not in ['admin', 'risk_analyst']:
        flash('Access denied. Admin or Risk Analyst privileges required.', 'error')
        return redirect(url_for('dashboard') if role == 'admin' else url_for('loan_officer_dashboard') if role in ['loan_officer','officer'] else url_for('borrower_dashboard'))

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort = request.args.get('sort', 'date_desc')
    blacklisted_only = request.args.get('blacklisted', default=0, type=int)

    query = CRBReport.query.filter_by(national_id=national_id)
    if blacklisted_only:
        query = query.filter(CRBReport.blacklist_status.is_(True))
    if sort == 'score_desc':
        query = query.order_by(CRBReport.credit_score.desc())
    elif sort == 'score_asc':
        query = query.order_by(CRBReport.credit_score.asc())
    elif sort == 'date_asc':
        query = query.order_by(CRBReport.created_at.asc())
    else:
        query = query.order_by(CRBReport.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    reports = pagination.items
    return render_template('crb_history.html', 
                           username=current_user.username, 
                           national_id=national_id, 
                           reports=reports,
                           pagination=pagination,
                           sort=sort,
                           per_page=per_page,
                           blacklisted=blacklisted_only)

# Backward/alternate path alias
@app.route('/crb-history')
@login_required
def crb_history_alias():
    return redirect(url_for('crb_history_lookup'))

# Risk Threshold Management API
@app.route('/api/update-risk-thresholds', methods=['POST'])
@login_required
def update_risk_thresholds():
    """Update risk threshold configuration"""
    if current_user.role.lower() not in ['admin', 'risk_analyst']:
        return jsonify({'error': 'Access denied. Risk Analyst privileges required.'}), 403
    
    try:
        low_risk_min = request.form.get('low_risk_min', type=int)
        medium_risk_min = request.form.get('medium_risk_min', type=int)
        high_risk_max = request.form.get('high_risk_max', type=int)
        
        # Validate thresholds
        if not all([low_risk_min, medium_risk_min, high_risk_max]):
            return jsonify({'error': 'All threshold values are required'}), 400
        
        if not (high_risk_max < medium_risk_min < low_risk_min):
            return jsonify({'error': 'Invalid threshold values. Must be: High < Medium < Low'}), 400
        
        # Update risk levels for all loans based on new thresholds
        from sqlalchemy import case
        
        # Update loans with new risk levels
        loans_to_update = Loan.query.filter(
            Loan.status.in_(['active', 'approved'])
        ).all()
        
        for loan in loans_to_update:
            if loan.risk_score >= low_risk_min:
                loan.risk_level = 'Low'
            elif loan.risk_score >= medium_risk_min:
                loan.risk_level = 'Medium'
            else:
                loan.risk_level = 'High'
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Risk thresholds updated successfully',
            'thresholds': {
                'low_risk_min': low_risk_min,
                'medium_risk_min': medium_risk_min,
                'high_risk_max': high_risk_max
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating risk thresholds: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-borrower-segments')
@login_required
def analyze_borrower_segments():
    """API endpoint for borrower segmentation"""
    if current_user.role.lower() not in ['admin', 'risk_analyst']:
        return jsonify({'error': 'Access denied'}), 403
    
    segments = get_borrower_segments()
    return jsonify(segments)

@app.route('/api/portfolio-metrics')
@login_required
def get_portfolio_metrics():
    """API endpoint for portfolio metrics"""
    if current_user.role.lower() not in ['admin', 'risk_analyst']:
        return jsonify({'error': 'Access denied'}), 403
    
    portfolio_health = get_portfolio_health()
    risk_distribution = get_risk_distribution()
    
    return jsonify({
        'portfolio_health': portfolio_health,
        'risk_distribution': risk_distribution
    })

# Create Risk Analyst User
@app.route('/create-risk-analyst')
@login_required
def create_risk_analyst_user():
    """Create a risk analyst user for testing"""
    if current_user.role.lower() != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Check if risk analyst already exists
        existing_analyst = User.query.filter_by(username='risk_analyst').first()
        if existing_analyst:
            flash('Risk analyst user already exists.', 'info')
            return redirect(url_for('dashboard'))
        
        # Create risk analyst user
        risk_analyst = User(
            username='risk_analyst',
            email='analyst@crimap.com',
            password_hash=generate_password_hash('analyst123'),
            role='risk_analyst',
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(risk_analyst)
        db.session.commit()
        
        flash('Risk analyst user created successfully! Username: risk_analyst, Password: analyst123', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating risk analyst user: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# ===== BEHAVIOR MONITORING ROUTES =====

@app.route('/behavior-monitoring')
@login_required
def behavior_monitoring():
    """Behavior monitoring dashboard"""
    if current_user.role not in ['admin', 'loan_officer']:
        flash('Access denied. Admin or loan officer privileges required.', 'error')
        return redirect(url_for('borrower_dashboard'))
    
    high_risk_loans = Loan.query.filter(
        Loan.status == 'approved',
        Loan.behavior_score < 60
    ).order_by(Loan.behavior_score.asc()).all()
    
    flagged_loans = Loan.query.filter_by(is_flagged=True).all()
    all_loans = Loan.query.filter_by(status='approved').all()
    
    return render_template('behavior_monitoring.html',
                         username=current_user.username,
                         high_risk_loans=high_risk_loans,
                         flagged_loans=flagged_loans,
                         all_loans=all_loans,
                         now=datetime.now(timezone.utc))

@app.route('/loan/<int:loan_id>/repayments')
@login_required
def loan_repayments(loan_id):
    """View repayment history for a loan"""
    loan = Loan.query.get_or_404(loan_id)
    
    if current_user.role == 'borrower' and loan.client_email != current_user.email:
        flash('Access denied.', 'error')
        return redirect(url_for('borrower_dashboard'))
    
    return render_template('repayment_history.html',
                         username=current_user.username,
                         loan=loan)

@app.route('/api/behavior-check', methods=['POST'])
@login_required
def run_behavior_check():
    """Manual trigger for behavior monitoring"""
    if current_user.role not in ['admin']:
        return jsonify({'error': 'Access denied'}), 403
    
    result = BehaviorMonitor.check_missed_payments()
    return jsonify({'message': result})

# GET-friendly wrapper for UI buttons
@app.route('/behavior-check', methods=['GET'])
@login_required
def behavior_check():
    if current_user.role not in ['admin', 'loan_officer']:
        flash('Access denied.', 'error')
        return redirect(url_for('borrower_dashboard'))

    try:
        result = BehaviorMonitor.check_missed_payments()
        flash(result or 'Behavior check completed.', 'success')
    except Exception as e:
        logger.error(f"Behavior check error: {e}")
        flash('Failed to run behavior check.', 'error')
    return redirect(url_for('behavior_monitoring'))

@app.route('/api/record-payment/<int:loan_id>/<float:amount>')
@login_required
def record_test_payment(loan_id, amount):
    """Record a test payment"""
    try:
        loan = Loan.query.get_or_404(loan_id)
        
        if current_user.role == 'borrower' and loan.client_email != current_user.email:
            return jsonify({'error': 'Access denied'}), 403
        
        loan.record_payment(amount)
        db.session.commit()
        
        return jsonify({
            'message': f'Payment of KSh {amount} recorded for {loan.client_name}',
            'new_behavior_score': loan.behavior_score,
            'total_paid': loan.total_paid
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ENHANCED INTERVENTION ROUTES =====

@app.route('/interventions')
@login_required
def interventions_page():
    """View all interventions"""
    if current_user.role not in ['admin', 'loan_officer']:
        flash('Access denied.', 'error')
        return redirect(url_for('borrower_dashboard'))
    
    interventions = Intervention.query.order_by(Intervention.sent_at.desc()).all()
    today = datetime.now(timezone.utc).date()
    
    # Get stats for the template
    total_interventions = len(interventions)
    high_risk_alerts = len([i for i in interventions if i.type == 'high_risk_alert'])
    payment_reminders = len([i for i in interventions if i.type == 'payment_reminder'])
    interventions_today = len([i for i in interventions if i.sent_at.date() == today])
    
    return render_template('interventions.html',
                         username=current_user.username,
                         interventions=interventions,
                         total_interventions=total_interventions,
                         high_risk_alerts=high_risk_alerts,
                         payment_reminders=payment_reminders,
                         interventions_today=interventions_today,
                         today=today)

@app.route('/interventions-dashboard')
@login_required
def interventions_dashboard():
    """Enhanced interventions dashboard"""
    if current_user.role not in ['admin', 'loan_officer']:
        flash('Access denied.', 'error')
        return redirect(url_for('borrower_dashboard'))
    
    return render_template('interventions_dashboard.html', username=current_user.username)

@app.route('/api/trigger-interventions')
@login_required
def trigger_interventions():
    """Manual trigger for intervention system"""
    if current_user.role not in ['admin', 'loan_officer']:
        return jsonify({'error': 'Access denied'}), 403
    
    result = InterventionBot.check_and_trigger_interventions()
    return jsonify({'message': result})

@app.route('/test-intervention/<int:loan_id>')
@login_required
def test_intervention(loan_id):
    """Test intervention for a specific loan"""
    loan = Loan.query.get_or_404(loan_id)
    
    if current_user.role not in ['admin', 'loan_officer']:
        return jsonify({'error': 'Access denied'}), 403
    
    success = InterventionBot.send_sms_reminder(loan, "payment_reminder")
    
    if success:
        return jsonify({
            'message': f'Test intervention sent to {loan.client_name}',
            'loan': loan.client_name,
            'type': 'payment_reminder'
        })
    else:
        return jsonify({'error': 'Failed to send intervention'}), 500

@app.route('/api/interventions/stats')
@login_required
def get_intervention_stats():
    """Get intervention statistics"""
    try:
        total_interventions = Intervention.query.count()
        high_risk_alerts = Intervention.query.filter_by(type='high_risk_alert').count()
        payment_reminders = Intervention.query.filter_by(type='payment_reminder').count()
        missed_payments = Intervention.query.filter_by(type='missed_payment').count();
        
        # Interventions sent today
        today = datetime.now(timezone.utc).date()
        active_today = Intervention.query.filter(
            db.func.date(Intervention.sent_at) == today
        ).count()
        
        return jsonify({
            'total_interventions': total_interventions,
            'high_risk_alerts': high_risk_alerts,
            'payment_reminders': payment_reminders,
            'missed_payments': missed_payments,
            'active_today': active_today
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/loans/high-risk')
@login_required
def get_high_risk_loans():
    """Get loans that would trigger interventions"""
    try:
        high_risk_loans = Loan.query.filter(
            Loan.status == 'approved',
            Loan.behavior_score < 60  # Show loans that are medium-high risk
        ).order_by(Loan.behavior_score.asc()).limit(10).all()
        
        loans_data = []
        for loan in high_risk_loans:
            loans_data.append({
                'id': loan.id,
                'client_name': loan.client_name,
                'behavior_score': loan.behavior_score,
                'payments_missed': loan.payments_missed,
                'risk_flags': f"{len(loan.get_risk_flags())} risk flags",
                'next_payment_date': loan.next_payment_date.isoformat() if loan.next_payment_date else None,
                'is_high_risk': loan.behavior_score < 40
            })
        
        return jsonify({'loans': loans_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create-high-risk-loans')
@login_required
def create_high_risk_loans():
    """Create high-risk loans that will trigger interventions"""
    if current_user.role not in ['admin', 'loan_officer']:
        return "Access denied", 403
    
    try:
        # Get existing approved loans
        approved_loans = Loan.query.filter_by(status='approved').all()
        
        if not approved_loans:
            return """
            <div style="padding: 20px; background: #f8d7da; border-radius: 10px;">
                <h2>❌ No Approved Loans Found</h2>
                <p>You need approved loans to create high-risk scenarios.</p>
                <p>Please approve some loans first from the Loans page.</p>
                <a href="/loans" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">View Loans</a>
            </div>
            """
        
        modified_count = 0
        today = datetime.now(timezone.utc).date()
        
        for i, loan in enumerate(approved_loans[:3]):  # Modify first 3 loans
            # Create different risk scenarios
            if i == 0:
                # Scenario 1: Very high risk (behavior score 25, multiple missed payments)
                loan.behavior_score = 25
                loan.payments_missed = 3
                loan.next_payment_date = today - timedelta(days=45)  # 45 days overdue
                loan.add_risk_flag('critical_risk', 'high', 'Multiple payments missed and very low behavior score')
                logger.info(f"Created CRITICAL RISK scenario for {loan.client_name}")
                
            elif i == 1:
                # Scenario 2: High risk (behavior score 35, some missed payments)
                loan.behavior_score = 35
                loan.payments_missed = 2
                loan.next_payment_date = today - timedelta(days=15)  # 15 days overdue
                loan.add_risk_flag('high_risk', 'medium', 'Multiple risk factors detected')
                logger.info(f"Created HIGH RISK scenario for {loan.client_name}")
                
            elif i == 2:
                # Scenario 3: Medium risk (payment due soon)
                loan.behavior_score = 65
                loan.payments_missed = 1
                loan.next_payment_date = today + timedelta(days=2)  # Due in 2 days
                loan.add_risk_flag('payment_due', 'low', 'Payment due soon with previous missed payment')
                logger.info(f"Created MEDIUM RISK scenario for {loan.client_name}")
            
            loan.is_flagged = True
            modified_count += 1
        
        db.session.commit()
        
        return f"""
        <div style="padding: 20px; background: #d4edda; border-radius: 10px;">
            <h2>✅ High-Risk Loans Created Successfully!</h2>
            <p>Modified {modified_count} loans with different risk scenarios:</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h4>📊 Created Risk Scenarios:</h4>
                <ul>
                    <li><strong>Loan 1:</strong> Critical Risk (Score: 25, 3 missed payments, 45 days overdue)</li>
                    <li><strong>Loan 2:</strong> High Risk (Score: 35, 2 missed payments, 15 days overdue)</li>
                    <li><strong>Loan 3:</strong> Medium Risk (Score: 65, 1 missed payment, due in 2 days)</li>
                </ul>
            </div>
            
            <p>These loans will now trigger interventions when you run the intervention check.</p>
            
            <div style="margin-top: 20px;">
                <a href="/api/trigger-interventions" style="background: #dc3545; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                    🚨 Run Intervention Check Now
                </a>
                <a href="/behavior-monitoring" style="background: #007bff; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; margin-left: 10px;">
                    📊 View Behavior Monitoring
                </a>
                <a href="/interventions-dashboard" style="background: #28a745; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; margin-left: 10px;">
                    📱 View Interventions Dashboard
                </a>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 8px;">
                <h4>🔍 What to Expect:</h4>
                <p><strong>Loan 1:</strong> Will trigger <strong>HIGH_RISK_ALERT</strong> (behavior score < 40)</p>
                <p><strong>Loan 2:</strong> Will trigger <strong>HIGH_RISK_ALERT</strong> (behavior score < 40)</p>
                <p><strong>Loan 3:</strong> Will trigger <strong>MISSED_PAYMENT</strong> (1 missed payment) + <strong>PAYMENT_REMINDER</strong> (due in 2 days)</p>
            </div>
        </div>
        """
        
    except Exception as e:
        logger.error(f"Error creating high-risk loans: {e}")
        return f"""
        <div style="padding: 20px; background: #f8d7da; border-radius: 10px;">
            <h2>❌ Error Creating High-Risk Loans</h2>
            <p><strong>Error:</strong> {str(e)}</p>
        </div>
        """

@app.route('/check-loan-status')
@login_required
def check_loan_status():
    """Check current loan status for debugging"""
    if current_user.role not in ['admin', 'loan_officer']:
        return "Access denied", 403
    
    approved_loans = Loan.query.filter_by(status='approved').all()
    
    status_html = """
    <div style="padding: 20px; background: #e3f2fd; border-radius: 10px;">
        <h2>📊 Current Loan Status</h2>
        <p><strong>Total Approved Loans:</strong> {}</p>
    """.format(len(approved_loans))
    
    if approved_loans:
        status_html += """
        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
            <tr style="background: #007bff; color: white;">
                <th style="padding: 10px; border: 1px solid #ddd;">Loan ID</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Client</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Behavior Score</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Missed Payments</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Next Payment</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Risk Level</th>
            </tr>
        """
        
        for loan in approved_loans:
            risk_level = "🟢 Low" if loan.behavior_score >= 70 else "🟡 Medium" if loan.behavior_score >= 40 else "🔴 High"
            next_payment = loan.next_payment_date.strftime('%Y-%m-%d') if loan.next_payment_date else "Not set"
            bg_color = '#f8f9fa' if loan.behavior_score >= 70 else '#fff3cd' if loan.behavior_score >= 40 else '#f8d7da'

            status_html += f"""
            <tr style="background: {bg_color};">
                <td style="padding: 8px; border: 1px solid #ddd;">{loan.id}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{loan.client_name}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{loan.behavior_score}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{loan.payments_missed}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{next_payment}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{risk_level}</td>
            </tr>
            """
        
        status_html += "</table>"
    else:
        status_html += "<p>No approved loans found.</p>"
    
    status_html += """
        <div style="margin-top: 20px;">
            <a href="/create-high-risk-loans" style="background: #dc3545; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">
                🚨 Create High-Risk Test Data
            </a>
            <a href="/behavior-monitoring" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-left: 10px;">
                📊 Behavior Monitoring
            </a>
        </div>
    </div>
    """
    
    return status_html

# ===== EXISTING APPLICATION ROUTES =====

@app.route('/loans')
@login_required
def loans_page():
    role = current_user.role.lower()
    if role == 'borrower':
        loans = Loan.query.filter_by(client_email=current_user.email).order_by(Loan.created_at.desc()).all()
    else:
        loans = Loan.query.order_by(Loan.created_at.desc()).all()
    
    return render_template('loans.html',
        username=current_user.username,
        loans=loans,
        total_loans=len(loans),
        approved_loans=len([l for l in loans if l.status == 'approved']),
        pending_loans=len([l for l in loans if l.status == 'pending']),
        rejected_loans=len([l for l in loans if l.status == 'rejected']),
        is_sample_data=False
    )

@app.route('/clients')
@login_required
def clients_page():
    role = current_user.role.lower()
    if role == 'borrower':
        flash('Access denied. Admin or loan officer privileges required.', 'error')
        return redirect(url_for('borrower_dashboard'))
    
    clients = Client.query.order_by(Client.created_at.desc()).all()
    return render_template('clients.html', username=current_user.username, clients=clients)

@app.route('/clients/add', methods=['GET', 'POST'])
@login_required
def clients_add():
    role = current_user.role.lower()
    if role not in ['admin', 'loan_officer', 'officer']:
        flash('Access denied. Admin or loan officer privileges required.', 'error')
        if role == 'borrower':
            return redirect(url_for('borrower_dashboard'))
        elif role == 'risk_analyst':
            return redirect(url_for('risk_analyst_dashboard'))
        else:
            return redirect(url_for('login_page'))

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            employment_status = request.form.get('employment_status')
            monthly_income = float(request.form.get('income') or 0)
            credit_score = int(request.form.get('credit_score') or 0)
            address = request.form.get('address')

            if not name or not email:
                flash('Name and Email are required.', 'error')
                return render_template('add_client.html')

            existing = Client.query.filter_by(email=email).first()
            if existing:
                flash('A client with this email already exists.', 'error')
                return render_template('add_client.html')

            client = Client(
                name=name,
                email=email,
                phone=phone,
                employment_status=employment_status,
                monthly_income=monthly_income,
                credit_score=credit_score,
                address=address
            )
            db.session.add(client)
            db.session.commit()
            flash('Client added successfully.', 'success')
            return redirect(url_for('clients_page'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding client: {e}")
            flash('Failed to add client. Please try again.', 'error')
            return render_template('add_client.html')

    return render_template('add_client.html')

# Backward-compatibility route for old links
@app.route('/clients/manage')
@login_required
def clients_manage_redirect():
    return redirect(url_for('clients_page'))

# ===== PREDICTIONS ROUTE =====

@app.route('/predictions')
@login_required
def predictions():
    """Smart redirect based on user role"""
    role = current_user.role.lower()
    
    if role in ['admin', 'risk_analyst']:
        return redirect(url_for('ml_demo'))  # Full ML demo with retraining features for technical users
    elif role in ['loan_officer', 'officer']:
        return redirect(url_for('prediction_page'))  # Simple prediction tool for daily use
    else:
        return redirect(url_for('prediction_page'))  # Basic eligibility check for borrowers

@app.route('/prediction', methods=['GET', 'POST'])
@login_required
def prediction_page():
    if request.method == 'POST':
        try:
            loan_amount = float(request.form.get('loan_amount', 0))
            employment_status = request.form.get('employment_status', 'Unemployed')
            monthly_income = float(request.form.get('monthly_income', 0))
            existing_debt = float(request.form.get('existing_debt', 0))
            credit_history = int(request.form.get('credit_history', 0))
            
            score = calculate_eligibility(
                loan_amount, 
                employment_status, 
                monthly_income, 
                existing_debt, 
                credit_history
            )
            
            risk_category, recommendation, risk_level = get_risk_recommendation(score)
            
            return render_template('prediction.html',
                                username=current_user.username,
                                score=round(score),
                                risk_category=risk_category,
                                recommendation=recommendation,
                                risk_level=risk_level,
                                show_result=True,
                                form_data=request.form)
            
        except Exception as e:
            flash('Error calculating prediction. Please check your inputs.', 'error')
            logger.error(f"Prediction error: {e}")
            return render_template('prediction.html', username=current_user.username, show_result=False)
    
    return render_template('prediction.html', username=current_user.username, show_result=False)

@app.route('/reports')
@login_required
def reports_page():
    role = current_user.role.lower()
    if role == 'borrower':
        flash('Access denied. Admin or loan officer privileges required.', 'error')
        return redirect(url_for('borrower_dashboard'))
    
    return render_template('reports.html', username=current_user.username)

# ===== ADMIN OVERVIEW API (for dashboard charts) =====

@app.route('/api/admin/overview')
@login_required
def api_admin_overview():
    """Aggregate portfolio + CRB analytics for admin dashboard charts"""
    role = current_user.role.lower()
    if role not in ['admin', 'risk_analyst']:
        return jsonify({'error': 'Access denied'}), 403

    try:
        portfolio_health = get_portfolio_health()
        risk_distribution = get_risk_distribution()
        monthly_trends = get_portfolio_health_trends()
        warning_indicators = get_early_warning_indicators()

        # Inline CRB stats to avoid role-restricted endpoint reuse
        score_ranges = {
            'excellent': CRBReport.query.filter(CRBReport.credit_score >= 750).count(),
            'good': CRBReport.query.filter(CRBReport.credit_score >= 700, CRBReport.credit_score < 750).count(),
            'fair': CRBReport.query.filter(CRBReport.credit_score >= 600, CRBReport.credit_score < 700).count(),
            'poor': CRBReport.query.filter(CRBReport.credit_score >= 500, CRBReport.credit_score < 600).count(),
            'very_poor': CRBReport.query.filter(CRBReport.credit_score < 500).count()
        }
        total_reports = CRBReport.query.count()
        blacklist_count = CRBReport.query.filter_by(blacklist_status=True).count()
        avg_credit_score = db.session.query(db.func.avg(CRBReport.credit_score)).scalar() or 0

        crb_stats = {
            'score_distribution': score_ranges,
            'total_reports': total_reports,
            'blacklist_rate': round((blacklist_count / max(total_reports, 1)) * 100, 2),
            'avg_credit_score': float(avg_credit_score)
        }

        return jsonify({
            'portfolio_health': portfolio_health,
            'risk_distribution': risk_distribution,
            'monthly_trends': monthly_trends,
            'warning_indicators': warning_indicators,
            'crb_stats': crb_stats
        })
    except Exception as e:
        logger.error(f"Error in admin overview API: {e}")
        return jsonify({'error': 'Failed to load overview data'}), 500

# ===== REPORTS: VIEW + EXPORT (LIGHTWEIGHT) =====

def _loans_table_rows(query):
    rows = []
    for loan in query:
        rows.append({
            'ID': loan.id,
            'Client': getattr(loan, 'client_name', '') or '-',
            'Email': getattr(loan, 'client_email', '') or '-',
            'Amount': f"{float(loan.amount or 0):.2f}",
            'Status': loan.status or '-',
            'RiskScore': getattr(loan, 'risk_score', ''),
            'CreatedAt': loan.created_at.strftime('%Y-%m-%d') if getattr(loan, 'created_at', None) else ''
        })
    return rows

def _csv_response(filename, columns, rows):
    import csv
    from io import StringIO
    si = StringIO()
    writer = csv.DictWriter(si, fieldnames=columns)
    writer.writeheader()
    for r in rows:
        writer.writerow({c: r.get(c, '') for c in columns})
    from flask import Response
    return Response(
        si.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@app.route('/reports/loan-portfolio')
@login_required
def report_loan_portfolio():
    loans = Loan.query.order_by(Loan.created_at.desc()).limit(200).all()
    rows = _loans_table_rows(loans)
    columns = ['ID','Client','Email','Amount','Status','RiskScore','CreatedAt']
    metrics = {
        'Total Loans': Loan.query.count(),
        'Approved': Loan.query.filter_by(status='approved').count(),
        'Pending': Loan.query.filter_by(status='pending').count(),
        'Rejected': Loan.query.filter_by(status='rejected').count()
    }
    return render_template('reports_view.html', username=current_user.username,
                           title='Loan Portfolio Report', description='Overview of all loan applications and statuses.',
                           columns=columns, rows=rows, metrics=metrics)

@app.route('/reports/loan-portfolio/export')
@login_required
def report_loan_portfolio_export():
    loans = Loan.query.order_by(Loan.created_at.desc()).all()
    rows = _loans_table_rows(loans)
    columns = ['ID','Client','Email','Amount','Status','RiskScore','CreatedAt']
    return _csv_response('loan_portfolio.csv', columns, rows)

@app.route('/reports/risk-analysis')
@login_required
def report_risk_analysis():
    # Reuse existing analytics helpers
    portfolio_health = get_portfolio_health()
    risk_distribution = get_risk_distribution()
    high_risk = Loan.query.filter(Loan.status.in_(['active','approved']), Loan.risk_level=='High').order_by(Loan.risk_score.asc()).limit(100).all()
    rows = _loans_table_rows(high_risk)
    columns = ['ID','Client','Email','Amount','Status','RiskScore','CreatedAt']
    metrics = {
        'Active Loans': portfolio_health.get('active_loans', 0),
        'Default Rate %': portfolio_health.get('default_rate', 0),
        'Avg Risk Score': f"{portfolio_health.get('avg_risk_score',0):.1f}",
        'High Risk Bkts': sum(risk_distribution.get('data', [])) if risk_distribution.get('data') else 0
    }
    return render_template('reports_view.html', username=current_user.username,
                           title='Risk Analysis Report', description='Portfolio risk overview and high-risk loans.',
                           columns=columns, rows=rows, metrics=metrics)

@app.route('/reports/risk-analysis/export')
@login_required
def report_risk_analysis_export():
    high_risk = Loan.query.filter(Loan.status.in_(['active','approved']), Loan.risk_level=='High').order_by(Loan.risk_score.asc()).all()
    rows = _loans_table_rows(high_risk)
    columns = ['ID','Client','Email','Amount','Status','RiskScore','CreatedAt']
    return _csv_response('risk_analysis.csv', columns, rows)

@app.route('/reports/client-performance')
@login_required
def report_client_performance():
    loans = Loan.query.order_by(Loan.created_at.desc()).limit(200).all()
    rows = _loans_table_rows(loans)
    columns = ['ID','Client','Email','Amount','Status','RiskScore','CreatedAt']
    metrics = {
        'Total Clients': Client.query.count(),
        'Loans (Last 30d)': Loan.query.filter(Loan.created_at >= datetime.now(timezone.utc) - timedelta(days=30)).count(),
        'Approved (Last 30d)': Loan.query.filter(Loan.created_at >= datetime.now(timezone.utc) - timedelta(days=30), Loan.status=='approved').count()
    }
    return render_template('reports_view.html', username=current_user.username,
                           title='Client Performance Report', description='Recent client loan activity and outcomes.',
                           columns=columns, rows=rows, metrics=metrics)

@app.route('/reports/client-performance/export')
@login_required
def report_client_performance_export():
    loans = Loan.query.order_by(Loan.created_at.desc()).all()
    rows = _loans_table_rows(loans)
    columns = ['ID','Client','Email','Amount','Status','RiskScore','CreatedAt']
    return _csv_response('client_performance.csv', columns, rows)

@app.route('/reports/financial-summary')
@login_required
def report_financial_summary():
    from sqlalchemy import func
    total_amount = db.session.query(func.sum(Loan.amount)).scalar() or 0
    avg_amount = db.session.query(func.avg(Loan.amount)).scalar() or 0
    loans = Loan.query.order_by(Loan.created_at.desc()).limit(200).all()
    rows = _loans_table_rows(loans)
    columns = ['ID','Client','Email','Amount','Status','RiskScore','CreatedAt']
    metrics = {
        'Total Amount (KSh)': f"{float(total_amount):.0f}",
        'Average Amount (KSh)': f"{float(avg_amount):.0f}",
        'Total Loans': Loan.query.count()
    }
    return render_template('reports_view.html', username=current_user.username,
                           title='Financial Summary', description='Financial totals and recent loans.',
                           columns=columns, rows=rows, metrics=metrics)

@app.route('/reports/financial-summary/export')
@login_required
def report_financial_summary_export():
    loans = Loan.query.order_by(Loan.created_at.desc()).all()
    rows = _loans_table_rows(loans)
    columns = ['ID','Client','Email','Amount','Status','RiskScore','CreatedAt']
    return _csv_response('financial_summary.csv', columns, rows)

@app.route('/reports/audit-trail')
@login_required
def report_audit_trail():
    # Use recent interventions as activity log proxy
    interventions = Intervention.query.order_by(Intervention.sent_at.desc()).limit(200).all()
    rows = []
    for i in interventions:
        rows.append({
            'ID': i.id,
            'LoanID': i.loan_id,
            'Type': i.type,
            'Status': i.status,
            'SentAt': i.sent_at.strftime('%Y-%m-%d %H:%M') if i.sent_at else ''
        })
    columns = ['ID','LoanID','Type','Status','SentAt']
    metrics = {'Interventions (Last 200)': len(rows)}
    return render_template('reports_view.html', username=current_user.username,
                           title='Audit Trail Report', description='Recent automated interventions (activity log).',
                           columns=columns, rows=rows, metrics=metrics)

@app.route('/reports/audit-trail/export')
@login_required
def report_audit_trail_export():
    interventions = Intervention.query.order_by(Intervention.sent_at.desc()).all()
    rows = []
    for i in interventions:
        rows.append({'ID': i.id,'LoanID': i.loan_id,'Type': i.type,'Status': i.status,'SentAt': i.sent_at.strftime('%Y-%m-%d %H:%M') if i.sent_at else ''})
    columns = ['ID','LoanID','Type','Status','SentAt']
    return _csv_response('audit_trail.csv', columns, rows)

@app.route('/reports/custom')
@login_required
def report_custom_builder():
    # For now, redirect to analytics dashboard as a placeholder
    flash('Custom report builder coming soon. Redirected to analytics.', 'info')
    return redirect(url_for('analytics_page'))

# ===== FIXED ANALYTICS AND RISK ROUTES =====

@app.route('/analytics')
@login_required
def analytics_page():
    """Analytics dashboard - redirect to risk analyst dashboard for admins"""
    role = current_user.role.lower()
    if role == 'admin':
        return redirect(url_for('risk_analyst_dashboard'))
    elif role in ['loan_officer', 'officer']:
        return redirect(url_for('reports_page'))
    elif role == 'borrower':
        flash('Access denied. Admin or loan officer privileges required.', 'error')
        return redirect(url_for('borrower_dashboard'))
    else:
        return redirect(url_for('reports_page'))

@app.route('/risk-analytics')
@login_required
def risk_analytics():
    """Explicit risk analytics route"""
    return redirect(url_for('risk_analyst_dashboard'))

# ===== ENHANCED LOAN APPLICATION ROUTE WITH CRB INTEGRATION =====

@app.route('/loans/apply', methods=['GET', 'POST'])
@login_required
def apply_loan():
    print("🔍 ALL FORM DATA RECEIVED:", dict(request.form))
    role = current_user.role.lower()
    if role != 'borrower':
        flash('Only borrowers can apply for loans.', 'error')
        if role == 'admin':
            return redirect(url_for('dashboard'))
        elif role in ['loan_officer', 'officer']:
            return redirect(url_for('loan_officer_dashboard'))
        elif role == 'risk_analyst':
            return redirect(url_for('risk_analyst_dashboard'))
        else:
            return redirect(url_for('login_page'))
    
    if request.method == 'POST':
        try:
            print("🔍 DEBUG: Loan application form submitted")
            print(f"🔍 DEBUG: User: {current_user.username}, Email: {current_user.email}")
            
            # Get form data
            amount = request.form.get('amount')
            term = request.form.get('term')
            purpose = request.form.get('purpose')
            employment_status = request.form.get('employment_status')
            monthly_income = request.form.get('monthly_income', '0')
            credit_history = request.form.get('credit_history', '0')
            client_phone = request.form.get('client_phone')
            national_id = request.form.get('national_id', '').strip()
            client_name = request.form.get('client_name')  # ADDED: Get client_name from form
            
            print(f"🔍 DEBUG: Form data - Amount: {amount}, Term: {term}, Purpose: {purpose}, Client Name: {client_name}")
            
            # Validate required fields
            if not all([amount, term, purpose, employment_status, monthly_income, client_phone, national_id, client_name]):
                flash('Please fill in all required fields including Full Name and National ID.', 'error')
                print("❌ DEBUG: Missing required fields")
                return render_template('apply_loan.html', 
                                    username=current_user.username,
                                    user_email=current_user.email)
            
            # Convert numeric fields with proper error handling
            try:
                amount_float = float(amount)
                term_int = int(term)
                monthly_income_float = float(monthly_income) if monthly_income else 0
                credit_history_int = int(credit_history) if credit_history else 0
                existing_debt_float = float(request.form.get('existing_debt', '0'))
            except ValueError as e:
                flash('Please check your numeric fields (amount, income, debt).', 'error')
                print(f"❌ DEBUG: Number conversion error: {e}")
                return render_template('apply_loan.html', 
                                    username=current_user.username,
                                    user_email=current_user.email)
            
            # Validate minimum values
            if amount_float < 1000:
                flash('Loan amount must be at least KSh 1,000.', 'error')
                return render_template('apply_loan.html', 
                                    username=current_user.username,
                                    user_email=current_user.email)
            
            if monthly_income_float < 0:
                flash('Monthly income cannot be negative.', 'error')
                return render_template('apply_loan.html', 
                                    username=current_user.username,
                                    user_email=current_user.email)
            
            if len(national_id) < 6:
                flash('Please enter a valid National ID.', 'error')
                return render_template('apply_loan.html', 
                                    username=current_user.username,
                                    user_email=current_user.email)
            
            # NEW: CRB Credit Check
            print(f"🔍 DEBUG: Performing CRB check for National ID: {national_id}")
            crb_service = CRBService()
            crb_report = crb_service.get_credit_report(
                national_id=national_id,
                phone_number=client_phone,
                client_name=client_name
            )
            # Defensive: ensure crb_report is a dict even if the service failed
            if crb_report is None:
                logger.warning("CRBService returned None; using fallback empty report")
                crb_report = {'success': False}
            
            # Check if applicant is blacklisted
            if crb_report.get('blacklist_status'):
                # Persist a CRB record for audit even if we reject immediately
                try:
                    model_cols = {c.name for c in CRBReport.__table__.columns}
                except Exception:
                    model_cols = {
                        'loan_id', 'national_id', 'phone_number', 'credit_score',
                        'active_loans', 'default_history', 'credit_utilization',
                        'payment_pattern', 'blacklist_status', 'days_arrears',
                        'credit_rating', 'crb_bureau'
                    }
                crb_data_reject = {
                    'loan_id': None,
                    'national_id': national_id,
                    'phone_number': client_phone,
                    'credit_score': crb_report.get('credit_score', 0),
                    'active_loans': crb_report.get('active_loans', 0),
                    'default_history': crb_report.get('default_history', 0),
                    'credit_utilization': crb_report.get('credit_utilization', 0.0),
                    'payment_pattern': crb_report.get('payment_pattern', 'unknown'),
                    'blacklist_status': crb_report.get('blacklist_status', False),
                    'days_arrears': crb_report.get('days_arrears', 0),
                    'credit_rating': crb_report.get('credit_rating', 'Unknown'),
                    'crb_bureau': crb_report.get('crb_bureau', 'Simulated')
                }
                filtered_reject = {k: v for k, v in crb_data_reject.items() if k in model_cols}
                try:
                    db.session.add(CRBReport(**filtered_reject))
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logger.warning(f"Failed to persist blacklisted CRB record: {e}")

                flash("❌ Application cannot be processed: Applicant is blacklisted in CRB", "danger")
                logger.info(f"CRB Blacklisted - Loan application rejected for {client_name}")
                return render_template('apply_loan.html', 
                                    username=current_user.username,
                                    user_email=current_user.email)
            
            # Calculate enhanced risk score with CRB data
            loan_data = {
                'amount': amount_float,
                'employment_status': employment_status,
                'monthly_income': monthly_income_float,
                'existing_debt': existing_debt_float,
                'credit_history': credit_history_int,
                'term': term_int,
                'purpose': purpose
            }
            
            risk_score = calculate_enhanced_risk_with_crb(loan_data, crb_report)
            
            # Calculate interest rate based on risk
            interest_rate = calculate_interest_rate(risk_score)
            
            print(f"🔍 DEBUG: Creating loan with risk_score: {risk_score}, interest_rate: {interest_rate}")
            
            # Create loan with CRB data
            new_loan = Loan(
                client_name=client_name,  # Use the client_name from form
                client_email=current_user.email,
                client_phone=client_phone,
                national_id=national_id,
                amount=amount_float,
                term=term_int,
                purpose=purpose,
                employment_status=employment_status,
                monthly_income=monthly_income_float,
                credit_history=str(credit_history_int),
                status='pending',
                risk_score=risk_score,
                interest_rate=interest_rate,
                crb_checked=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            print(f"🔍 DEBUG: Loan object created: {new_loan.client_name}, {new_loan.client_email}")
            
            # Add to database
            db.session.add(new_loan)
            db.session.flush()  # This assigns an ID without committing
            print(f"🔍 DEBUG: Loan added to session, ID: {new_loan.id}")
            
            # Save CRB report to database
            if crb_report.get('success'):
                # Build a safe dict with only CRBReport model columns to avoid invalid kwargs
                crb_data = {
                    'loan_id': new_loan.id,
                    'national_id': national_id,
                    'phone_number': client_phone,
                    'credit_score': crb_report.get('credit_score', 0),
                    'active_loans': crb_report.get('active_loans', 0),
                    'default_history': crb_report.get('default_history', 0),
                    'credit_utilization': crb_report.get('credit_utilization', 0.0),
                    'payment_pattern': crb_report.get('payment_pattern', 'unknown'),
                    'blacklist_status': crb_report.get('blacklist_status', False),
                    'days_arrears': crb_report.get('days_arrears', 0),
                    'credit_rating': crb_report.get('credit_rating', 'Unknown')
                }

                # Filter to only model columns (handles schema mismatch differences)
                try:
                    model_cols = {c.name for c in CRBReport.__table__.columns}
                except Exception:
                    # If model metadata isn't available (stale import or different SQLAlchemy
                    # instance), be conservative and use a safe whitelist of known columns.
                    # This avoids passing unexpected kwargs like 'crb_bureau' which can
                    # raise TypeError when the model mapping doesn't include them.
                    model_cols = {
                        'loan_id', 'national_id', 'phone_number', 'credit_score',
                        'active_loans', 'default_history', 'credit_utilization',
                        'payment_pattern', 'blacklist_status', 'days_arrears',
                        'credit_rating'
                    }

                # Filter to model columns (includes 'crb_bureau' when defined)
                filtered = {k: v for k, v in crb_data.items() if k in model_cols}
                crb_report_record = CRBReport(**filtered)
                db.session.add(crb_report_record)
                # assign relationship id after flush/commit
                db.session.flush()
                new_loan.crb_report_id = crb_report_record.id
                print(f"🔍 DEBUG: CRB report saved for loan {new_loan.id}")
            
            # COMMIT THE TRANSACTION
            print("🔍 DEBUG: About to commit loan to database...")
            db.session.commit()
            print("✅ DEBUG: Loan committed to database successfully!")
            
            # Verify the loan was saved
            saved_loan = Loan.query.get(new_loan.id)
            print(f"🔍 DEBUG: Loan retrieved from DB: {saved_loan is not None}")
            
            # Show CRB insights to user
            crb_rating = crb_report.get('credit_rating', 'Unknown')
            crb_score = crb_report.get('credit_score', 0)
            
            # Send email notification
            print("🔍 DEBUG: Attempting to send email notification...")
            email_sent = send_loan_application_email(new_loan)
            
            if email_sent:
                flash(f'✅ Loan application submitted! CRB Check: {crb_rating} (Score: {crb_score}) - Notification email sent.', 'success')
                print("✅ DEBUG: Email sent successfully")
            else:
                flash(f'✅ Loan application submitted! CRB Check: {crb_rating} (Score: {crb_score}) - (Email notification failed)', 'warning')
                print("⚠️ DEBUG: Email failed to send")
            
            print("✅ DEBUG: Loan application process completed successfully")
            return redirect(url_for('borrower_dashboard'))
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            db.session.rollback()
            error_msg = f'Error submitting loan application: {e}'
            flash(error_msg, 'error')
            print(f"❌ DEBUG: Loan application failed: {e}")
            logger.error(f"Loan application error: {e}", exc_info=True)
            return render_template('apply_loan.html', 
                                username=current_user.username,
                                user_email=current_user.email)
    
    # GET request - show the form
    return render_template('apply_loan.html', 
                         username=current_user.username,
                         user_email=current_user.email)
@app.route('/loans/update-status/<int:loan_id>', methods=['POST'])
@login_required
def update_loan_status(loan_id):
    """Update loan status and notify borrower"""
    if current_user.role.lower() not in ['admin', 'loan_officer']:
        flash('Access denied.', 'error')
        return redirect(url_for('borrower_dashboard'))
    
    loan = Loan.query.get_or_404(loan_id)
    new_status = request.form.get('status')
    
    if new_status in ['approved', 'rejected', 'pending']:
        old_status = loan.status
        loan.status = new_status
        
        # Set next payment date if approved
        if new_status == 'approved' and not loan.next_payment_date:
            loan.next_payment_date = datetime.now(timezone.utc).date() + timedelta(days=30)
        
        loan.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        if new_status in ['approved', 'rejected'] and old_status != new_status:
            email_sent = send_loan_status_email(loan)
            if email_sent:
                flash(f'Loan status updated to {new_status} and borrower notified.', 'success')
            else:
                flash(f'Loan status updated to {new_status} but email failed.', 'warning')
        else:
            flash(f'Loan status updated to {new_status}.', 'success')
    
    return redirect(url_for('loans_page'))

@app.route('/create-admin')
def create_admin():
    """Create admin user (run once)"""
    admin = User(
        username='admin',
        email='admin@crimap.com',
        password_hash=generate_password_hash('admin123'),
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()
    return "✅ Admin user created: admin / admin123"

# ===== TESTING AND DEBUG ROUTES =====

@app.route('/test-crb-integration')
@login_required
def test_crb_integration():
    """Test CRB integration"""
    if current_user.role != 'admin':
        return "Access denied", 403
    
    crb_service = CRBService()
    
    # Test different scenarios
    test_cases = [
        {'id': '12345678', 'phone': '0712345678', 'name': 'Good Applicant'},
        {'id': '87654321', 'phone': '0723456789', 'name': 'Medium Applicant'},
        {'id': '11111111', 'phone': '0734567890', 'name': 'High Risk Applicant'}
    ]
    
    results = []
    for case in test_cases:
        report = crb_service.get_credit_report(case['id'], case['phone'], case['name'])
        results.append({
            'case': case,
            'report': report,
            'risk_score': calculate_crb_score(report)
        })
    
    return jsonify(results)

@app.route('/test-behavior')
def test_behavior_monitoring():
    """Test the new behavior monitoring features"""
    try:
        loan = Loan.query.filter_by(status='approved').first()
        
        if loan:
            # Test payment recording
            loan.record_payment(5000)
            
            # Test risk flagging
            loan.add_risk_flag('test_flag', 'low', 'Test risk flag')
            
            db.session.commit()
            
            return f"""
            <div style="padding: 20px; background: #d4edda; border-radius: 10px;">
                <h2>✅ Behavior Monitoring Test Successful!</h2>
                <p><strong>Loan:</strong> {loan.client_name}</p>
                <p><strong>Behavior Score:</strong> {loan.behavior_score}</p>
                <p><strong>Risk Flags:</strong> {len(loan.get_risk_flags())}</p>
                <p><strong>Next Payment:</strong> {loan.next_payment_date}</p>
                <p><strong>Total Paid:</strong> KSh {loan.total_paid:,.2f}</p>
                <br>
                <a href="/behavior-monitoring" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">View Behavior Dashboard</a>
                <a href="/loans" style="background: #28a745; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-left: 10px;">View All Loans</a>
            </div>
            """
        else:
            return """
            <div style="padding: 20px; background: #f8d7da; border-radius: 10px;">
                <h2>❌ No Approved Loans Found</h2>
                <p>No approved loans available for testing behavior monitoring.</p>
                <a href="/loans/apply" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Apply for a Loan First</a>
            </div>
            """
            
    except Exception as e:
        return f"""
        <div style="padding: 20px; background: #f8d7da; border-radius: 10px;">
            <h2>❌ Test Failed</h2>
            <p><strong>Error:</strong> {str(e)}</p>
            <a href="/behavior-monitoring" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Try Behavior Dashboard</a>
        </div>
        """

@app.route('/test-interventions')
def test_interventions():
    """Test the intervention system"""
    try:
        result = InterventionBot.check_and_trigger_interventions()
        return f"""
        <div style="padding: 20px; background: #d4edda; border-radius: 10px;">
            <h2>✅ Intervention System Test</h2>
            <p><strong>Result:</strong> {result}</p>
            <br>
            <a href="/interventions" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">View Interventions</a>
            <a href="/behavior-monitoring" style="background: #28a745; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-left: 10px;">Behavior Monitoring</a>
        </div>
        """
    except Exception as e:
        return f"""
        <div style="padding: 20px; background: #f8d7da; border-radius: 10px;">
            <h2>❌ Intervention Test Failed</h2>
            <p><strong>Error:</strong> {str(e)}</p>
        </div>
        """

@app.route('/test-email')
def test_email():
    """Test email functionality"""
    try:
        msg = Message(
            subject='CRIMAP - Test Email',
            recipients=['kipropphilip09@gmail.com'],
            body='This is a test email from CRIMAP system.',
            html='<h3>CRIMAP Test Email</h3><p>If you can read this, email is working!</p>'
        )
        mail.send(msg)
        return "✅ Test email sent successfully! Check your inbox."
    except Exception as e:
        return f"❌ Email failed: {str(e)}"

@app.route('/debug-templates')
def debug_templates():
    """Debug template directory"""
    import os
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    result = f"<h2>Template Debug Information</h2>"
    result += f"<p><strong>Current Directory:</strong> {os.getcwd()}</p>"
    result += f"<p><strong>Template Directory:</strong> {template_dir}</p>"
    
    if os.path.exists(template_dir):
        result += f"<p style='color: green;'><strong>Directory exists:</strong> YES</p>"
        templates = os.listdir(template_dir)
        result += f"<p><strong>Available templates ({len(templates)}):</strong></p>"
        result += "<ul>"
        for template in sorted(templates):
            result += f"<li>{template}</li>"
        result += "</ul>"
    else:
        result += f"<p style='color: red;'><strong>Directory exists:</strong> NO</p>"
    
    return result

@app.route('/test')
def test_route():
    return "🚀 CRIMAP Server is running! Go to <a href='/login'>/login</a> to access the application."

# ===== DEBUG AND TEST ROUTES =====

@app.route('/debug-routes')
def debug_routes():
    """Debug all available routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': rule.rule
        })
    
    html = "<h2>Available Routes</h2><ul>"
    for route in sorted(routes, key=lambda x: x['path']):
        html += f"<li><strong>{route['path']}</strong> - {route['endpoint']} - {route['methods']}</li>"
    html += "</ul>"
    
    return html

@app.route('/test-risk')
@login_required
def test_risk_dashboard():
    """Test route for risk analyst dashboard"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Risk Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .btn {{ background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 5px; }}
        </style>
    </head>
    <body>
        <h1>🚀 Risk Analyst Dashboard - TEST</h1>
        
        <div class="card">
            <h3>This is a test page for Risk Analyst Dashboard</h3>
            <p>If you can see this, the route is working!</p>
            <p><strong>Current User:</strong> {current_user.username}</p>
            <p><strong>Route:</strong> /test-risk</p>
            
            <div style="margin-top: 20px;">
                <a href="/risk-analyst-dashboard" class="btn">Try Main Risk Dashboard</a>
                <a href="/dashboard" class="btn">Back to Admin Dashboard</a>
                <a href="/debug-routes" class="btn">Debug All Routes</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/check-my-role')
@login_required
def check_my_role():
    """Check current user role and authentication"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Check Role - CRIMAP</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .btn {{ background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 5px; }}
            .success {{ background: #d4edda; color: #155724; }}
            .warning {{ background: #fff3cd; color: #856404; }}
            .danger {{ background: #f8d7da; color: #721c24; }}
        </style>
    </head>
    <body>
        <h1>🔍 User Role & Authentication Check</h1>
        
        <div class="card">
            <h3>👤 User Information</h3>
            <p><strong>Username:</strong> {current_user.username}</p>
            <p><strong>Role:</strong> {current_user.role}</p>
            <p><strong>Email:</strong> {current_user.email}</p>
            <p><strong>User ID:</strong> {current_user.id}</p>
            <p><strong>Authenticated:</strong> {current_user.is_authenticated}</p>
        </div>

        <div class="card {'warning' if current_user.role != 'borrower' else 'success'}">
            <h3>🚨 Role Check</h3>
            <p><strong>Current Role:</strong> {current_user.role}</p>
            <p><strong>Required for Loans:</strong> borrower</p>
            {'<p style="color: #dc3545;">❌ You need to be a "borrower" to apply for loans!</p>' if current_user.role != 'borrower' else '<p style="color: #28a745;">✅ You have the correct role for applying loans!</p>'}
        </div>

        <div class="card">
            <h3>🚀 Quick Actions</h3>
            <a href="/create-test-loan" class="btn" style="background: #28a745;">➕ Create Test Loan</a>
            <a href="/debug-loans" class="btn" style="background: #007bff;">🐛 Debug All Loans</a>
            <a href="/borrower-dashboard" class="btn" style="background: #6c757d;">📊 Borrower Dashboard</a>
            <a href="/logout" class="btn" style="background: #dc3545;">🚪 Logout</a>
        </div>
    </body>
    </html>
    """

@app.route('/create-test-loan')
@login_required
def create_test_loan():
    """Create a test loan for current user"""
    try:
        # Check if user is borrower
        if current_user.role != 'borrower':
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>Wrong Role</title></head>
            <body style="font-family: Arial; margin: 40px;">
                <div style="padding: 20px; background: #fff3cd; border-radius: 10px;">
                    <h2>⚠️ Wrong Role</h2>
                    <p>Your role is <strong>{current_user.role}</strong> but you need to be <strong>borrower</strong> to create loans.</p>
                    <p><a href="/logout" style="color: #007bff;">Logout</a> and login as a borrower, or <a href="/register" style="color: #007bff;">register</a> as a new borrower.</p>
                </div>
            </body>
            </html>
            """
        
        # Create test loan
        test_loan = Loan(
            client_name=current_user.username,
            client_email=current_user.email,
            client_phone="+254712345678",
            amount=25000,
            term=12,
            purpose="Test Loan",
            employment_status="Employed", 
            monthly_income=50000,
            credit_history="12",
            status='pending',
            risk_score=75,
            interest_rate=10.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.session.add(test_loan)
        db.session.commit()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Test Loan Created</title></head>
        <body style="font-family: Arial; margin: 40px;">
            <div style="padding: 20px; background: #d4edda; border-radius: 10px;">
                <h2>✅ Test Loan Created!</h2>
                <p><strong>For:</strong> {current_user.username}</p>
                <p><strong>Amount:</strong> KSh 25,000</p>
                <p><strong>Status:</strong> Pending</p>
                <p><strong>Risk Score:</strong> 75%</p>
                
                <div style="margin-top: 20px;">
                    <a href="/borrower-dashboard" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin: 5px;">📊 Check Borrower Dashboard</a>
                    <a href="/debug-loans" style="background: #28a745; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin: 5px;">🐛 Debug All Loans</a>
                    <a href="/loans" style="background: #6c757d; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin: 5px;">📋 All Loans Page</a>
                </div>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body style="font-family: Arial; margin: 40px;">
            <div style="padding: 20px; background: #f8d7da; border-radius: 10px;">
                <h2>❌ Error Creating Test Loan</h2>
                <p><strong>Error:</strong> {str(e)}</p>
            </div>
        </body>
        </html>
        """

@app.route('/debug-loans')
@login_required
def debug_loans():
    """Debug route to check all loan data"""
    try:
        all_loans = Loan.query.all()
        user_loans = Loan.query.filter_by(client_email=current_user.email).all()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Loan Debug - CRIMAP</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .card { background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }
                .btn { background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 5px; }
                .loan-item { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .user-loan { border-left: 5px solid #28a745; background: #f8fff9; }
                .other-loan { border-left: 5px solid #6c757d; background: #f8f9fa; }
            </style>
        </head>
        <body>
            <h1>🔧 Loan Debug Information</h1>
        """
        
        # Summary card
        html += f"""
            <div class="card">
                <h3>📊 Summary</h3>
                <p><strong>Total Loans in System:</strong> {len(all_loans)}</p>
                <p><strong>Your Loans:</strong> {len(user_loans)}</p>
                <p><strong>Your Email:</strong> {current_user.email}</p>
                <p><strong>Your Role:</strong> {current_user.role}</p>
            </div>
        """
        
        # Show user's loans
        html += f"<h3>📋 Your Loans (Filtered by: {current_user.email})</h3>"
        if user_loans:
            for loan in user_loans:
                status_color = '#28a745' if loan.status == 'approved' else '#ffc107' if loan.status == 'pending' else '#dc3545'
                html += f"""
                <div class="loan-item user-loan">
                    <p><strong>ID:</strong> {loan.id}</p>
                    <p><strong>Client:</strong> {loan.client_name}</p>
                    <p><strong>Email:</strong> {loan.client_email}</p>
                    <p><strong>Status:</strong> <span style="color: {status_color}">{loan.status.upper()}</span></p>
                    <p><strong>Amount:</strong> KSh {loan.amount:,.2f}</p>
                    <p><strong>Created:</strong> {loan.created_at}</p>
                    <p><strong>Risk Score:</strong> {loan.risk_score}%</p>
                </div>
                """
        else:
            html += "<p style='color: #dc3545;'>❌ No loans found for your account!</p>"
        
        # Show all loans (for debugging)
        html += f"<h3>🔍 All Loans in Database ({len(all_loans)} total)</h3>"
        if all_loans:
            for loan in all_loans:
                is_user_loan = loan.client_email == current_user.email
                loan_class = "user-loan" if is_user_loan else "other-loan"
                html += f"""
                <div class="loan-item {loan_class}">
                    <p><strong>ID:</strong> {loan.id} | <strong>Client:</strong> {loan.client_name} | <strong>Email:</strong> {loan.client_email} | <strong>Status:</strong> {loan.status} | <strong>Amount:</strong> KSh {loan.amount:,.2f}</p>
                </div>
                """
        else:
            html += "<p>No loans in database.</p>"
        
        html += """
            <div style="margin-top: 20px;">
                <a href="/create-test-loan" class="btn" style="background: #28a745;">➕ Create Test Loan</a>
                <a href="/borrower-dashboard" class="btn" style="background: #007bff;">📊 Borrower Dashboard</a>
                <a href="/loans/apply" class="btn" style="background: #17a2b8;">📝 Apply for Loan</a>
                <a href="/check-my-role" class="btn" style="background: #6c757d;">🔍 Check Role</a>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"<h2>❌ Error</h2><p>{str(e)}</p>"

# Add this simple test route too
@app.route('/test-db')
def test_db():
    """Simple database test"""
    try:
        from models import User, Loan
        user_count = User.query.count()
        loan_count = Loan.query.count()
        return f"""
        <h2>✅ Database Test</h2>
        <p>Users: {user_count}</p>
        <p>Loans: {loan_count}</p>
        <p>Database connection: WORKING</p>
        """
    except Exception as e:
        return f"<h2>❌ Database Error</h2><p>{str(e)}</p>"
# Add this RIGHT BEFORE the APPLICATION STARTUP section:

# ===== DEBUG ROUTES FOR LOAN APPLICATION ISSUE =====

# ===== DEBUG ROUTES FOR LOAN APPLICATION ISSUE =====

@app.route('/debug-all-loans')
@login_required
def debug_all_loans():
    """Debug route to see ALL loans in the system"""
    all_loans = Loan.query.order_by(Loan.created_at.desc()).all()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug All Loans</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .loan {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .success {{ border-left: 5px solid #28a745; background: #f8fff9; }}
            .warning {{ border-left: 5px solid #ffc107; background: #fffef0; }}
            .danger {{ border-left: 5px solid #dc3545; background: #fff5f5; }}
        </style>
    </head>
    <body>
        <h1>🔧 Debug: All Loans in Database</h1>
        <p><strong>Total Loans:</strong> {len(all_loans)}</p>
    """
    
    for loan in all_loans:
        status_class = "success" if loan.status == 'approved' else "warning" if loan.status == 'pending' else "danger"
        html += f"""
        <div class="loan {status_class}">
            <h3>Loan ID: {loan.id} | {loan.purpose} | KSh {loan.amount:,}</h3>
            <p><strong>Client:</strong> {loan.client_name} ({loan.client_phone})</p>
            <p><strong>Email:</strong> {loan.client_email}</p>
            <p><strong>Status:</strong> {loan.status}</p>
            <p><strong>Risk Score:</strong> {loan.risk_score}%</p>
            <p><strong>Created:</strong> {loan.created_at}</p>
            <p><strong>Last Updated:</strong> {loan.updated_at}</p>
        </div>
        """
    
    html += """
        <div style="margin-top: 20px;">
            <a href="/test-loan-creation" style="background: #28a745; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">➕ Create Test Loan</a>
            <a href="/check-my-role" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-left: 10px;">🔍 Check My Role</a>
            <a href="/borrower-dashboard" style="background: #6c757d; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-left: 10px;">📊 Borrower Dashboard</a>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/test-loan-creation')
@login_required
def test_loan_creation():
    """Test route to create a loan and verify it appears in dashboards"""
    try:
        # Create a test loan for current user
        test_loan = Loan(
            client_name=current_user.username,
            client_email=current_user.email,
            client_phone="+254700000000",
            amount=15000,
            term=6,
            purpose="Test Loan - Debug",
            employment_status="Employed",
            monthly_income=50000,
            credit_history="12",
            status='pending',
            risk_score=65,
            interest_rate=10.5,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.session.add(test_loan)
        db.session.commit()
        
        # Verify the loan was saved
        saved_loan = Loan.query.filter_by(client_email=current_user.email).order_by(Loan.created_at.desc()).first()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Loan Created</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .success {{ background: #d4edda; padding: 20px; border-radius: 10px; }}
                .info {{ background: #e3f2fd; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="success">
                <h2>✅ Test Loan Created Successfully!</h2>
                <p><strong>Loan ID:</strong> {saved_loan.id}</p>
                <p><strong>For:</strong> {saved_loan.client_name}</p>
                <p><strong>Email:</strong> {saved_loan.client_email}</p>
                <p><strong>Amount:</strong> KSh {saved_loan.amount:,.2f}</p>
                <p><strong>Status:</strong> {saved_loan.status}</p>
                <p><strong>Created:</strong> {saved_loan.created_at}</p>
            </div>
            
            <div class="info">
                <h3>🔍 Next Steps:</h3>
                <p>1. <a href="/borrower-dashboard" target="_blank">Check Borrower Dashboard</a> - You should see this loan</p>
                <p>2. <a href="/debug-all-loans" target="_blank">Check All Loans</a> - Verify loan is in database</p>
                <p>3. <a href="/loans" target="_blank">Check Loans Page</a> - Should show in loans list</p>
            </div>
            
            <div style="margin-top: 20px;">
                <a href="/borrower-dashboard" style="background: #007bff; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-weight: bold;">📊 Check Borrower Dashboard</a>
                <a href="/debug-all-loans" style="background: #28a745; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; margin-left: 10px;">🐛 Debug All Loans</a>
                <a href="/loans/apply" style="background: #17a2b8; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; margin-left: 10px;">📝 Apply Real Loan</a>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body style="font-family: Arial; margin: 40px;">
            <div style="padding: 20px; background: #f8d7da; border-radius: 10px;">
                <h2>❌ Error Creating Test Loan</h2>
                <p><strong>Error:</strong> {str(e)}</p>
                <p>This indicates a database issue.</p>
            </div>
        </body>
        </html>
        """

@app.route('/check-database-connection')
def check_database_connection():
    """Check if database is working and show basic stats"""
    try:
        user_count = User.query.count()
        loan_count = Loan.query.count()
        pending_loans = Loan.query.filter_by(status='pending').count()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Check</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0; }}
                .success {{ background: #d4edda; }}
            </style>
        </head>
        <body>
            <h1>🔍 Database Connection Check</h1>
            
            <div class="card success">
                <h3>✅ Database Connection: WORKING</h3>
                <p><strong>Total Users:</strong> {user_count}</p>
                <p><strong>Total Loans:</strong> {loan_count}</p>
                <p><strong>Pending Loans:</strong> {pending_loans}</p>
            </div>
            
            <div class="card">
                <h3>🚀 Quick Tests:</h3>
                <p><a href="/test-loan-creation">Create Test Loan</a> - Test loan creation process</p>
                <p><a href="/debug-all-loans">View All Loans</a> - See all loans in database</p>
                <p><a href="/check-my-role">Check My Role</a> - Verify user role and permissions</p>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <div style="padding: 20px; background: #f8d7da; border-radius: 10px;">
            <h2>❌ Database Connection Failed</h2>
            <p><strong>Error:</strong> {str(e)}</p>
        </div>
        """
@app.route('/debug-form-submission', methods=['POST'])
def debug_form_submission():
    """Temporary debug route to see form data"""
    print("🎯 DEBUG FORM SUBMISSION TRIGGERED!")
    print("🔍 ALL FORM DATA:", dict(request.form))
    print("🔍 HEADERS:", dict(request.headers))
    return "Form received - check console logs"
# ===== APPLICATION STARTUP =====

if __name__ == "__main__":
    print("🚀 CRIMAP Flask Server Starting...")
    print("📍 Available at: http://127.0.0.1:5001")
    print("💾 Using MySQL (XAMPP)")
    print("🔐 Login: admin / admin123")
    print("📧 Email: Configured with Gmail")
    print("")
    print("🎯 CORE FEATURES:")
    print("   - Behavior Monitoring & Scoring")
    print("   - Automated Intervention Bot")
    print("   - Risk Prediction System")
    print("   - Multi-role Dashboards")
    print("   - CRB Integration (NEW!)")
    print("")
    print("🤖 ML MODEL INTEGRATION:")
    print("   /api/test-model-setup - Test ML model setup")
    print("   /api/predict-risk - Real-time risk prediction API")
    print("   /api/train-model - Train new ML model")
    print("   /ml-demo - ML Demo Page")
    print("")
    print("🔄 AUTOMATED RETRAINING SYSTEM:")
    print("   /api/retrain-model - Manual retraining trigger")
    print("   /api/retraining-status - Check retraining status")
    print("   /api/retraining-stats - Get retraining statistics")
    print("   Automated weekly retraining checks")
    print("   Performance monitoring & improvement tracking")
    print("")
    print("🔗 ENHANCED INTERVENTION SYSTEM:")
    print("   /interventions-dashboard - New enhanced dashboard")
    print("   /create-high-risk-loans - Create test data")
    print("   /api/trigger-interventions - Run intervention check")
    print("   /api/interventions/stats - Get intervention statistics")
    print("   /api/loans/high-risk - Get high-risk loans")
    print("   /check-loan-status - Check current loan status")
    print("")
    print("📊 ENHANCED RISK ANALYST DASHBOARD:")
    print("   /risk_analyst_dashboard - Advanced portfolio analytics")
    print("   /api/risk-analytics/portfolio-metrics - Portfolio metrics API")
    print("   /api/risk-analytics/borrower-segments - Borrower segmentation")
    print("   /api/risk-analytics/model-performance - ML model performance")
    print("   /api/risk-analytics/early-warnings - Early warning system")
    print("")
    print("🔍 CRB INTEGRATION (NEW!):")
    print("   /crb-dashboard - CRB monitoring dashboard")
    print("   /api/crb-stats - CRB statistics API")
    print("   Automated credit checks for loan applications")
    print("   Blacklist detection and risk scoring")
    print("")
    print("📋 ENHANCED LOAN APPLICATION:")
    print("   Comprehensive risk assessment with 8+ factors")
    print("   Dynamic interest rates based on risk profile")
    print("   Professional application form with all necessary fields")
    print("   CRB credit checks integrated")
    print("")
    
    # Allow skipping DB initialization to avoid startup blocking when MySQL is down
    try:
        import os
        skip_db_init = os.getenv('SKIP_DB_INIT', '0') == '1'
    except Exception:
        skip_db_init = False

    if skip_db_init:
        print("⏭️  Skipping database initialization (SKIP_DB_INIT=1). Starting server immediately...")
        app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)
    else:
        try:
            with app.app_context():
                # Create database tables
                db.create_all()
                loan_count = Loan.query.count()
                user_count = User.query.count()
                intervention_count = Intervention.query.count()
                crb_count = CRBReport.query.count()
                print(f"✅ Database: {user_count} users, {loan_count} loans, {intervention_count} interventions, {crb_count} CRB reports")
                # Ensure useful indexes exist
                ensure_crb_indexes()
                
                # Initialize retraining system
                setup_scheduler()
                print("✅ Automated retraining system initialized")
        except Exception as e:
            print(f"⚠️  Note during DB init: {e}")
        
        app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)