import logging
import datetime
import pandas as pd
import numpy as np
from typing import List, Dict, Any

# Configure health logging
logging.basicConfig(
    filename='system_health.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SystemHealth")

class DataIntegrityChecker:
    """Validates telemetry data for range violations, staleness, and stuck sensors."""
    def __init__(self, voltage_range=(0, 1000), power_range=(0, 15000), temp_range=(0, 100)):
        self.voltage_range = voltage_range
        self.power_range = power_range
        self.temp_range = temp_range

    def check_ranges(self, data: Dict[str, Any]) -> List[str]:
        violations = []
        if not (self.voltage_range[0] <= data.get('voltage', 0) <= self.voltage_range[1]):
            violations.append(f"Voltage out of range: {data.get('voltage')}V")
        if not (self.power_range[0] <= data.get('power', 0) <= self.power_range[1]):
            violations.append(f"Power out of range: {data.get('power')}W")
        if not (self.temp_range[0] <= data.get('temperature', 0) <= self.temp_range[1]):
            violations.append(f"Temperature out of range: {data.get('temperature')}°C")
        return violations

    def check_staleness(self, latest_timestamp: datetime.datetime, threshold_seconds=600) -> bool:
        """Returns True if data is older than threshold."""
        delta = (datetime.datetime.utcnow() - latest_timestamp).total_seconds()
        return delta > threshold_seconds

    def check_stuck_sensors(self, history: List[Dict[str, Any]], window_size=10) -> List[str]:
        """Checks if sensors have zero variance over the last window_size samples."""
        if len(history) < window_size:
            return []
            
        df = pd.DataFrame(history[-window_size:])
        stuck = []
        for col in ['voltage', 'current', 'temperature']:
            if col in df.columns and df[col].std() < 1e-4:
                stuck.append(col)
        return stuck

class StatusMonitor:
    def __init__(self):
        self.checker = DataIntegrityChecker()
        self.last_status = {
            "is_healthy": True,
            "integrity_score": 100,
            "violations": [],
            "staleness_detected": False,
            "stuck_sensors": [],
            "last_check": datetime.datetime.utcnow().isoformat()
        }

    def evaluate_health(self, latest_telemetry: Dict[str, Any], history: List[Dict[str, Any]]):
        violations = self.checker.check_ranges(latest_telemetry)
        
        # Check staleness if timestamp exists
        ts = latest_telemetry.get('timestamp')
        if isinstance(ts, str):
            ts = datetime.datetime.fromisoformat(ts.replace('Z', ''))
        
        staleness = False
        if ts:
            staleness = self.checker.check_staleness(ts)
            
        stuck = self.checker.check_stuck_sensors(history)
        
        # Calculate score (simple penalty system)
        score = 100 - (len(violations) * 10) - (20 if staleness else 0) - (len(stuck) * 15)
        score = max(0, score)
        
        self.last_status = {
            "is_healthy": score > 70,
            "integrity_score": score,
            "violations": violations,
            "staleness_detected": staleness,
            "stuck_sensors": stuck,
            "last_check": datetime.datetime.utcnow().isoformat()
        }
        
        if not self.last_status["is_healthy"]:
            logger.warning(f"Health check failed: {self.last_status}")
        else:
            logger.info(f"Health check passed: Score {score}")
            
        return self.last_status

monitor = StatusMonitor()
