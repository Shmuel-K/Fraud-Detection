import importlib
import pytest


def test_send_slack_notification(monkeypatch):
    # Override the webhook URL before importing the module
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "http://example.com/webhook")

    import notifications
    importlib.reload(notifications)  # ensure the env var is picked up

    captured = {}

    def fake_post(url, json, timeout, verify):
        captured["url"] = url

        class DummyResp:
            def raise_for_status(self):
                pass

        return DummyResp()

    import requests
    monkeypatch.setattr(requests, "post", fake_post)

    notifications.send_slack_notification("test", "dummy message")
    assert captured.get("url") == "http://example.com/webhook"


def test_send_email_notification(monkeypatch):
    # Minimal SMTP environment variables
    monkeypatch.setenv("SMTP_HOST", "smtp.test")
    monkeypatch.setenv("EMAIL_FROM", "a@b.com")
    monkeypatch.setenv("EMAIL_TO", "x@b.com,y@b.com")

    import notifications
    importlib.reload(notifications)

    delivered = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def starttls(self, context):
            pass

        def login(self, user, pwd):
            pass

        def sendmail(self, frm, to, msg):
            delivered["to"] = to

        def quit(self):
            pass

    import smtplib
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    notifications.send_email_notification("subject", "body")
    assert delivered.get("to") == ["x@b.com", "y@b.com"]
