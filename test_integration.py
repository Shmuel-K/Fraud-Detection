# tests/test_integration.py

import pytest
import pandas as pd
from app import server

@pytest.fixture

def client():
    return server.test_client()


def test_api_empty(client, monkeypatch):
    # Simulate no transaction tables
    monkeypatch.setattr(pd, 'read_sql', lambda *args, **kwargs: pd.DataFrame())
    resp = client.get('/api/v1/transactions')
    assert resp.status_code == 200
    assert resp.json == []


def test_api_success(client, monkeypatch):
    # Simulate one master table and one data row
    master_df = pd.DataFrame({'table_name': ['transactions_1']})
    data_df = pd.DataFrame([{'a': 1, 'b': 2}])
    call_count = {'n': 0}
    def fake_read_sql(query, conn, *args, **kwargs):
        call_count['n'] += 1
        return master_df if call_count['n'] == 1 else data_df
    monkeypatch.setattr(pd, 'read_sql', fake_read_sql)

    resp = client.get('/api/v1/transactions')
    assert resp.status_code == 200
    assert resp.json == [{'a': 1, 'b': 2}]


def test_dash_index(client):
    # Check that the Dash index page loads
    resp = client.get('/')
    assert resp.status_code == 200
    # Dash serves a DOCTYPE and entry-point div
    assert b'<!DOCTYPE html>' in resp.data
    assert b'id="react-entry-point"' in resp.data
