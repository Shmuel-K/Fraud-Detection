# tests/test_ml_model.py

import importlib
import pandas as pd

# Helper to create a minimal DataFrame
# No indentation before this function

def make_fake_df():
    return pd.DataFrame({
        'step': [1, 2],
        'customer': ['X', 'Y'],
        'age': [20, 30],
        'gender': ['M', 'F'],
        'zipcodeOri': ['00000', '11111'],
        'merchant': ['A', 'B'],
        'zipMerchant': ['99999', '88888'],
        'category': ['Cat1', 'Cat2'],
        'amount': [10.0, 20.0]
    })


def test_model_file_creation(tmp_path, monkeypatch):
    # Override MODEL_PATH via environment variable
    mp = tmp_path / 'fraud_model.pkl'
    monkeypatch.setenv('MODEL_PATH', str(mp))

    # Reload ml_model to pick up the new MODEL_PATH
    import ml_model
    importlib.reload(ml_model)

    # Ensure no leftover file
    if mp.exists():
        mp.unlink()

    # Train should create the model file
    ml_model.train_fraud_model()
    assert mp.exists(), f"Model file not created at {mp}"


def test_detect_fraud_with_fraud(monkeypatch):
    # Reload module to reset state
    import ml_model
    importlib.reload(ml_model)

    # Inject dummy model for predictable output
    class DummyModel:
        def predict(self, X):
            return [1] + [0] * (len(X) - 1)

    monkeypatch.setattr(ml_model, 'fraud_model', DummyModel())

    # Run detection on a fake dataframe
    df = make_fake_df()
    result = ml_model.detect_fraud(df)
    assert '1 fraudulent transactions detected' in result
