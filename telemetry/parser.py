import csv
from datetime import datetime
from dataclasses import dataclass

@dataclass(frozen=True)
class SensorFram:
    timestamp: float
    glucose: float

def read_cgm_stream(file_path: str) :
    # read clinical CSV file line by line using memory efficient generator
    # parses timestamps and glucose entries, drops invalid records, and performs
    # linear interpolation to scale irregular mutli-minute steps into 1 sec ticks

# Verification
if __name__ == "__main__":
    import os
    
    # Trace path relative to current workspace root
    data_path = "fault_tolerant_pump/data/patient_cgm.csv"
    
    if os.path.exists(data_path):
        print("Starting Data Ingestion Telemetry Stream test...")
        stream = read_cgm_stream(data_path)
        
        # Pull and look at the first 10 seconds of simulated operations
        for i in range(10):
            try:
                frame = next(stream)
                print(f"Tick {i+1:02d} | Timestamp: {frame.timestamp} | Glucose: {frame.glucose:.4f} mg/dL")
            except StopIteration:
                print("Stream completed prematurely.")
                break
    else:
        print(f"Error: Target data file not found at {data_path}. Verify layout paths.")