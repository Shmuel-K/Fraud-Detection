# callbacks.py

from dash import Input, Output, State
import threading
import plotly.express as px
import dash_bootstrap_components as dbc
from math import isnan

from utils import process_uploaded_file, save_to_database, get_historical_fraud_rate
from ml_model import fraud_model
from charts import (
    create_category_chart,
    create_pie_chart,
    create_transaction_time_chart,
    create_fraud_customers_chart,
    create_suspicious_transaction_table
)
from notifications import send_slack_notification, send_email_notification

# In-memory cache for historical fraud rate
_cached_hist_rate = None

def _cache_historical_rate():
    """Fetch and cache the historical fraud rate."""
    global _cached_hist_rate
    rate = get_historical_fraud_rate()
    if rate is not None:
        _cached_hist_rate = rate

# Preload the cache on startup in a background thread
threading.Thread(target=_cache_historical_rate, daemon=True).start()


def register_callbacks(app):
    @app.callback(
        Output('transaction-table', 'data'),
        Output('category-chart', 'figure'),
        Output('pie-chart', 'figure'),
        Output('transaction-time-chart', 'figure'),
        Output('save-status', 'children'),
        Output('fraud-customers-chart', 'figure'),
        Output('suspicious-row-div', 'children'),
        Output('suspicious-alert-div', 'children'),
        Input('uploader', 'contents'),
        State('uploader', 'filename')
    )
    def update_table(contents, filename):
        # 1) No file uploaded: return empty UI
        if not contents:
            empty_fig = px.bar(title='No data available').update_layout(template="plotly_dark")
            return [], empty_fig, empty_fig, empty_fig, "No file uploaded.", empty_fig, [], []

        # 2) Process uploaded file
        df = process_uploaded_file(contents)
        if df is None:
            empty_fig = px.bar(title='Invalid file format').update_layout(template="plotly_dark")
            return [], empty_fig, empty_fig, empty_fig, "Invalid file format.", empty_fig, [], []

        # 3) Prediction branch (do not retrain here)
        required_cols = [
            'step', 'customer', 'age', 'gender',
            'zipcodeOri', 'merchant', 'zipMerchant',
            'category', 'amount'
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            empty_fig = px.bar(title='No data').update_layout(template="plotly_dark")
            msg = f"Missing columns: {', '.join(missing)}"
            return [], empty_fig, empty_fig, empty_fig, msg, empty_fig, [], []

        # 4) Encode categorical and predict probabilities
        Xp = df[required_cols].copy()
        for col in Xp.select_dtypes(include=['object']):
            Xp[col] = Xp[col].astype('category').cat.codes

        probs = fraud_model.predict_proba(Xp)[:, 1]
        fraud_count = int((probs >= 0.5).sum())
        fraud_rate = fraud_count / len(probs) * 100

        # 5) Build status message using cached historical rate
        hist = _cached_hist_rate if _cached_hist_rate is not None else float('nan')
        status = (
            f"Detected {fraud_count}/{len(probs)} frauds ({fraud_rate:.2f}%). "
            + (f"Historical rate: {hist:.2f}%." if not isnan(hist) else "Computing historical rate...")
        )

        # 6) Determine severity level
        severity = float(probs.max())
        if severity > 0.7:
            level, color = "Severe", "danger"
        elif severity > 0.3:
            level, color = "Medium", "warning"
        else:
            level, color = "Low", "info"

        alert = dbc.Alert(f"Severity: {severity:.2f} ({level})", color=color)

        # 7) Send notifications in background threads
        if level == "Medium":
            threading.Thread(
                target=send_slack_notification,
                args=(level, alert.children),
                daemon=True
            ).start()
        elif level == "Severe":
            threading.Thread(
                target=send_slack_notification,
                args=(level, alert.children),
                daemon=True
            ).start()
            threading.Thread(
                target=send_email_notification,
                args=("Severe Fraud Alert", alert.children),
                daemon=True
            ).start()

        # 8) Save to database and refresh historical cache in background
        threading.Thread(
            target=save_to_database,
            args=(df, filename),
            daemon=True
        ).start()
        threading.Thread(target=_cache_historical_rate, daemon=True).start()

        # 9) Prepare suspicious transaction table if severity high
        if severity >= 0.5:
            idx = int(probs.argmax())
            suspicious = create_suspicious_transaction_table(df.iloc[[idx]])
        else:
            suspicious = []

        # 10) Return results for UI rendering
        return (
            df.to_dict('records'),
            create_category_chart(df),
            create_pie_chart(df),
            create_transaction_time_chart(df),
            status,
            create_fraud_customers_chart(df),
            suspicious,
            alert
        )
