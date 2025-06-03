# notifications.py

import os
import warnings
import requests
import smtplib
import ssl
from email.mime.text import MIMEText
from requests.exceptions import RequestException
from pathlib import Path
from dotenv import load_dotenv

# ——— Load your `env` file (not “.env”) ———
env_path = Path(__file__).parent / "env"
load_dotenv(dotenv_path=env_path)

# suppress only the single InsecureRequestWarning from urllib3
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ——— Configuration from environment ———
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()
SMTP_HOST        = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT        = int(os.getenv("SMTP_PORT", 587))
SMTP_USER        = os.getenv("SMTP_USER", "").strip()
SMTP_PASS        = os.getenv("SMTP_PASS", "").strip()
EMAIL_FROM       = os.getenv("EMAIL_FROM", "").strip()
EMAIL_TO         = [addr.strip() for addr in os.getenv("EMAIL_TO", "").split(",") if addr.strip()]


def send_slack_notification(level: str, message: str):
    """Post a simple text message to Slack, skipping SSL verify."""
    if not SLACK_WEBHOOK_URL:
        print("[notifications] No SLACK_WEBHOOK_URL configured, skipping Slack alert.")
        return

    payload = {"text": f"{level.upper()} ALERT: {message}"}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=urllib3.exceptions.InsecureRequestWarning)
            resp = requests.post(
                SLACK_WEBHOOK_URL,
                json=payload,
                timeout=5,
                verify=False
            )
        resp.raise_for_status()
    except RequestException as e:
        print(f"[notifications] Slack error: {e}")


def send_email_notification(subject: str, body: str):
    """Send a plain-text email; guard against mis-configured SMTP host."""
    if not (SMTP_HOST and EMAIL_FROM and EMAIL_TO):
        print("[notifications] SMTP or recipient not configured, skipping email alert.")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls(context=context)
            if SMTP_USER and SMTP_PASS:
                server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    except Exception as e:
        print(f"[notifications] Email error: {e}")


