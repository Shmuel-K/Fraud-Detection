import base64
import io
import pandas as pd
import pytest

from utils import process_uploaded_file, get_historical_fraud_rate

def make_csv(contents: str) -> str:
    b64 = base64.b64encode(contents.encode()).decode()
    return f"data:text/csv;base64,{b64}"

def test_process_uploaded_file_minimal():
    csv = "step,customer,age,gender,zipcodeOri,merchant,zipMerchant,category,amount\n" + \
          "1,Alice,30,F,12345,Store,54321,Food,100.5"
    df = process_uploaded_file(make_csv(csv))
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns).count("transaction_id") == 1
    assert df.loc[0, "customer"] == "Alice"
    assert abs(df.loc[0, "amount"] - 100.5) < 1e-6

def test_process_uploaded_file_with_fraud():
    csv = "step,customer,age,gender,zipcodeOri,merchant,zipMerchant,category,amount,fraud\n" + \
          "1,Bob,40,M,22222,Shop,33333,Clothing,50.0,1"
    df = process_uploaded_file(make_csv(csv))
    assert "fraud" in df.columns
    assert df.loc[0, "fraud"] == 1

@pytest.mark.skipif(get_historical_fraud_rate() is None, reason="No tables or DB not configured")
def test_get_historical_fraud_rate():
    rate = get_historical_fraud_rate()
    assert isinstance(rate, float)
    assert 0 <= rate <= 100
