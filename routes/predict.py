from flask import Blueprint, request, render_template, redirect, url_for, flash
import joblib
import numpy as np

predict_bp = Blueprint('predict_bp', __name__, url_prefix='/predict')

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            _model = joblib.load("risk_model.pkl")  # Make sure this path is correct
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            _model = None
    return _model

@predict_bp.route('/', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            # Extract input features from form
            features = [
                float(request.form.get('age', 0)),
                float(request.form.get('income', 0)),
                float(request.form.get('loan_amount', 0)),
                float(request.form.get('credit_score', 0)),
                float(request.form.get('employment_years', 0))
            ]
            model = get_model()
            if model is None:
                flash("Model not available. Please contact admin.", "danger")
                return redirect(url_for('predict_bp.predict'))

            prediction = model.predict(np.array([features]))[0]
            risk_level = "High Risk" if prediction == 1 else "Low Risk"
            return render_template('prediction_result.html', risk=risk_level)

        except Exception as e:
            flash(f"Prediction failed: {str(e)}", "danger")
            return redirect(url_for('predict_bp.predict'))

    return render_template('prediction.html')
