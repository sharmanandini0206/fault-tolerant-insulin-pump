import random
from fault_tolerant_pump.telemetry.parser import SensorFrame
from fault_tolerant_pump.config import FAULT_CONFIGS

def inject_hardware_faults(clean_stream):
    '''
    Wraps an incoming clean SensorFrame stream and injects
    hardware errors based on elapsed operational second counters.
    '''
    elapsed_seconds = 0
    frozen_value = None

    for frame in clean_stream:
        elapsed_seconds += 1
        
        # 1. TRANSIENT_SPIKE : Simulates electromagnetic motor interference
        cfg_spike = FAULT_CONFIGS["TRANSIENT_SPIKE"]
        if cfg_spike["start"] <= elapsed_seconds <= cfg_spike["end"]:
            # Add a major positive anomaly to a single frame packet
            corrupted_glucose = frame.glucose + cfg_spike["magnitude"]
            yield SensorFrame(timestamp=frame.timestamp, glucose=round(corrupted_glucose, 4))
            continue

        # 2. SIGNAL_FREEZE : Simulates a locked memory bus or firmware crash
        cfg_freeze = FAULT_CONFIGS["SIGNAL_FREEZE"]
        if cfg_freeze["start"] <= elapsed_seconds <= cfg_freeze["end"]:
            if frozen_value is None:
                frozen_value = frame.glucose
            yield SensorFrame(timestamp=frame.timestamp, glucose=frozen_value)
            continue
        else:
            # Clear frozen state memory container once out of the window bounds
            frozen_value = None

        # 3. SENSOR_DISCONNECT : Simulates physical detachment or wire rupture
        cfg_drop = FAULT_CONFIGS["SENSOR_DISCONNECT"]
        if cfg_drop["start"] <= elapsed_seconds <= cfg_drop["end"]:
            # Drop reading instantly to zero volts/physiological null
            yield SensorFrame(timestamp=frame.timestamp, glucose=0.0)
            continue

        # Nominal Condition : Pass through unaffected frame
        yield frame