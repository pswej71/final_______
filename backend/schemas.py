from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TelemetryBase(BaseModel):
    voltage: float
    current: float
    power: float
    energy: float
    frequency: float
    temperature: float
    status: str
    solar_irradiance: float
    ambient_temperature: float
    dust_index: float
    air_quality_index: float

class TelemetryCreate(TelemetryBase):
    pass

class Telemetry(TelemetryBase):
    id: int
    timestamp: datetime
    is_anomaly: Optional[bool] = False
    predicted_energy: Optional[float] = None
    efficiency: Optional[float] = None
    failure_risk: Optional[float] = None

    class Config:
        from_attributes = True

class GeminiSuggestion(BaseModel):
    insight: str
    recommendation: str
    severity: str
    trend: str
