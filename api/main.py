from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Optional
import pandas as pd
import uvicorn
import asyncer

from ml_model.pipeline import SolarPredictor
from llm_layer.generator import generate_explanation, format_maintenance_ticket
from rag_pipeline.retriever import RAGRetriever

app = FastAPI(title="Production Intelligent Solar Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models
predictor = SolarPredictor()
# We train it with dummy data for immediate use in testing if no DB is available
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

class TelemetryInput(BaseModel):
    inverter_id: str
    block: str
    ac_power: float
    dc_power: float
    pv1_power: float
    pv2_power: float
    v_r: float
    v_y: float
    v_b: float
    temperature: float
    pv1_voltage: float = 500.0
    pv2_voltage: float = 500.0
    grid_voltage: float = 400.0

class PredictResponse(BaseModel):
    risk_score: float
    risk_category: int
    top_features: List[Dict[str, float]]
    llm_explanation: str
    maintenance_ticket: Optional[str] = None

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    answer: str

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Intelligent Solar Platform"}

@app.post("/predict", response_model=PredictResponse)
def predict_risk(telemetry: TelemetryInput):
    try:
        # 1. Convert to DataFrame
        df = pd.DataFrame([telemetry.model_dump()])
        
        # 2. ML Prediction (Risk + Anomaly)
        ml_result = predictor.predict(df)
        
        # 3. LLM Generation
        explanation = generate_explanation(
            ml_result['final_risk_score'], 
            ml_result['top_features'], 
            "Telemetry summary: TBD"
        )
        
        # 4. Agentic Workflow
        # Operator -> Retrieve telemetry -> Run ML -> Generate Explanation -> Draft Ticket
        ticket = None
        if ml_result['final_risk_score'] > 0.5:
            ticket = format_maintenance_ticket(
                telemetry.inverter_id,
                ml_result['final_risk_score'],
                telemetry.block,
                explanation
            )
            
        returnPredictResponse = {
            "risk_score": ml_result['final_risk_score'],
            "risk_category": ml_result['risk_category'],
            "top_features": ml_result['top_features'],
            "llm_explanation": explanation,
            "maintenance_ticket": ticket
        }
        return returnPredictResponse
        
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=AskResponse)
def ask_question(req: AskRequest):
    retriever = RAGRetriever(db_session=None)
    ans = retriever.ask_question(req.query)
    return {"answer": ans}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
