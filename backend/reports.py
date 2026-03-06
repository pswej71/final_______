import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from gemini_service import get_suggestions

class MaintenanceReporter:
    def __init__(self, db_session):
        self.db = db_session

    def generate_report(self, days: int = 7) -> Dict[str, Any]:
        """Aggregates historical data and generates a maintenance report."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # In a real app, import models here to avoid circular imports or use session directly
        from db_models import InverterTelemetry
        
        history = self.db.query(InverterTelemetry).filter(
            InverterTelemetry.timestamp >= cutoff_date
        ).order_by(InverterTelemetry.timestamp.asc()).all()
        
        if not history:
            return {"error": "No data found for the specified period."}
            
        df = pd.DataFrame([h.__dict__ for h in history])
        df.pop('_sa_instance_state', None)
        
        # Calculate summary metrics
        avg_efficiency = df['efficiency'].mean()
        max_risk = df['failure_risk'].max()
        peak_risk_time = df.loc[df['failure_risk'].idxmax(), 'timestamp'] if not df.empty else None
        
        anomalies_count = len(df[df['is_anomaly'] == True])
        
        # Prepare context for AI
        summary_context = {
            "period_days": days,
            "avg_efficiency": float(avg_efficiency),
            "max_failure_risk": float(max_risk),
            "peak_risk_timestamp": peak_risk_time.isoformat() if peak_risk_time else None,
            "total_anomalies": anomalies_count,
            "data_points": len(df)
        }
        
        # Generate AI recommendations using the existing gemini_service
        # We'll repurpose get_suggestions with specific reporting context
        report_prompt = f"""
        Generate a Maintenance Recommendation Report for a Solar Inverter based on the following 7-day summary:
        - Average Efficiency: {avg_efficiency:.2f}%
        - Peak Failure Risk: {max_risk*100:.1f}%
        - Detected Anomalies: {anomalies_count}
        - Total Readings: {len(df)}
        
        Provide:
        1. Executive Summary
        2. Technical Analysis of Risk Trends
        3. Priority Action Items for Technicians
        4. Preventive Maintenance Schedule
        """
        
        # We call Gemini with this specific prompt
        ai_report = get_suggestions(telemetry_data=df.tail(20).to_dict('records'), alerts=[f"Peak Risk: {max_risk:.2f}"])
        
        return {
            "metadata": summary_context,
            "report_content": ai_report,
            "generated_at": datetime.utcnow().isoformat()
        }
