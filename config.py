# --- Physiological and Safety Bounds ---
GLUCOSE_SETPOINT = 100.0       # Target baseline (mg/dL)
MIN_SAFE_GLUCOSE = 70.0        # FIXED: Raised from 40.0 to 70.0 mg/dL for clinical safety (Predictive Low Suspension)
MAX_SAFE_GLUCOSE = 400.0       # Hard physiological upper bound (mg/dL) - Severe Hyperglycemia

# --- FSM & Anomaly Windows ---
STATS_WINDOW_SIZE = 15         # Moving circular buffer tracking window size
# Note: Retained short windows optimized for the accelerated 1-second simulation tick loop.
FAULT_TIMEOUT_SECONDS = 30     # Max seconds allowed in SENSOR_FAULT before SAFE_FALLBACK
FALLBACK_TIMEOUT_SECONDS = 60  # Max seconds allowed in SAFE_FALLBACK before EMERGENCY_ALARM

# --- Safety Core Basal Rates ---
DEFAULT_BASAL_RATE = 1.0       # Standard default dosage (units/hour)
SAFE_FALLBACK_RATE = 0.5       # Safe hardcoded micro-dose under degraded operation (units/hour)
MAX_DOSE_CEILING = 3.0         # Hard clipping limit for autonomous PID delivery

# --- PID Math Engine Parameters ---
# Derivative gain (KD) is dampened to prevent sensor noise/jitters from causing erratic spikes.
KP = 0.15                      # Proportional gain (dominant response driver)
KI = 0.001                     # Integral gain (slow steady-state error correction)
KD = 0.01                      # Derivative gain (dampened to shield against high-frequency noise)

# --- Fault Injection Timelines (Simulated Elapsed Seconds) ---
# Specific windows where hardware physical connections or readings deteriorate
FAULT_CONFIGS = {
    "TRANSIENT_SPIKE": {"start": 10, "end": 12, "magnitude": 50.0},
    "SIGNAL_FREEZE": {"start": 40, "end": 60},
    "SENSOR_DISCONNECT": {"start": 90, "end": 110}
}