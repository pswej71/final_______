import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_telemetry_csv(rows=1000, output_path="d:/Aubegine/data/historical_telemetry.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    start_time = datetime.now() - timedelta(days=30)
    data = []
    
    for i in range(rows):
        timestamp = start_time + timedelta(minutes=15 * i)
        
        # Simulate daylight curve (roughly 6 AM to 6 PM)
        hour = timestamp.hour
        if 6 <= hour <= 18:
            irradiance = random.uniform(200, 1000) * np.sin(np.pi * (hour - 6) / 12)
        else:
            irradiance = 0
            
        power = irradiance * random.uniform(8, 10) if irradiance > 0 else 0
        energy = power * 0.25 / 1000 # 15 min interval in kWh
        
        # Inject some faults/anomalies (5% chance)
        is_fault = random.random() < 0.05
        if is_fault:
            power = power * random.uniform(0.1, 0.4) # Severe drop
            
        row = {
            "timestamp": timestamp.isoformat(),
            "voltage": random.uniform(210, 240) if power > 0 else 0,
            "current": power / 220 if power > 0 else 0,
            "power": power,
            "energy": energy,
            "frequency": random.uniform(49.8, 50.2) if power > 0 else 0,
            "temperature": random.uniform(30, 60) if power > 0 else random.uniform(15, 25),
            "status": "Fault" if is_fault else "Normal",
            "solar_irradiance": irradiance,
            "ambient_temperature": random.uniform(20, 45),
            "dust_index": random.uniform(0, 100),
            "air_quality_index": random.uniform(20, 150)
        }
        data.append(row)
        
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Generated {rows} rows of mock data saved to {output_path}")

if __name__ == "__main__":
    generate_telemetry_csv()
