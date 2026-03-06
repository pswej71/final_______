from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import database
import db_models as models
import schemas
from gemini_service import get_suggestions
from ml_service import analyze_trends_and_anomalies
import json
import asyncio
from datetime import datetime
import random

import sys
import os

# Add models directory to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)
from models.predictive_maintenance_pipeline import ProductionPipeline
from monitoring import monitor
from reports import MaintenanceReporter

piped_model = ProductionPipeline()

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Solar Inverter Monitoring API")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

@app.get("/")
def read_root():
    return {"message": "Solar Inverter API is Running"}

@app.post("/api/inverter/telemetry", response_model=schemas.Telemetry)
async def create_telemetry(telemetry: schemas.TelemetryCreate, db: Session = Depends(database.get_db)):
    efficiency = 0.0
    if telemetry.solar_irradiance > 0:
        efficiency = (telemetry.power / telemetry.solar_irradiance) * 100

    # Calculate failure risk using the predictive pipeline
    mock_sensor_state = {
        'eff_loss_1H': -0.01 if efficiency > 80 else -0.15,
        'voltage_imbalance': random.uniform(0.5, 3.0),
        'thermal_stress': telemetry.power * telemetry.temperature,
        'temperature': telemetry.temperature,
        'power_drop': random.uniform(-50, 0),
        'inverter_power': telemetry.power
    }
    
    risk_score = 0.0
    try:
        risk_result = piped_model.predict_real_time(current_telemetry=mock_sensor_state, recent_weather={})
        risk_score = risk_result.get('failure_probability_7d', 0.0)
    except Exception as e:
        print(f"Error calculating risk during intake: {e}")

    db_item = models.InverterTelemetry(
        **telemetry.dict(),
        efficiency=efficiency,
        is_anomaly=False, # This gets evaluated when querying history
        predicted_energy=telemetry.energy * 1.05, # Mock prediction factor
        failure_risk=risk_score
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # Run system health check
    history = db.query(models.InverterTelemetry).order_by(models.InverterTelemetry.timestamp.desc()).limit(20).all()
    history_dicts = []
    for h in history:
        hd = h.__dict__.copy()
        hd.pop('_sa_instance_state', None)
        history_dicts.append(hd)
        
    current_data = db_item.__dict__.copy()
    current_data.pop('_sa_instance_state', None)
    monitor.evaluate_health(current_data, history_dicts)
    
    # Broadcast to connected websocket clients
    for client in clients:
        try:
            d = db_item.__dict__.copy()
            d.pop('_sa_instance_state', None)
            d['timestamp'] = d['timestamp'].isoformat()
            await client.send_json(d)
        except Exception:
            pass

    return db_item

@app.get("/api/inverter/history")
def get_history(limit: int = 100, db: Session = Depends(database.get_db)):
    items = db.query(models.InverterTelemetry).order_by(models.InverterTelemetry.timestamp.desc()).limit(limit).all()
    # Reverse to return chronological order
    items = items[::-1]
    
    # Apply ML Trend Analysis and Anomaly Detection
    processed_data = analyze_trends_and_anomalies(items)
    return processed_data

@app.get("/api/inverter/latest")
def get_latest_telemetry(db: Session = Depends(database.get_db)):
    item = db.query(models.InverterTelemetry).order_by(models.InverterTelemetry.timestamp.desc()).first()
    if not item:
        return {}
    
    d = item.__dict__.copy()
    d.pop('_sa_instance_state', None)
    return d

@app.get("/api/alerts")
def get_alerts(db: Session = Depends(database.get_db)):
    faults = db.query(models.InverterTelemetry).filter(models.InverterTelemetry.status != "Normal").order_by(models.InverterTelemetry.timestamp.desc()).limit(10).all()
    
    faults_dict = []
    for f in faults:
        d = f.__dict__.copy()
        d.pop('_sa_instance_state', None)
        faults_dict.append(d)
        
    return {
        "faults": faults_dict
    }

@app.get("/api/ai/suggestions")
def get_ai_suggestions(db: Session = Depends(database.get_db)):
    # Get last 15 readings for context
    items = db.query(models.InverterTelemetry).order_by(models.InverterTelemetry.timestamp.desc()).limit(15).all()
    items = items[::-1]
    
    data_dicts = []
    for item in items:
        d = item.__dict__.copy()
        d.pop('_sa_instance_state', None)
        d['timestamp'] = str(d['timestamp'])
        data_dicts.append(d)
        
    # Example alert logic
    alerts = ["Low efficiency warning"] if any((d.get('efficiency', 100) < 50 for d in data_dicts)) else []
    
    suggestion = get_suggestions(telemetry_data=data_dicts, alerts=alerts)
    return suggestion

# Simulator Endpoint for Testing easily without real sensors
@app.post("/api/simulator/generate")
async def generate_mock_data(db: Session = Depends(database.get_db)):
    telemetry = schemas.TelemetryCreate(
        voltage=random.uniform(210, 240),
        current=random.uniform(10, 50),
        power=random.uniform(2000, 10000),
        energy=random.uniform(10, 50),
        frequency=random.uniform(49.8, 50.2),
        temperature=random.uniform(30, 60),
        status="Normal" if random.random() > 0.1 else "Warning",
        solar_irradiance=random.uniform(400, 1000),
        ambient_temperature=random.uniform(20, 45),
        dust_index=random.uniform(0, 100),
        air_quality_index=random.uniform(20, 150)
    )
    
    efficiency = 0.0
    if telemetry.solar_irradiance > 0:
        efficiency = (telemetry.power / telemetry.solar_irradiance) * 100

    # Calculate failure risk for simulation
    mock_sensor_state = {
        'eff_loss_1H': -0.01 if efficiency > 80 else -0.15,
        'voltage_imbalance': random.uniform(2.0, 10.0) if telemetry.status != "Normal" else random.uniform(0.5, 3.0),
        'thermal_stress': telemetry.power * telemetry.temperature,
        'temperature': telemetry.temperature,
        'power_drop': random.uniform(-50, 0) if telemetry.power > 1000 else random.uniform(-2000, -1000),
        'inverter_power': telemetry.power
    }
    
    risk_score = 0.0
    try:
        risk_result = piped_model.predict_real_time(current_telemetry=mock_sensor_state, recent_weather={})
        risk_score = risk_result.get('failure_probability_7d', 0.0)
    except Exception as e:
        print(f"Simulation risk error: {e}")

    try:
        db_item = models.InverterTelemetry(
            **telemetry.dict(),
            efficiency=efficiency,
            is_anomaly=False,
            predicted_energy=telemetry.energy * 1.05,
            failure_risk=risk_score
        )
        print("DEBUG: db_item created, adding to DB...")
        db.add(db_item)
        print("DEBUG: db.add done, committing...")
        db.commit()
        print("DEBUG: db.commit done, refreshing...")
        db.refresh(db_item)
        print("DEBUG: db.refresh done.")
    except Exception as e:
        print(f"CRITICAL SQL ERROR during simulation: {e}")
        db.rollback()
        raise e
    
    # Run system health check for simulation
    print("DEBUG: Fetching history for health check...")
    history = db.query(models.InverterTelemetry).order_by(models.InverterTelemetry.timestamp.desc()).limit(20).all()
    print(f"DEBUG: Found {len(history)} history items.")
    history_dicts = []
    for h in history:
        hd = h.__dict__.copy()
        hd.pop('_sa_instance_state', None)
        history_dicts.append(hd)
    
    current_data = db_item.__dict__.copy()
    current_data.pop('_sa_instance_state', None)
    monitor.evaluate_health(current_data, history_dicts)
    
    # Broadcast to connected websocket clients
    for client in clients:
        try:
            d = db_item.__dict__.copy()
            d.pop('_sa_instance_state', None)
            d['timestamp'] = d['timestamp'].isoformat()
            await client.send_json(d)
        except Exception:
            pass
            
    return {"message": "Data generated successfully"}

@app.post("/api/ml/train")
def train_anomaly_model(db: Session = Depends(database.get_db)):
    # Grab last 1000 items to train
    items = db.query(models.InverterTelemetry).order_by(models.InverterTelemetry.timestamp.desc()).limit(1000).all()
    if len(items) < 50:
        return {"status": "error", "message": "Not enough data to train (need at least 50)"}
        
    data_list = []
    for t in items:
        d = t.__dict__.copy()
        d.pop('_sa_instance_state', None)
        data_list.append(d)
        
    success = ml_service.train_model(data_list)
    return {"status": "success" if success else "error", "message": "Model retrained and saved to disk"}


@app.get("/api/predictive/risk")
def get_predictive_risk(db: Session = Depends(database.get_db)):
    item = db.query(models.InverterTelemetry).order_by(models.InverterTelemetry.timestamp.desc()).first()
    if not item:
        return {
            "failure_probability_7d": 0.0,
            "risk_level": "Low",
            "explanation": "No data available.",
            "key_contributing_factors": []
        }
    
    # Map raw telemetry to features needed by the predict_real_time engine
    mock_sensor_state = {
        'eff_loss_1H': -0.01 if item.efficiency > 80 else -0.15,
        'voltage_imbalance': random.uniform(2.0, 10.0) if item.status != "Normal" else random.uniform(0.5, 3.0),
        'thermal_stress': item.power * item.temperature,
        'temperature': item.temperature,
        'power_drop': random.uniform(-50, 0) if item.power > 1000 else random.uniform(-2000, -1000),
        'inverter_power': item.power
    }
    
    try:
        # Get history for LSTM sequence construction (last 60 min = 30 samples)
        history = db.query(models.InverterTelemetry).order_by(models.InverterTelemetry.timestamp.desc()).limit(30).all()
        history_df = pd.DataFrame([h.__dict__ for h in history[::-1]])
        if not history_df.empty:
            history_df.pop('_sa_instance_state', None)
            
        prob = piped_model.ml_model.predict_hybrid(pd.Series(mock_sensor_state), history_df)
        result = piped_model.xai.generate_explanation(prob, pd.Series(mock_sensor_state))
        return result
    except Exception as e:
        return {
            "failure_probability_7d": 0.0,
            "risk_level": "Unknown",
            "explanation": f"Failed evaluating risk: {str(e)}",
            "key_contributing_factors": []
        }

@app.get("/api/system/status")
def get_system_status():
    return monitor.last_status

@app.get("/api/reports/generate")
def generate_maintenance_report(days: int = 7, db: Session = Depends(database.get_db)):
    reporter = MaintenanceReporter(db)
    return reporter.generate_report(days=days)
