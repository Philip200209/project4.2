from flask import Blueprint, render_template, request
from auth_utils import login_required
from database import get_db_connection
from ml_engine.model_predict import predict_risk  # ML scoring function

risk_bp = Blueprint('risk_bp', __name__)

@risk_bp.route('/risk')
@login_required
def view_risk():
    min_score = request.args.get('min_score', default=0.7, type=float)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch loan + client features (no 'region')
    cursor.execute("""
        SELECT loans.id AS loan_id, clients.id AS client_id, clients.name,
               loans.amount, loans.term, clients.income,
               clients.credit_score, loans.repayment_status
        FROM loans
        JOIN clients ON loans.client_id = clients.id
    """)
    raw_data = cursor.fetchall()

    risk_data = []
    for row in raw_data:
        input_dict = {
            "loan_amount": row['amount'],
            "term": row['term'],
            "income": row['income'],
            "credit_score": row['credit_score'],
            "repayment_status": row['repayment_status']
        }
        risk_score = predict_risk(input_dict, model_name='xgb')  # ML scoring
        if risk_score >= min_score:
            row['risk_score'] = risk_score
            risk_data.append(row)

    cursor.close()
    conn.close()

    # FIXED: Changed 'risk.html' to 'risk_analytics.html'
    return render_template('risk_analytics.html', risk_data=risk_data, min_score=min_score)