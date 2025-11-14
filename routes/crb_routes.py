from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models.crb_report import CRBReport
from models.loan import Loan
from services.crb_service import CRBService

crb_bp = Blueprint('crb', __name__)

@crb_bp.route('/crb-dashboard')
@login_required
def crb_dashboard():
    """CRB Monitoring Dashboard"""
    if current_user.role not in ['admin', 'risk_analyst']:
        return "Access denied", 403
    
    total_checks = CRBReport.query.count()
    blacklisted = CRBReport.query.filter_by(blacklist_status=True).count()
    high_risk = CRBReport.query.filter(CRBReport.credit_score < 550).count()
    recent_reports = CRBReport.query.order_by(CRBReport.created_at.desc()).limit(10).all()
    
    return render_template('crb_dashboard.html',
                         username=current_user.username,
                         total_checks=total_checks,
                         blacklisted=blacklisted,
                         high_risk=high_risk,
                         recent_reports=recent_reports)

@crb_bp.route('/api/crb-stats')
@login_required
def crb_stats():
    """API endpoint for CRB statistics"""
    try:
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