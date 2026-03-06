import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import IsolationForest
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import shap
import json
import logging

logger = logging.getLogger(__name__)
 
 
class SolarPredictor:
    def __init__(self):
        self.risk_model = xgb.XGBClassifier(
            objective='multi:softprob',
            num_class=3, # 0 = No Risk, 1 = Degradation, 2 = Shutdown
            eval_metric='mlogloss',
            n_estimators=100,
            max_depth=4,
            random_state=42
        )
        self.anomaly_model = IsolationForest(contamination=0.05, random_state=42)
        self.features = [
            'inverter_efficiency', 'pv_imbalance', 'voltage_imbalance', 
            'thermal_stress', 'power_drop_rate', 'temperature', 'pv1_voltage', 'pv2_voltage', 'grid_voltage'
        ]
        self.explainer = None
    
    def feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Calculate features based on required formulas
        df['inverter_efficiency'] = df.apply(
            lambda row: row['ac_power'] / (row['dc_power'] + 1e-6) if pd.notna(row.get('ac_power')) else 0.95, axis=1
        )
        
        if 'pv1_power' in df.columns and 'pv2_power' in df.columns:
            df['pv_imbalance'] = abs(df['pv1_power'] - df['pv2_power'])
        else:
            df['pv_imbalance'] = 0
            
        if all(c in df.columns for c in ['v_r', 'v_y', 'v_b']):
            df['voltage_imbalance'] = df[['v_r', 'v_y', 'v_b']].std(axis=1)
        else: # Default or placeholder if not present
            df['voltage_imbalance'] = 0
            
        if 'temperature' in df.columns and 'ac_power' in df.columns:
            df['thermal_stress'] = df['temperature'] * df['ac_power']
        else:
            df['thermal_stress'] = 0
            
        # power drop rate
        df['power_drop_rate'] = df['ac_power'].diff().fillna(0)
        
        for col in self.features:
            if col not in df.columns:
                df[col] = 0.0

        return df

    def train_with_time_series_cv(self, df: pd.DataFrame, target_col: str):
        df = self.feature_engineering(df)
        X = df[self.features]
        y = df[target_col]
        
        tscv = TimeSeriesSplit(n_splits=3)
        metrics = []
        for train_index, test_index in tscv.split(X):
            X_train, X_test = X.iloc[train_index], X.iloc[test_index]
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]
            
            self.risk_model.fit(X_train, y_train)
            
            preds = self.risk_model.predict(X_test)
            probs = self.risk_model.predict_proba(X_test)
            
            # Weighted metrics for multi-class
            metrics.append({
                'precision': precision_score(y_test, preds, average='weighted', zero_division=0),
                'recall': recall_score(y_test, preds, average='weighted', zero_division=0),
                'f1': f1_score(y_test, preds, average='weighted', zero_division=0),
                # multi_class roc auc needs specific setup
                'roc_auc': roc_auc_score(y_test, probs, multi_class='ovr') if len(set(y_test)) > 1 else 0.5
            })
            
        logger.info(f"CV Metrics: {metrics}")
        
        # Fit on all
        self.risk_model.fit(X, y)
        self.anomaly_model.fit(X)
        self.explainer = shap.TreeExplainer(self.risk_model)
        
    def predict(self, input_df: pd.DataFrame):
        df = self.feature_engineering(input_df)
        X = df[self.features]
        
        # Risk predictions
        probs = self.risk_model.predict_proba(X)[0] # assumes single row prediction
        predicted_class = int(np.argmax(probs))
        ml_risk_score = 1.0 - probs[0] # Risk is not 0
        
        # Anomaly score
        # decision_function gives score, lower is more anomalous. Convert to [0,1]
        anomaly_score_raw = self.anomaly_model.decision_function(X)[0]
        # map to 0,1 roughly
        anomaly_score = 1 - (1 / (1 + np.exp(-anomaly_score_raw * -10)))
        
        final_risk = 0.7 * float(ml_risk_score) + 0.3 * float(anomaly_score)
        
        # SHAP Explanations
        shap_values = self.explainer.shap_values(X)
        if isinstance(shap_values, list):
            # Extract features pointing towards the predicted class
            vals = np.abs(shap_values[predicted_class][0])
        else:
            vals = np.abs(shap_values[0])
            
        feature_importance = pd.DataFrame(list(zip(self.features, vals)), columns=['feature', 'importance'])\
            .sort_values(by='importance', ascending=False)
            
        top_5 = feature_importance.head(5).to_dict('records')
        
        return {
            'risk_category': predicted_class,
            'final_risk_score': round(final_risk, 2),
            'anomaly_score': round(anomaly_score, 2),
            'top_features': top_5
        }
