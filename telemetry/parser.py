import csv
from datetime import datetime
from dataclasses import dataclass

@dataclass(frozen=True)
class SensorFrame:
    timestamp: float
    glucose: float

def read_cgm_stream(file_path: str) :
    # read clinical CSV file line by line using memory efficient generator
    # parses timestamps and glucose entries, drops invalid records, and performs
    # linear interpolation to scale irregular mutli-minute steps into 1 sec ticks
    with open(file_path, mode='r', encoding='utf-8') as f :
        reader = csv.DictReader(f)
        prev_frame = None
        for row in reader :
            try :
                # 1. parse fields using headers from Kaggle : GlucoBench
                raw_time = row['timestamp'].strip()
                raw_glucose = row['glucose'].strip()

                if not raw_time or not raw_glucose :
                    continue

                # convert ISO string format "YYYY-MM-DD HH:MM:SS" to a Unix epoch float
                dt = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
                current_time = dt.timestamp()
                current_glucose = float(raw_glucose)
                current_frame = SensorFrame(timestamp=current_time, glucose=current_glucose)

                # 2. if this is very first row, yield it
                if prev_frame is None :
                    yield current_frame
                    prev_frame = current_frame
                    continue

                # 3. calculate interval for time series interpolation
                time_delta = current_frame.timestamp - prev_frame.timestamp

                # check for reversed timestamps or simultaneous frames
                if time_delta <= 0 :
                    continue

                # 4. interpolate steps at a 1 second internal system interrup clock rate
                step = 1.0
                elapsed = step
                while elapsed < time_delta :
                    fraction = elapsed / time_delta
                    interp_glucose = prev_frame.glucose + fraction *(current_frame.glucose - prev_frame.glucose)
                    interp_time = prev_frame.timestamp + elapsed
                    yield SensorFrame(timestamp=interp_time, glucose=interp_glucose)
                    elapsed += step

                #5. yield canonical clinical anchor reading at the end of the interval
                yield current_frame
                prev_frame = current_frame
            
            except (ValueError, KeyError) :
                continue
'''
# Verification
if __name__ == "__main__":
    import os
    
    # trace path relative to current workspace root
    data_path = "fault_tolerant_pump/data/patient_cgm.csv"
    
    if os.path.exists(data_path):
        print("Starting Data Ingestion Telemetry Stream test...")
        stream = read_cgm_stream(data_path)
        
        # pull and look at the first 10 seconds of simulated operations
        for i in range(10):
            try:
                frame = next(stream)
                print(f"Tick {i+1:02d} | Timestamp: {frame.timestamp} | Glucose: {frame.glucose:.4f} mg/dL")
            except StopIteration:
                print("Stream completed prematurely.")
                break
    else:
        print(f"Error: Target data file not found at {data_path}. Verify layout paths.")
'''