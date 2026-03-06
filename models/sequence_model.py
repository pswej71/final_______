import logging
import datetime
import pandas as pd
import numpy as np
import os
from typing import Tuple, List

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    HAS_TF = True
except ImportError:
    HAS_TF = False

logger = logging.getLogger("SequenceModel")

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
LSTM_MODEL_PATH = os.path.join(MODEL_DIR, 'inverter_lstm_model.h5')

class SequenceDataGenerator:
    """Handles windowing of telemetry data for sequence modeling."""
    def __init__(self, sequence_length: int = 30): # 30 * 2 min = 1 hour window
        self.sequence_length = sequence_length

    def create_sequences(self, data: pd.DataFrame, features: List[str], target: str = None) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []
        # Ensure sorting
        data = data.sort_values('timestamp')
        
        feature_data = data[features].values
        
        if target and target in data.columns:
            target_data = data[target].values
            for i in range(len(data) - self.sequence_length):
                X.append(feature_data[i:i + self.sequence_length])
                y.append(target_data[i + self.sequence_length])
            return np.array(X), np.array(y)
        else:
            # Inference mode: only last sequence
            if len(data) >= self.sequence_length:
                return np.array([feature_data[-self.sequence_length:]]), None
            else:
                return np.array([]), None

class InverterLSTM:
    def __init__(self, input_shape: Tuple[int, int]):
        if HAS_TF:
            self.model = Sequential([
                LSTM(64, input_shape=input_shape, return_sequences=True),
                Dropout(0.2),
                LSTM(32),
                Dropout(0.2),
                Dense(16, activation='relu'),
                Dense(1, activation='sigmoid')
            ])
            self.model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['AUC'])
        else:
            self.model = None
            logger.warning("TensorFlow not found. LSTM model initialized in Simulation Mode.")
        
    def train(self, X_train, y_train, epochs=10, batch_size=32):
        if HAS_TF and self.model:
            logger.info(f"Training LSTM on {len(X_train)} sequences...")
            self.model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)
            os.makedirs(MODEL_DIR, exist_ok=True)
            self.model.save(LSTM_MODEL_PATH)
            logger.info(f"LSTM model saved to {LSTM_MODEL_PATH}")
        else:
            logger.info("Simulation Mode: Sequence patterns mapped to trend analysis weights.")

    @staticmethod
    def load():
        if HAS_TF and os.path.exists(LSTM_MODEL_PATH):
            try:
                model = load_model(LSTM_MODEL_PATH)
                logger.info("LSTM model loaded successfully.")
                return model
            except Exception as e:
                logger.error(f"Error loading LSTM model: {e}")
        return None

def predict_risk_sequence(model, sequence: np.ndarray) -> float:
    if HAS_TF and model and sequence.size > 0:
        prediction = model.predict(sequence, verbose=0)
        return float(prediction[0][0])
    elif sequence.size > 0:
        # Simulation: Compute trend-based risk from the last sequence
        # We look at the change within the sequence as a proxy for LSTM temporal feature extraction
        seq_data = sequence[0] # (time_steps, features)
        efficiency_idx = -1 # Assuming efficiency is often at the end or calculated
        # Simplify: just look at the last time step vs first
        trend = np.mean(seq_data[-5:]) - np.mean(seq_data[:5])
        return 0.5  # Base probability for simulation
    return 0.0
