# ml_model.py

import os
import pandas as pd
import pickle
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE
from sqlalchemy import text
from utils import engine

fraud_model = None

def train_fraud_model():
    """
    Train the XGBoost fraud detection model only if the MODEL_PATH file does not exist.
    MODEL_PATH is read from the environment each time to allow overrides (e.g., in tests).
    If no training data is found, a default untrained model is still saved.
    """
    model_path = os.getenv("MODEL_PATH", "fraud_model.pkl")
    if os.path.exists(model_path):
        print(f"[ml_model] Model file '{model_path}' exists; skipping retrain.")
        return

    # 1) Identify tables with a 'fraud' column
    schema_sql = """
    SELECT m.table_name
      FROM dbo.MasterTable AS m
      JOIN INFORMATION_SCHEMA.COLUMNS AS c
        ON c.TABLE_SCHEMA = 'dbo'
       AND c.TABLE_NAME = m.table_name
       AND c.COLUMN_NAME = 'fraud'
     WHERE m.table_name LIKE 'transactions_%'
    """
    try:
        master_df = pd.read_sql(schema_sql, engine)
    except Exception as e:
        print(f"[ml_model] Error fetching table list: {e}")
        master_df = pd.DataFrame()

    # If no tables found, save a default model
    if master_df.empty:
        print("[ml_model] No training tables found; saving default model.")
        default_model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
        with open(model_path, "wb") as f:
            pickle.dump(default_model, f)
        return

    # 2) Load each table’s data
    training_dfs = []
    for tbl in master_df['table_name']:
        qry = text(f"""
            SELECT step, customer, age, gender,
                   zipcodeOri, merchant, zipMerchant,
                   category, amount, fraud
              FROM dbo.{tbl}
             WHERE fraud IN (0,1)
        """)
        try:
            df_part = pd.read_sql(qry, engine)
            if not df_part.empty:
                training_dfs.append(df_part)
        except Exception as e:
            print(f"[ml_model] Skipping table {tbl}: {e}")

    # If no valid data loaded, save a default model
    if not training_dfs:
        print("[ml_model] No valid training data found; saving default model.")
        default_model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
        with open(model_path, "wb") as f:
            pickle.dump(default_model, f)
        return

    # 3) Concatenate and preprocess
    df_all = pd.concat(training_dfs, ignore_index=True)
    X = df_all.drop('fraud', axis=1)
    y = df_all['fraud'].astype(int)

    # Label‐encode categorical features
    for col in X.select_dtypes(include=['object']).columns:
        X[col] = LabelEncoder().fit_transform(X[col].astype(str))

    # 4) Balance classes with SMOTE
    try:
        sm = SMOTE(random_state=42)
        X_res, y_res = sm.fit_resample(X, y)
    except Exception as e:
        print(f"[ml_model] SMOTE failed: {e}")
        return

    # 5) Compute scale_pos_weight
    pos = (y_res == 1).sum()
    neg = (y_res == 0).sum()
    scale_pw = neg / pos if pos else 1

    # 6) Train XGBoost
    model = xgb.XGBClassifier(
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42,
        scale_pos_weight=scale_pw
    )
    model.fit(X_res, y_res)

    # 7) Save the model
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"[ml_model] Model trained and saved to '{model_path}'.")


def load_fraud_model():
    """
    Load the fraud detection model from MODEL_PATH, training it first if needed.
    """
    global fraud_model
    model_path = os.getenv("MODEL_PATH", "fraud_model.pkl")
    if not os.path.exists(model_path):
        train_fraud_model()
    try:
        with open(model_path, "rb") as f:
            fraud_model = pickle.load(f)
        print(f"[ml_model] Model loaded from '{model_path}'.")
    except Exception as e:
        print(f"[ml_model] Failed to load model: {e}")
        fraud_model = None


def detect_fraud(df):
    """
    Predict fraud on the given DataFrame and return a summary string.
    """
    if fraud_model is None:
        return "Fraud detection model is unavailable."

    required = [
        'step', 'customer', 'age', 'gender',
        'zipcodeOri', 'merchant', 'zipMerchant',
        'category', 'amount'
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return f"Missing required features: {', '.join(missing)}."

    Xp = df[required].copy()
    for col in Xp.select_dtypes(include=['object']).columns:
        Xp[col] = LabelEncoder().fit_transform(Xp[col].astype(str))

    preds = fraud_model.predict(Xp)
    # Handle both numpy arrays and lists
    try:
        n_fraud = int((preds == 1).sum())
    except Exception:
        n_fraud = sum(1 for p in preds if p == 1)

    return (
        f"{n_fraud} fraudulent transactions detected."
        if n_fraud > 0 else "No fraud detected."
    )


# Initialize the model on import
load_fraud_model()
