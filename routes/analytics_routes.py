from flask import Blueprint, render_template
from flask_login import login_required, current_user
from utils.db import get_db_connection
from utils.audit_utils import log_action

analytics_bp = Blueprint('analytics_bp', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@login_required
def analytics_dashboard():
    """Main analytics dashboard"""
    print("🎯 [ANALYTICS] Analytics dashboard accessed")
    
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return render_template('analytics_dashboard.html', 
                                analytics_data=get_sample_analytics())
        
        cursor = conn.cursor(dictionary=True)
        
        # Get loan application statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_applications,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                AVG(loan_amount) as avg_loan_amount,
                MAX(loan_amount) as max_loan_amount,
                MIN(loan_amount) as min_loan_amount
            FROM loan_applications
        """)
        stats = cursor.fetchone()
        
        # Get applications by month
        cursor.execute("""
            SELECT 
                DATE_FORMAT(created_at, '%Y-%m') as month,
                COUNT(*) as count,
                AVG(loan_amount) as avg_amount
            FROM loan_applications 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY month DESC
        """)
        monthly_data = cursor.fetchall()
        
        # Get loan purposes distribution
        cursor.execute("""
            SELECT 
                loan_purpose,
                COUNT(*) as count,
                AVG(loan_amount) as avg_amount
            FROM loan_applications 
            WHERE loan_purpose IS NOT NULL AND loan_purpose != ''
            GROUP BY loan_purpose
            ORDER BY count DESC
        """)
        purpose_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        analytics_data = {
            'overview_stats': stats,
            'monthly_trends': monthly_data,
            'purpose_distribution': purpose_data,
            'total_volume': stats['total_applications'] or 0,
            'approval_rate': (stats['approved'] / stats['total_applications'] * 100) if stats['total_applications'] > 0 else 0
        }
        
        # Log the access
        log_action(current_user.id, current_user.username, "Accessed analytics dashboard", "Analytics")
        
        return render_template('analytics_dashboard.html',
                            analytics_data=analytics_data,
                            current_user=current_user)
        
    except Exception as e:
        print(f"💥 Error in analytics_dashboard: {e}")
        return render_template('analytics_dashboard.html',
                            analytics_data=get_sample_analytics(),
                            error=str(e),
                            current_user=current_user)

def get_sample_analytics():
    """Return sample analytics data for fallback"""
    return {
        'overview_stats': {
            'total_applications': 2,
            'pending': 2,
            'approved': 0,
            'rejected': 0,
            'avg_loan_amount': 74000,
            'max_loan_amount': 98000,
            'min_loan_amount': 50000
        },
        'monthly_trends': [
            {'month': '2024-11', 'count': 2, 'avg_amount': 74000}
        ],
        'purpose_distribution': [
            {'loan_purpose': 'Personal', 'count': 1, 'avg_amount': 98000},
            {'loan_purpose': 'General', 'count': 1, 'avg_amount': 50000}
        ],
        'total_volume': 2,
        'approval_rate': 0
    }