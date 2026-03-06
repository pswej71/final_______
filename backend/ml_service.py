import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import IsolationForest

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
MODEL_PATH = os.path.join(MODEL_DIR, 'anomaly_model.joblib')

class MLModelService:
    def __init__(self):
        self.model = None
        self.features = ['voltage', 'current', 'temperature', 'dust_index']
        self.load_model()

    def train_model(self, telemetry_data: list):
        """Train and save the model based on historical telemetry."""
        if len(telemetry_data) < 50:
            return False # Not enough data
            
        df = pd.DataFrame(telemetry_data)
        available_features = [f for f in self.features if f in df.columns]
        
        if len(available_features) > 0:
            X = df[available_features].fillna(0)
            
            # Re-train Isolation Forest
            clf = IsolationForest(contamination=0.05, random_state=42)
            clf.fit(X)
            self.model = clf
            
            # Save the model
            os.makedirs(MODEL_DIR, exist_ok=True)
            joblib.dump(self.model, MODEL_PATH)
            print(f"Model successfully saved to {MODEL_PATH}")
            return True
            
        return False

    def load_model(self):
        """Load the model if it exists on disk."""
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                print("Anomaly Detection model loaded from disk.")
            except Exception as e:
                print(f"Error loading model: {e}")
                self.model = None

    def predict_anomalies(self, df: pd.DataFrame):
        """Predict anomalies for a dataframe using the loaded model."""
        if self.model is None:
            # Fallback inline calculation if model doesn't exist yet
            available_features = [f for f in self.features if f in df.columns]
            if len(available_features) > 0:
                X = df[available_features].fillna(0)
                clf = IsolationForest(contamination=0.05, random_state=42)
                preds = clf.fit_predict(X)
                return preds == -1
            return [False] * len(df)
            
        # Use trained model
        available_features = [f for f in self.features if f in df.columns]
        if len(available_features) > 0:
            X = df[available_features].fillna(0)
            preds = self.model.predict(X)
            return preds == -1 # -1 means anomaly in IsolationForest
            
        return [False] * len(df)

ml_service = MLModelService()

def analyze_trends_and_anomalies(telemetry_data):
    if len(telemetry_data) < 10:
        data_list = []
        for t in telemetry_data:
            d = t.__dict__.copy()
            d.pop('_sa_instance_state', None)
            data_list.append(d)
        return data_list
    
    data_list = []
    for t in telemetry_data:
        d = t.__dict__.copy()
        d.pop('_sa_instance_state', None)
        data_list.append(d)
        
    df = pd.DataFrame(data_list)
    
    # Predict anomalies using the persistent ML model
    df['is_anomaly'] = ml_service.predict_anomalies(df)
        
    # Analytics: Trend Analysis using Moving Average
    if 'energy' in df.columns:
        df['energy_trend'] = df['energy'].rolling(window=5, min_periods=1).mean()
    if 'efficiency' in df.columns:
        df['efficiency_trend'] = df['efficiency'].rolling(window=5, min_periods=1).mean()
        
    return df.to_dict(orient='records')
