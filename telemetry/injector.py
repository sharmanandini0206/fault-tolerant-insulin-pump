import random
from fault_tolerant_pump.telemetry.parser import SensorFrame
from fault_tolerant_pump.config import FAULT_CONFIGS

def inject_hardware_faults(clean_stream):
    """
    Wraps a clean SensorFrame generator and injects hardware failure modes
    at configured elapsed-second windows defined in config.FAULT_CONFIGS.
    """
    elapsed_seconds = 0
    frozen_value    = None

    for frame in clean_stream:
        elapsed_seconds += 1

        cfg_spike = FAULT_CONFIGS["TRANSIENT_SPIKE"]
        if cfg_spike["start"] <= elapsed_seconds <= cfg_spike["end"]:
            corrupted = frame.glucose + cfg_spike["magnitude"]
            yield SensorFrame(timestamp=frame.timestamp, glucose=round(corrupted, 4))
            continue

        cfg_freeze = FAULT_CONFIGS["SIGNAL_FREEZE"]
        if cfg_freeze["start"] <= elapsed_seconds <= cfg_freeze["end"]:
            if frozen_value is None:
                frozen_value = frame.glucose
            yield SensorFrame(timestamp=frame.timestamp, glucose=frozen_value)
            continue
        else:
            frozen_value = None

        cfg_drop = FAULT_CONFIGS["SENSOR_DISCONNECT"]
        if cfg_drop["start"] <= elapsed_seconds <= cfg_drop["end"]:
            yield SensorFrame(timestamp=frame.timestamp, glucose=0.0)
            continue

        yield frame

fault_injector_stream = inject_hardware_faults