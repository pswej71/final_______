import pytest
from fastapi.testclient import TestClient
import pandas as pd
from api.main import app
from ml_model.pipeline import SolarPredictor

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Intelligent Solar Platform"}

def test_ml_prediction_layer():
    predictor = SolarPredictor()
    dummy_data = pd.DataFrame({
        'ac_power': [1000, 1000, 800, 900, 700],
        'dc_power': [1050, 1050, 850, 950, 900],
        'pv1_power': [500, 500, 400, 450, 350],
        'pv2_power': [500, 500, 400, 450, 350],
        'v_r': [230, 230, 220, 235, 230],
        'v_y': [230, 229, 225, 230, 230],
        'v_b': [230, 231, 215, 225, 230],
        'temperature': [40, 41, 55, 45, 60],
        'pv1_voltage': [500]*5,
        'pv2_voltage': [500]*5,
        'grid_voltage': [400]*5,
        'target': [0, 0, 1, 0, 2]
    })
    predictor.train_with_time_series_cv(dummy_data, 'target')
    
    test_df = pd.DataFrame([{
        'ac_power': 700, 'dc_power': 800, 'pv1_power': 350, 'pv2_power': 350,
        'v_r': 230, 'v_y': 230, 'v_b': 230, 'temperature': 65,
        'pv1_voltage': 500.0, 'pv2_voltage': 500.0, 'grid_voltage': 400.0
    }])
    result = predictor.predict(test_df)
    
    assert 'final_risk_score' in result
    assert 'risk_category' in result
    assert result['risk_category'] in [0, 1, 2]
    assert 0.0 <= result['final_risk_score'] <= 1.0

def test_risk_score_calculation():
    # Test feature engineering formulas directly
    predictor = SolarPredictor()
    test_df = pd.DataFrame([{
        'ac_power': 500, 'dc_power': 1000,
        'pv1_power': 600, 'pv2_power': 300,
        'v_r': 240, 'v_y': 230, 'v_b': 220, 'temperature': 50,
        'pv1_voltage': 500.0, 'pv2_voltage': 500.0, 'grid_voltage': 400.0
    }])
    features_df = predictor.feature_engineering(test_df)
    
    # Efficiency = ac / dc = 500 / 1000 = 0.5
    assert features_df.iloc[0]['inverter_efficiency'] == 0.5
    # PV Imbalance = |600 - 300| = 300
    assert features_df.iloc[0]['pv_imbalance'] == 300
    # Thermal stress = 500 * 50 = 25000
    assert features_df.iloc[0]['thermal_stress'] == 25000
