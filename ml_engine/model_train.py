import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import joblib
import os

def train_xgb_model():
    df = pd.read_csv('data/loan_data.csv')  # Make sure this file exists

    df = df.dropna()
    df = pd.get_dummies(df, drop_first=True)

    X = df.drop('default', axis=1)
    y = df['default']

    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)

    os.makedirs('ml_engine/models', exist_ok=True)
    joblib.dump(model, 'ml_engine/models/xgb_model.pkl')
    print("✅ XGBoost model trained and saved.")

if __name__ == '__main__':
    train_xgb_model()
