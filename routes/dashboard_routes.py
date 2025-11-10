from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import db, User, LoanApplication, Client
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard with comprehensive statistics"""
    try:
        # Query counts
        total_users = db.session.query(User).count()
        total_clients = db.session.query(Client).count()
        total_loans = db.session.query(LoanApplication).count()
        
        # Loan status counts
        pending_loans = db.session.query(LoanApplication).filter(
            LoanApplication.status.in_(['pending', 'Pending', 'under_review'])
        ).count()
        
        approved_loans = db.session.query(LoanApplication).filter(
            LoanApplication.status.in_(['approved', 'Approved'])
        ).count()
        
        rejected_loans = db.session.query(LoanApplication).filter(
            LoanApplication.status.in_(['rejected', 'Rejected'])
        ).count()
        
        defaulted_loans = db.session.query(LoanApplication).filter(
            LoanApplication.status.in_(['defaulted', 'Defaulted'])
        ).count()

        # Financial metrics
        total_amount_result = db.session.query(func.sum(LoanApplication.loan_amount)).scalar()
        total_loan_amount = total_amount_result if total_amount_result else 0
        avg_loan_amount = round(total_loan_amount / total_loans, 2) if total_loans > 0 else 0
        
        # Rates
        approval_rate = round((approved_loans / total_loans * 100), 1) if total_loans > 0 else 0
        default_rate = round((defaulted_loans / total_loans * 100), 1) if total_loans > 0 else 0

        # Recent loans for activity feed
        recent_loans = LoanApplication.query.order_by(LoanApplication.created_at.desc()).limit(5).all()

        print(f"✅ ADMIN DASHBOARD - Loans: {total_loans}, Pending: {pending_loans}, Approved: {approved_loans}")

        return render_template('admin_dashboard.html',
            username=current_user.username,
            total_users=total_users,
            total_clients=total_clients,
            total_loans=total_loans,
            pending_loans=pending_loans,
            approved_loans=approved_loans,
            rejected_loans=rejected_loans,
            defaulted_loans=defaulted_loans,
            avg_loan_amount=avg_loan_amount,
            approval_rate=approval_rate,
            default_rate=default_rate,
            recent_loans=recent_loans
        )

    except Exception as e:
        print(f"❌ Admin dashboard error: {e}")
        return render_template('admin_dashboard.html',
            username=current_user.username,
            total_users=0, total_clients=0, total_loans=0,
            pending_loans=0, approved_loans=0, rejected_loans=0,
            defaulted_loans=0, avg_loan_amount=0, approval_rate=0,
            default_rate=0, recent_loans=[]
        )

@dashboard_bp.route('/officer')
@login_required
def officer_dashboard():
    """Officer dashboard"""
    try:
        total_loans = db.session.query(LoanApplication).count()
        pending_loans = db.session.query(LoanApplication).filter(
            LoanApplication.status.in_(['pending', 'Pending', 'under_review'])
        ).count()
        approved_loans = db.session.query(LoanApplication).filter_by(status='approved').count()
        rejected_loans = db.session.query(LoanApplication).filter_by(status='rejected').count()
        
        # Officer-specific: loans assigned to current officer
        my_loans = LoanApplication.query.filter_by(assigned_officer_id=current_user.id).count()
        my_pending = LoanApplication.query.filter_by(
            assigned_officer_id=current_user.id, 
            status='pending'
        ).count()
        
        print(f"💰 Officer - Total loans: {total_loans}, Pending: {pending_loans}")
        
        return render_template('officer_dashboard.html', 
                            username=current_user.username,
                            total_loans=total_loans,
                            pending_loans=pending_loans,
                            approved_loans=approved_loans,
                            rejected_loans=rejected_loans,
                            my_loans=my_loans,
                            my_pending=my_pending)
    except Exception as e:
        print(f"❌ Officer dashboard error: {e}")
        return render_template('officer_dashboard.html',
                            username=current_user.username,
                            total_loans=0, pending_loans=0,
                            approved_loans=0, rejected_loans=0,
                            my_loans=0, my_pending=0)

@dashboard_bp.route('/borrower')
@login_required
def borrower_dashboard():
    """Borrower dashboard"""
    try:
        # Get borrower's applications
        user_applications = LoanApplication.query.filter_by(user_id=current_user.id).all()
        
        # Calculate stats
        stats = {
            'total': len(user_applications),
            'pending': len([app for app in user_applications if app.status in ['pending', 'under_review']]),
            'approved': len([app for app in user_applications if app.status == 'approved']),
            'rejected': len([app for app in user_applications if app.status == 'rejected']),
            'active': len([app for app in user_applications if app.status == 'active'])
        }
        
        # Calculate total borrowed amount
        total_borrowed = sum([app.loan_amount for app in user_applications if app.status in ['approved', 'active']])
        
        print(f"👤 Borrower - User ID: {current_user.id}, Stats: {stats}")
        
        return render_template('borrower_dashboard.html', 
                            username=current_user.username,
                            stats=stats,
                            applications=user_applications,
                            total_borrowed=total_borrowed)
    
    except Exception as e:
        print(f"❌ Borrower dashboard error: {e}")
        default_stats = {
            'total': 0, 'pending': 0, 'approved': 0, 'rejected': 0, 'active': 0
        }
        return render_template('borrower_dashboard.html',
                            username=current_user.username,
                            stats=default_stats,
                            applications=[],
                            total_borrowed=0)

@dashboard_bp.route('/api/stats')
@login_required
def api_dashboard_stats():
    """API endpoint for dashboard statistics"""
    try:
        # Get comprehensive dashboard statistics
        total_users = db.session.query(User).count()
        total_clients = db.session.query(Client).count()
        total_loans = db.session.query(LoanApplication).count()
        
        pending_loans = db.session.query(LoanApplication).filter(
            LoanApplication.status.in_(['pending', 'Pending', 'under_review'])
        ).count()
        
        approved_loans = db.session.query(LoanApplication).filter_by(status='approved').count()
        rejected_loans = db.session.query(LoanApplication).filter_by(status='rejected').count()
        defaulted_loans = db.session.query(LoanApplication).filter_by(status='defaulted').count()
        
        # Financial metrics
        total_amount_result = db.session.query(func.sum(LoanApplication.loan_amount)).scalar()
        total_loan_amount = total_amount_result if total_amount_result else 0
        avg_loan_amount = round(total_loan_amount / total_loans, 2) if total_loans > 0 else 0
        
        # Rates
        approval_rate = round((approved_loans / total_loans * 100), 1) if total_loans > 0 else 0
        default_rate = round((defaulted_loans / total_loans * 100), 1) if total_loans > 0 else 0
        
        dashboard_stats = {
            'users': {
                'total': total_users,
                'clients': total_clients
            },
            'loans': {
                'total': total_loans,
                'pending': pending_loans,
                'approved': approved_loans,
                'rejected': rejected_loans,
                'defaulted': defaulted_loans
            },
            'financials': {
                'total_amount': total_loan_amount,
                'avg_loan_amount': avg_loan_amount
            },
            'rates': {
                'approval_rate': approval_rate,
                'default_rate': default_rate
            },
            'status': 'success',
            'timestamp': '2025-01-15 10:30:00'
        }
        
        print(f"✅ API Stats: {total_loans} loans, {pending_loans} pending")
        return jsonify(dashboard_stats)
    
    except Exception as e:
        print(f"❌ API dashboard stats error: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

# Debug and utility routes
@dashboard_bp.route('/debug-data')
@login_required
def debug_data():
    """Debug route to check all data"""
    try:
        clients = Client.query.all()
        client_list = []
        for client in clients:
            client_list.append({
                'id': client.id,
                'name': client.name,
                'income': client.income,
                'credit_score': client.credit_score
            })
        
        debug_info = {
            'total_users': db.session.query(User).count(),
            'total_clients': db.session.query(Client).count(),
            'total_loans': db.session.query(LoanApplication).count(),
            'clients_data': client_list,
            'client_table_exists': True,
            'status': 'success'
        }
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e), 'client_table_exists': False, 'status': 'error'}), 500

@dashboard_bp.route('/test-all-models')
def test_all_models():
    try:
        results = {
            'users_count': db.session.query(User).count(),
            'clients_count': db.session.query(Client).count(),
            'loans_count': db.session.query(LoanApplication).count(),
            'status': 'All models working correctly!'
        }
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'Model error'}), 500

@dashboard_bp.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'dashboard'})

@dashboard_bp.route('/endpoints')
def list_endpoints():
    """List all available endpoints in this blueprint"""
    endpoints = [
        {'url': '/dashboard/admin', 'method': 'GET', 'description': 'Admin dashboard'},
        {'url': '/dashboard/officer', 'method': 'GET', 'description': 'Loan officer dashboard'},
        {'url': '/dashboard/borrower', 'method': 'GET', 'description': 'Borrower dashboard'},
        {'url': '/dashboard/api/stats', 'method': 'GET', 'description': 'API statistics endpoint'},
        {'url': '/dashboard/debug-data', 'method': 'GET', 'description': 'Debug data endpoint'},
        {'url': '/dashboard/test-all-models', 'method': 'GET', 'description': 'Test all database models'},
        {'url': '/dashboard/health', 'method': 'GET', 'description': 'Health check'}
    ]
    return jsonify({'endpoints': endpoints, 'total': len(endpoints)})