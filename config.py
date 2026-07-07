# --- Physiological and Safety Bounds ---
GLUCOSE_SETPOINT = 100.0       # Target baseline (mg/dL)
MIN_SAFE_GLUCOSE = 70.0        # Raised from 40.0 for Predictive Low Suspension
MAX_SAFE_GLUCOSE = 400.0       # Hard physiological upper bound (mg/dL)

# --- FSM & Anomaly Windows ---
STATS_WINDOW_SIZE = 15
FAULT_TIMEOUT_SECONDS = 30
FALLBACK_TIMEOUT_SECONDS = 60

# FIX: fsm.py imports FAULT_TIMEOUT_LIMIT but only FAULT_TIMEOUT_SECONDS was defined.
FAULT_TIMEOUT_LIMIT = FAULT_TIMEOUT_SECONDS

# --- Safety Core Basal Rates ---
DEFAULT_BASAL_RATE = 1.0
SAFE_FALLBACK_RATE = 0.5
MAX_DOSE_CEILING = 3.0

# --- PID Parameters ---
KP = 0.15
KI = 0.001
KD = 0.01

# FIX: main.py imports DATA_FILE_PATH but it was never defined anywhere.
import os
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "data", "patient_cgm.csv")

# --- Fault Injection Timelines ---
FAULT_CONFIGS = {
    "TRANSIENT_SPIKE":   {"start": 10, "end": 12,  "magnitude": 50.0},
    "SIGNAL_FREEZE":     {"start": 40, "end": 60},
    "SENSOR_DISCONNECT": {"start": 90, "end": 110},
}