from flask import Blueprint, render_template, flash, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from utils.db import get_db_connection
from utils.audit_utils import log_action
import mysql.connector

loan_bp = Blueprint('loan_bp', __name__, url_prefix='/loans')

# Test route to verify blueprint is working
@loan_bp.route('/test')
def test_route():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Blueprint Test</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                padding: 40px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
            }
            .container {
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                max-width: 600px;
                margin: 0 auto;
            }
            .success {
                background: #4CAF50;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Loan Blueprint Test</h1>
            <div class="success">
                <h2>SUCCESS!</h2>
                <p>The loan blueprint is working correctly.</p>
                <p>Your routes are properly registered.</p>
            </div>
            <p>Now test the main page:</p>
            <a href="/loans/review" style="color: #FFD700; font-weight: bold; font-size: 1.2em;">
                Go to Loan Review Page →
            </a>
        </div>
    </body>
    </html>
    """

@loan_bp.route('/review')
@login_required
def review_loans():
    print("🎯 [LOAN ROUTE] /loans/review endpoint hit!")
    print(f"👤 User: {current_user.username}")
    print(f"🎭 Role: {current_user.role}")
    print(f"🎭 Role type: {type(current_user.role)}")
    print(f"🎭 Role repr: {repr(current_user.role)}")
    
    try:
        # FIXED: Better role checking that handles both string and Role objects
        user_role = str(current_user.role).lower()
        allowed_roles = ['admin', 'loan_officer']
        
        print(f"🔍 Checking access: user_role='{user_role}', allowed_roles={allowed_roles}")
        
        # Check if user has access
        has_access = any(allowed_role in user_role for allowed_role in allowed_roles)
        
        if not has_access:
            print(f"❌ Access denied for role: {user_role}")
            flash("🔒 Access denied: Insufficient permissions", "danger")
            return redirect(url_for('dashboard_bp.admin_dashboard'))
        
        print("✅ Access granted - user has appropriate role")
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            flash("❌ Database connection failed", "danger")
            # Fallback to sample data
            return render_template('loan_review.html', 
                                loans=get_sample_loans(),
                                is_sample_data=True)
        
        cursor = conn.cursor(dictionary=True)
        
        # Check if loan_applications table exists
        try:
            cursor.execute("SHOW TABLES LIKE 'loan_applications'")
            table_exists = cursor.fetchone()
            if not table_exists:
                print("⚠️ loan_applications table doesn't exist")
                flash("Loan applications table not found in database", "warning")
                return render_template('loan_review.html', 
                                    loans=get_sample_loans(),
                                    is_sample_data=True)
        except Exception as e:
            print(f"❌ Error checking tables: {e}")
            conn.close()
            return render_template('loan_review.html', 
                                loans=get_sample_loans(),
                                is_sample_data=True)
        
        # ✅ FIXED: Fetch from loan_applications table instead of loans
        print("🔄 Fetching loan applications from database...")
        cursor.execute("""
            SELECT 
                id,
                loan_amount as amount,
                loan_term as duration_months,
                status,
                created_at,
                applicant_name,
                applicant_email,
                loan_purpose
            FROM loan_applications 
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        raw_loans = cursor.fetchall()
        print(f"📊 Found {len(raw_loans)} loan applications in database")
        
        # Process applications
        applications = []
        for row in raw_loans:
            try:
                application = {
                    'id': row.get('id', 0),
                    'amount': float(row.get('amount', 0)),
                    'term': row.get('duration_months', 0),
                    'status': map_loan_status(row.get('status', 'pending')),
                    'raw_status': row.get('status', 'pending'),
                    'submitted_at': format_date(row.get('created_at')),
                    'client_name': row.get('applicant_name', f"Client {row.get('id', 'N/A')}"),
                    'email': row.get('applicant_email', 'N/A'),
                    'purpose': row.get('loan_purpose', 'General')
                }
                applications.append(application)
            except Exception as e:
                print(f"⚠️ Error processing application row: {e}")
                continue
        
        cursor.close()
        conn.close()
        
        # If no applications found, use sample data
        if not applications:
            print("ℹ️ No loan applications found, using sample data")
            applications = get_sample_loans()
            is_sample_data = True
        else:
            is_sample_data = False
        
        print(f"🚀 Rendering template with {len(applications)} applications")
        
        # Log the action
        log_action(current_user.id, current_user.username, "Viewed loan applications", "Loans")
        
        return render_template('loan_review.html', 
                             loans=applications, 
                             is_sample_data=is_sample_data,
                             current_user=current_user)
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR in review_loans: {e}")
        import traceback
        traceback.print_exc()
        
        # Emergency fallback - bypass role check
        print("🆘 Using emergency fallback - bypassing role check")
        return render_template('loan_review.html', 
                             loans=get_sample_loans(), 
                             is_sample_data=True,
                             error=str(e),
                             current_user=current_user)

@loan_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply_loan():
    """Apply for a new loan (for borrowers)"""
    print("🎯 [LOAN] Apply loan route hit")
    
    try:
        # Check if user is a borrower
        user_role = str(current_user.role).lower()
        if 'borrower' not in user_role:
            flash("Only borrowers can apply for loans", "danger")
            return redirect(url_for('dashboard_bp.borrower_dashboard'))
        
        if request.method == 'POST':
            print("📝 Processing loan application")
            
            # ✅ FIXED: Better amount parsing with error handling
            try:
                loan_amount_str = request.form.get('loan_amount', '0').strip()
                # Remove any commas or spaces
                loan_amount_str = loan_amount_str.replace(',', '').replace(' ', '')
                loan_amount = float(loan_amount_str)
                print(f"💰 Parsed loan amount: {loan_amount}")
            except (ValueError, TypeError) as e:
                print(f"❌ Error parsing loan amount: {e}")
                flash("Please enter a valid loan amount (numbers only)", "warning")
                return render_template('loan_application.html', current_user=current_user)
            
            try:
                loan_term = int(request.form.get('loan_term', 12))
            except (ValueError, TypeError):
                flash("Please select a valid loan term", "warning")
                return render_template('loan_application.html', current_user=current_user)
                
            loan_purpose = request.form.get('loan_purpose', 'General')
            terms_accepted = request.form.get('terms_accepted') == 'on'
            
            # ✅ FIXED: Better validation with clear messages
            if loan_amount < 1000:
                flash("Loan amount must be at least KSh 1,000", "warning")
                return render_template('loan_application.html', current_user=current_user)
            
            if loan_amount > 1000000:
                flash("Loan amount cannot exceed KSh 1,000,000", "warning")
                return render_template('loan_application.html', current_user=current_user)
            
            if loan_term not in [6, 12, 18, 24, 36]:
                flash("Please select a valid loan term", "warning")
                return render_template('loan_application.html', current_user=current_user)
            
            if not terms_accepted:
                flash("You must agree to the terms and conditions", "warning")
                return render_template('loan_application.html', current_user=current_user)
            
            # Get database connection
            conn = get_db_connection()
            if not conn:
                flash("Database connection failed", "danger")
                return render_template('loan_application.html', current_user=current_user)
            
            cursor = conn.cursor()
            
            # ✅ FIXED: Insert into loan_applications table with correct columns
            cursor.execute("""
                INSERT INTO loan_applications 
                (loan_amount, loan_term, loan_purpose, terms_accepted, status, applicant_name, applicant_email)
                VALUES (%s, %s, %s, %s, 'pending', %s, %s)
            """, (loan_amount, loan_term, loan_purpose, terms_accepted, current_user.username, current_user.email))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash(f'✅ Loan application for KSh {loan_amount:,.2f} submitted successfully! It will be reviewed by our loan officers.', 'success')
            log_action(current_user.id, current_user.username, f"Applied for loan: KSh {loan_amount:,.2f}", "Loans")
            return redirect(url_for('dashboard_bp.borrower_dashboard'))
        
        # GET request - show application form
        return render_template('loan_application.html', current_user=current_user)
        
    except Exception as e:
        print(f"💥 Error in apply_loan: {e}")
        flash(f"Error submitting loan application: {e}", "danger")
        return render_template('loan_application.html', current_user=current_user)

@loan_bp.route('/repayment-history/<int:loan_id>')
@login_required
def repayment_history(loan_id):
    """View repayment history for a specific loan"""
    print(f"🎯 [LOAN] Repayment history requested for loan {loan_id}")
    
    try:
        # Check if user has access
        user_role = str(current_user.role).lower()
        if 'loan_officer' not in user_role and 'admin' not in user_role:
            flash("Unauthorized access", "danger")
            return redirect(url_for('dashboard_bp.officer_dashboard'))
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return redirect(url_for('dashboard_bp.officer_dashboard'))
        
        cursor = conn.cursor(dictionary=True)
        
        # Get loan details from loan_applications table
        cursor.execute("SELECT * FROM loan_applications WHERE id = %s", (loan_id,))
        loan = cursor.fetchone()
        
        if not loan:
            flash("Loan not found", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard_bp.officer_dashboard'))
        
        # Get repayment history (sample data for now)
        repayment_history = [
            {
                'id': 1,
                'due_date': '2024-01-15',
                'paid_date': '2024-01-14',
                'amount': loan['loan_amount'] / loan['loan_term'],
                'status': 'Paid',
                'penalty': 0.00
            },
            {
                'id': 2,
                'due_date': '2024-02-15',
                'paid_date': None,
                'amount': loan['loan_amount'] / loan['loan_term'],
                'status': 'Pending',
                'penalty': 0.00
            },
            {
                'id': 3,
                'due_date': '2024-03-15',
                'paid_date': None,
                'amount': loan['loan_amount'] / loan['loan_term'],
                'status': 'Pending',
                'penalty': 0.00
            }
        ]
        
        cursor.close()
        conn.close()
        
        # Log the action
        log_action(current_user.id, current_user.username, f"Viewed repayment history for loan {loan_id}", "Loans")
        
        return render_template('repayment_history.html', 
                             loan=loan, 
                             repayment_history=repayment_history,
                             current_user=current_user)
        
    except Exception as e:
        print(f"💥 Error in repayment_history: {e}")
        flash(f"Error loading repayment history: {e}", "danger")
        return redirect(url_for('dashboard_bp.officer_dashboard'))

@loan_bp.route('/approve/<int:loan_id>')
@login_required
def approve_loan(loan_id):
    user_role = str(current_user.role).lower()
    if 'admin' not in user_role and 'loan_officer' not in user_role:
        flash("Unauthorized access", "danger")
        return redirect(url_for('loan_bp.review_loans'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # ✅ FIXED: Update loan_applications table
        cursor.execute("UPDATE loan_applications SET status = 'approved' WHERE id = %s", (loan_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'Loan application #{loan_id} approved successfully!', 'success')
        log_action(current_user.id, current_user.username, f"Approved loan application {loan_id}", "Loans")
    except Exception as e:
        flash(f'Error approving loan: {e}', 'danger')
    
    return redirect(url_for('loan_bp.review_loans'))

@loan_bp.route('/reject/<int:loan_id>')
@login_required
def reject_loan(loan_id):
    user_role = str(current_user.role).lower()
    if 'admin' not in user_role and 'loan_officer' not in user_role:
        flash("Unauthorized access", "danger")
        return redirect(url_for('loan_bp.review_loans'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # ✅ FIXED: Update loan_applications table
        cursor.execute("UPDATE loan_applications SET status = 'rejected' WHERE id = %s", (loan_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'Loan application #{loan_id} rejected!', 'warning')
        log_action(current_user.id, current_user.username, f"Rejected loan application {loan_id}", "Loans")
    except Exception as e:
        flash(f'Error rejecting loan: {e}', 'danger')
    
    return redirect(url_for('loan_bp.review_loans'))

@loan_bp.route('/details/<int:loan_id>')
@login_required
def loan_details(loan_id):
    """View loan application details"""
    try:
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return redirect(url_for('loan_bp.review_loans'))
            
        cursor = conn.cursor(dictionary=True)
        
        # ✅ FIXED: Fetch from loan_applications table
        cursor.execute("SELECT * FROM loan_applications WHERE id = %s", (loan_id,))
        loan = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not loan:
            flash('Loan application not found', 'danger')
            return redirect(url_for('loan_bp.review_loans'))
            
        return render_template('loan_details.html', loan=loan)
        
    except Exception as e:
        print(f"❌ Error fetching loan details: {e}")
        flash(f'Error loading loan details: {e}', 'danger')
        return redirect(url_for('loan_bp.review_loans'))

@loan_bp.route('/api/loans')
@login_required
def api_loans():
    """API endpoint for loan applications data"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        # ✅ FIXED: Fetch from loan_applications table
        cursor.execute("SELECT * FROM loan_applications ORDER BY created_at DESC")
        loans = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(loans)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_sample_loans():
    """Return sample loan application data for testing"""
    return [
        {
            'id': 1001,
            'amount': 50000.0,
            'term': 12,
            'status': 'Pending Review',
            'raw_status': 'pending',
            'submitted_at': '2024-01-15 10:30:00',
            'client_name': 'Sample Client A',
            'email': 'client_a@example.com',
            'purpose': 'Business Expansion'
        },
        {
            'id': 1002,
            'amount': 150000.0,
            'term': 24,
            'status': 'Approved',
            'raw_status': 'approved',
            'submitted_at': '2024-01-14 14:45:00',
            'client_name': 'Sample Client B',
            'email': 'client_b@example.com',
            'purpose': 'Education'
        },
        {
            'id': 1003,
            'amount': 75000.0,
            'term': 18,
            'status': 'Active',
            'raw_status': 'active',
            'submitted_at': '2024-01-13 09:15:00',
            'client_name': 'Sample Client C',
            'email': 'client_c@example.com',
            'purpose': 'Home Improvement'
        }
    ]

def map_loan_status(status):
    """Map database status to display status"""
    status_map = {
        'pending': 'Pending Review',
        'approved': 'Approved',
        'active': 'Active',
        'rejected': 'Rejected',
        'completed': 'Completed'
    }
    return status_map.get(status, 'Pending Review')

def format_date(date_value):
    """Format date for display"""
    if not date_value:
        return "—"
    return str(date_value)