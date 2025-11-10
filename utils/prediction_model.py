from utils.sms_utils import send_sms_alert

def predict_risk(features, phone_number=None):
    """
    Predicts loan risk based on input features.

    Parameters:
    - features (list of float): [loan_amount, term, income, credit_score]
    - phone_number (str, optional): If provided, sends SMS alert for high-risk predictions

    Returns:
    - float: risk score between 0 and 1
    """
    if len(features) != 4:
        raise ValueError("Expected 4 features: [loan_amount, term, income, credit_score]")

    loan_amount, term, income, credit_score = features

    # Simple mock logic: higher loan-to-income ratio and lower credit score = higher risk
    try:
        risk_score = (loan_amount / max(income, 1)) * (1 - credit_score / 100)
        risk_score = round(min(max(risk_score, 0), 1), 2)
    except Exception as e:
        print(f"[Prediction Error] {e}")
        return None

    # Optional: trigger SMS alert for high-risk cases
    if risk_score >= 0.7 and phone_number:
        message = f"⚠️ High loan risk detected (score: {risk_score}). Manual review recommended."
        send_sms_alert(phone_number, message)

    return risk_score
