import json
import pytest
from server import register_api_routes
from flask import Flask

@pytest.fixture
def client(monkeypatch):
    app = Flask(__name__)
    register_api_routes(app)
    return app.test_client()

def test_get_transactions_empty(client, monkeypatch):
    # simulate no tables
    import pandas as pd
    monkeypatch.setattr("server.pd.read_sql", lambda *a, **k: pd.DataFrame())
    resp = client.get("/api/v1/transactions")
    assert resp.status_code == 200
    assert resp.json == []

def test_get_transactions_success(client, monkeypatch):
    import pandas as pd
    df_master = pd.DataFrame({'table_name':['transactions_1']})
    df_data = pd.DataFrame([{'a':1,'b':2}])
    calls = {'count':0}
    def fake_read_sql(q, engine):
        calls['count'] += 1
        return df_master if calls['count']==1 else df_data
    monkeypatch.setattr("server.pd.read_sql", fake_read_sql)
    resp = client.get("/api/v1/transactions")
    assert resp.status_code == 200
    assert isinstance(resp.json, list)
    assert resp.json[0]['a'] == 1
