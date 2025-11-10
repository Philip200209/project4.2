from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from utils.db import get_db_connection
from utils.audit_utils import log_action

predict_bp = Blueprint('predict_bp', __name__, url_prefix='/predict')

@predict_bp.route('/')
@login_required
def predict_home():
    """Loan prediction home page"""
    print("🎯 Predict home route called")
    print(f"👤 User: {current_user.username}, Role: {current_user.role}")
    
    return render_template('prediction.html', username=current_user.username)

@predict_bp.route('/check', methods=['POST'])
@login_required
def check_eligibility():
    """Check loan eligibility"""
    print("🎯 Check eligibility route called")
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Extract form data
        loan_amount = float(data.get('loan_amount', 0))
        loan_term = int(data.get('loan_term', 12))
        purpose = data.get('purpose', 'personal')
        monthly_income = float(data.get('monthly_income', 0))
        employment_type = data.get('employment_type', 'employed')
        
        print(f"📊 Prediction data: Amount={loan_amount}, Term={loan_term}, Income={monthly_income}")
        
        # Basic eligibility logic (replace with your ML model)
        score = calculate_eligibility_score(loan_amount, loan_term, monthly_income, employment_type)
        
        # Determine eligibility message
        if score >= 80:
            message = "Excellent! You have a very high chance of loan approval."
            eligible = True
        elif score >= 60:
            message = "Good! You have a high chance of loan approval."
            eligible = True
        elif score >= 40:
            message = "Fair. You might be eligible with some conditions."
            eligible = True
        else:
            message = "We recommend improving your financial profile before applying."
            eligible = False
        
        # Log the prediction
        log_action(current_user.id, current_user.username, 
                  f"Checked loan eligibility - Score: {score}%", "Prediction")
        
        return jsonify({
            'success': True,
            'score': score,
            'eligible': eligible,
            'message': message,
            'recommendations': get_recommendations(score, loan_amount, monthly_income)
        })
        
    except Exception as e:
        print(f"❌ Error in eligibility check: {e}")
        return jsonify({
            'success': False,
            'message': 'Error processing your request. Please try again.'
        }), 500

def calculate_eligibility_score(loan_amount, loan_term, monthly_income, employment_type):
    """Calculate eligibility score based on basic rules"""
    score = 50  # Base score
    
    # Income-to-loan ratio (40% weight)
    monthly_loan_payment = loan_amount / loan_term
    income_ratio = monthly_loan_payment / monthly_income if monthly_income > 0 else 1
    
    if income_ratio <= 0.2:
        score += 30
    elif income_ratio <= 0.4:
        score += 20
    elif income_ratio <= 0.6:
        score += 10
    else:
        score -= 10
    
    # Employment type (20% weight)
    employment_scores = {
        'employed': 20,
        'self_employed': 15,
        'student': 5,
        'unemployed': 0
    }
    score += employment_scores.get(employment_type, 0)
    
    # Loan amount reasonableness (20% weight)
    if loan_amount <= monthly_income * 12:  # <= 1 year income
        score += 20
    elif loan_amount <= monthly_income * 24:  # <= 2 years income
        score += 10
    else:
        score -= 10
    
    # Loan term (10% weight)
    if 6 <= loan_term <= 36:
        score += 10
    else:
        score -= 5
    
    # Ensure score is between 0-100
    return max(0, min(100, score))

def get_recommendations(score, loan_amount, monthly_income):
    """Get personalized recommendations based on score"""
    if score >= 80:
        return "You're in a great position! Consider applying for the loan amount you requested."
    elif score >= 60:
        return "Consider reducing the loan amount slightly or providing additional collateral."
    elif score >= 40:
        return "We recommend improving your income documentation or considering a smaller loan amount."
    else:
        return "Focus on building your income stability and credit history before applying."

@predict_bp.route('/quick-check', methods=['GET'])
@login_required
def quick_check():
    """Quick eligibility check with minimal input"""
    print("🎯 Quick check route called")
    
    try:
        loan_amount = float(request.args.get('amount', 50000))
        
        # Get user's income from database if available
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT monthly_income FROM clients WHERE user_id = %s", (current_user.id,))
        client_data = cursor.fetchone()
        
        monthly_income = client_data['monthly_income'] if client_data and client_data['monthly_income'] else 30000
        
        cursor.close()
        conn.close()
        
        # Calculate basic score
        score = calculate_eligibility_score(loan_amount, 12, monthly_income, 'employed')
        
        return jsonify({
            'success': True,
            'score': score,
            'message': f'Quick check complete: {score}% eligibility score',
            'recommended_amount': monthly_income * 10  # 10 months income as recommendation
        })
        
    except Exception as e:
        print(f"❌ Error in quick check: {e}")
        return jsonify({
            'success': False,
            'message': 'Error performing quick check'
        }), 500