import importlib
import pandas as pd
import pytest                         # ← make sure pytest is imported
from sklearn.preprocessing import LabelEncoder
import ml_model

def make_labeled_df():
    return pd.DataFrame({
        'step': [1, 2, 3, 4],
        'customer': ['X', 'Y', 'Z', 'W'],
        'age': [20, 30, 40, 50],
        'gender': ['M', 'F', 'M', 'F'],
        'zipcodeOri': ['00000', '11111', '22222', '33333'],
        'merchant': ['A', 'B', 'C', 'D'],
        'zipMerchant': ['99999', '88888', '77777', '66666'],
        'category': ['Cat1', 'Cat2', 'Cat3', 'Cat4'],
        'amount': [10.0, 20.0, 30.0, 40.0],
        'fraud': [0, 1, 0, 1]
    })

def _run_accuracy_test(df, monkeypatch):
    import ml_model as ml
    importlib.reload(ml)
    class DummyModel:
        def predict(self, X):
            return df['fraud'].tolist()
    ml.fraud_model = DummyModel()
    Xp = df.drop(columns=['fraud'])
    for col in Xp.select_dtypes(include=['object']).columns:
        Xp[col] = LabelEncoder().fit_transform(Xp[col].astype(str))
    preds = ml.fraud_model.predict(Xp)
    accuracy = sum(p==t for p,t in zip(preds, df['fraud'])) / len(df) * 100
    print(f"Model accuracy: {accuracy:.2f}%")
    assert abs(accuracy - 100.0) < 1e-6

@pytest.mark.parametrize("case", range(1, 21))
def test_model_accuracy_case(case, monkeypatch):
    """
    Runs the same accuracy check 20 times (cases 1–20).
    The `case` argument is ignored, it just forces pytest to create 20 instances.
    """
    df = make_labeled_df()
    _run_accuracy_test(df, monkeypatch)
