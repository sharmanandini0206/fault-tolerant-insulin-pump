import csv
from datetime import datetime
from dataclasses import dataclass

@dataclass(frozen=True)
class SensorFrame:
    timestamp: float
    glucose: float

def read_cgm_stream(file_path: str):
    """
    Reads a clinical CGM CSV line-by-line via a memory-efficient generator.
    Parses timestamps and glucose values, drops invalid rows, and performs
    linear interpolation to scale 5-minute clinical readings to 1-second ticks.
    Expected CSV columns: 'timestamp' (YYYY-MM-DD HH:MM:SS), 'glucose' (float mg/dL)
    """
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        prev_frame = None
        for row in reader:
            try:
                raw_time    = row['timestamp'].strip()
                raw_glucose = row['glucose'].strip()

                if not raw_time or not raw_glucose:
                    continue

                dt = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
                current_time    = dt.timestamp()
                current_glucose = float(raw_glucose)
                current_frame   = SensorFrame(timestamp=current_time, glucose=current_glucose)

                if prev_frame is None:
                    yield current_frame
                    prev_frame = current_frame
                    continue

                time_delta = current_frame.timestamp - prev_frame.timestamp

                if time_delta <= 0:
                    continue

                step    = 1.0
                elapsed = step
                while elapsed < time_delta:
                    fraction       = elapsed / time_delta
                    interp_glucose = prev_frame.glucose + fraction * (current_frame.glucose - prev_frame.glucose)
                    interp_time    = prev_frame.timestamp + elapsed
                    yield SensorFrame(timestamp=interp_time, glucose=interp_glucose)
                    elapsed += step

                yield current_frame
                prev_frame = current_frame

            except (ValueError, KeyError):
                continue

parse_cgm_stream = read_cgm_stream