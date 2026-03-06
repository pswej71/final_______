from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from database import Base
import datetime

class InverterTelemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    # Internal metrics
    voltage = Column(Float)
    current = Column(Float)
    power = Column(Float)
    energy = Column(Float)
    frequency = Column(Float)
    temperature = Column(Float)
    status = Column(String) # Normal, Fault, Warning
    
    # External metrics
    solar_irradiance = Column(Float)
    ambient_temperature = Column(Float)
    dust_index = Column(Float)
    air_quality_index = Column(Float)
    
    # ML Outputs
    is_anomaly = Column(Boolean, default=False)
    predicted_energy = Column(Float, nullable=True)
    efficiency = Column(Float, nullable=True)
    failure_risk = Column(Float, nullable=True)
