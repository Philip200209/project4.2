import pandas as pd
import joblib

def predict_risk(input_dict, model_name='xgb'):
    model = joblib.load(f'ml_engine/models/{model_name}_model.pkl')

    # Convert input to DataFrame
    df = pd.DataFrame([input_dict])
    df = pd.get_dummies(df)

    # Align with training features
    model_features = model.get_booster().feature_names if model_name == 'xgb' else model.feature_names_in_
    for col in model_features:
        if col not in df.columns:
            df[col] = 0
    df = df[model_features]

    # Predict
    prob = model.predict_proba(df)[0][1]
    return round(prob, 3)
