import logging
from flask import Flask, redirect, url_for, render_template, flash, request, session, jsonify
from flask_session import Session
from flask_login import LoginManager, logout_user, current_user, login_required, login_user
from flask_mail import Mail, Message

# Correct imports - db from extensions, models from models package
from extensions import db, login_manager, mail
from models import User, Client, Loan, Intervention

from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone, timedelta
import json
import os

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
                    
                    # Update behavior score
                    loan.behavior_score = max(0, loan.behavior_score - 10)
                    
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
        """Update behavior scores for all active loans"""
        try:
            active_loans = Loan.query.filter_by(status='approved').all()
            updated = 0
            
            for loan in active_loans:
                new_score = BehaviorMonitor.calculate_behavior_score(loan)
                if loan.behavior_score != new_score:
                    loan.behavior_score = new_score
                    updated += 1
            
            db.session.commit()
            return f"Updated {updated} behavior scores"
            
        except Exception as e:
            logger.error(f"Error updating behavior scores: {e}")
            return f"Error: {e}"

    @staticmethod
    def calculate_behavior_score(loan):
        """Calculate comprehensive behavior score"""
        score = 100
        
        # Payment history impact
        if loan.payments_missed > 0:
            score -= (loan.payments_missed * 15)
        
        # Recent activity
        if loan.last_payment_date:
            days_since_last_payment = (datetime.now(timezone.utc).date() - loan.last_payment_date).days
            if days_since_last_payment > 30:
                score -= 15
            elif days_since_last_payment > 15:
                score -= 5
        
        return max(0, min(100, score))

# ===== INTERVENTION BOT SYSTEM =====
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
                status='simulated'  # Change to 'sent' when using real SMS API
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
        """Check all loans and trigger appropriate interventions"""
        try:
            active_loans = Loan.query.filter_by(status='approved').all()
            interventions_sent = 0
            
            for loan in active_loans:
                # Check behavior score for high risk
                if loan.behavior_score < 40:
                    InterventionBot.send_sms_reminder(loan, "high_risk_alert")
                    interventions_sent += 1
                
                # Check for missed payments
                elif loan.payments_missed > 0:
                    InterventionBot.send_sms_reminder(loan, "missed_payment")
                    interventions_sent += 1
                
                # Payment reminder for upcoming payments
                elif loan.next_payment_date:
                    days_until_due = (loan.next_payment_date - datetime.now(timezone.utc).date()).days
                    if 0 <= days_until_due <= 3:  # Due in next 3 days
                        InterventionBot.send_sms_reminder(loan, "payment_reminder")
                        interventions_sent += 1
            
            return f"Checked {len(active_loans)} loans, sent {interventions_sent} interventions"
            
        except Exception as e:
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
            <p><strong>Amount:</strong> KSh {loan.amount:,.2f}</p>
            <p><strong>Term:</strong> {loan.term} months</p>
            <p><strong>Purpose:</strong> {loan.purpose}</p>
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
    """Root route - ALWAYS go to login page"""
    return redirect(url_for('login_page'))

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
        else:
            return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            role = request.form.get('role', 'borrower')  # ← CHANGED: Get role from form
            
            if not all([username, email, password, confirm_password, role]):
                flash('Please fill in all fields.', 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('register.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
                return render_template('register.html')
            
            # Validate role ← ADDED: Role validation
            valid_roles = ['borrower', 'loan_officer', 'admin']
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
                role=role,  # ← THIS WILL NOW USE THE SELECTED ROLE
                created_at=datetime.now(timezone.utc)
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'Registration successful! Your account type: {role.title()}', 'success')  # ← UPDATED
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
        else:
            return redirect(url_for('login_page'))
    
    user_loans = Loan.query.filter_by(client_email=current_user.email).order_by(Loan.created_at.desc()).all()
    
    stats = {
        'pending': len([loan for loan in user_loans if loan.status == 'pending']),
        'approved': len([loan for loan in user_loans if loan.status == 'approved']),
        'rejected': len([loan for loan in user_loans if loan.status == 'rejected'])
    }
    
    return render_template('borrower_dashboard.html',
        username=current_user.username,
        loans=user_loans,
        stats=stats,
        total_loans=len(user_loans)
    )

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

# ===== INTERVENTION ROUTES =====

@app.route('/interventions')
@login_required
def interventions_page():
    """View all interventions"""
    if current_user.role not in ['admin', 'loan_officer']:
        flash('Access denied.', 'error')
        return redirect(url_for('borrower_dashboard'))
    
    interventions = Intervention.query.order_by(Intervention.sent_at.desc()).all()
    today = datetime.now(timezone.utc).date()
    
    return render_template('interventions.html',
                         username=current_user.username,
                         interventions=interventions,
                         today=today)

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
    
    clients = Client.query.all()
    return render_template('clients.html', username=current_user.username, clients=clients)

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

@app.route('/analytics')
def analytics():
    return redirect(url_for('reports_page'))

@app.route('/predictions')
def predictions():
    return redirect(url_for('prediction_page'))

@app.route('/risk')
def risk():
    return redirect(url_for('prediction_page'))

@app.route('/loans/apply', methods=['GET', 'POST'])
@login_required
def apply_loan():
    role = current_user.role.lower()
    if role != 'borrower':
        flash('Only borrowers can apply for loans.', 'error')
        if role == 'admin':
            return redirect(url_for('dashboard'))
        elif role in ['loan_officer', 'officer']:
            return redirect(url_for('loan_officer_dashboard'))
        else:
            return redirect(url_for('login_page'))
    
    if request.method == 'POST':
        try:
            amount = request.form.get('amount')
            term = request.form.get('term')
            purpose = request.form.get('purpose')
            
            if not all([amount, term, purpose]):
                flash('Please fill in all required fields.', 'error')
                return render_template('apply_loan.html', username=current_user.username)
            
            new_loan = Loan(
                client_name=current_user.username,
                client_email=current_user.email,
                amount=float(amount),
                term=int(term),
                purpose=purpose,
                status='pending',
                risk_score=50.0,
                interest_rate=12.0,
                monthly_income=0.0,
                employment_status='unknown',
                credit_history='unknown',
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            db.session.add(new_loan)
            db.session.commit()
            
            email_sent = send_loan_application_email(new_loan)
            if email_sent:
                flash('Loan application submitted successfully! Notification email sent to loan officers.', 'success')
            else:
                flash('Loan application submitted successfully! (Email notification failed)', 'warning')
            
            return redirect(url_for('borrower_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error submitting loan application. Please try again.', 'error')
            logger.error(f"Loan application error: {e}")
    
    return render_template('apply_loan.html', username=current_user.username)

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
    print("")
    print("🔗 TESTING URLS:")
    print("   /test-behavior - Test behavior monitoring")
    print("   /test-interventions - Test intervention system")
    print("   /behavior-monitoring - View behavior dashboard")
    print("   /interventions - View interventions")
    print("   /api/trigger-interventions - Run intervention check")
    print("")
    
    try:
        with app.app_context():
            # Create database tables
            db.create_all()
            loan_count = Loan.query.count()
            user_count = User.query.count()
            intervention_count = Intervention.query.count()
            print(f"✅ Database: {user_count} users, {loan_count} loans, {intervention_count} interventions")
            
    except Exception as e:
        print(f"⚠️  Note: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)