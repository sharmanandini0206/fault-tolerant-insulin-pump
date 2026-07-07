from fault_tolerant_pump.config import FAULT_TIMEOUT_LIMIT

class PumpState:
    MONITORING      = "MONITORING"
    SENSOR_FAULT    = "SENSOR_FAULT"
    SAFE_FALLBACK   = "SAFE_FALLBACK"
    EMERGENCY_ALARM = "EMERGENCY_ALARM"

class PumpEvent:
    DATA_RECEIVED    = "DATA_RECEIVED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    SENSOR_RESTORED  = "SENSOR_RESTORED"
    FAULT_TIMEOUT    = "FAULT_TIMEOUT"

TRANSITION_TABLE = {
    PumpState.MONITORING: {
        PumpEvent.DATA_RECEIVED:    PumpState.MONITORING,
        PumpEvent.ANOMALY_DETECTED: PumpState.SENSOR_FAULT,
    },
    PumpState.SENSOR_FAULT: {
        PumpEvent.SENSOR_RESTORED:  PumpState.MONITORING,
        PumpEvent.ANOMALY_DETECTED: PumpState.SENSOR_FAULT,
        PumpEvent.FAULT_TIMEOUT:    PumpState.SAFE_FALLBACK,
    },
    PumpState.SAFE_FALLBACK: {
        PumpEvent.SENSOR_RESTORED:  PumpState.MONITORING,
        PumpEvent.FAULT_TIMEOUT:    PumpState.EMERGENCY_ALARM,
        PumpEvent.ANOMALY_DETECTED: PumpState.SAFE_FALLBACK,
    },
    PumpState.EMERGENCY_ALARM: {
        PumpEvent.SENSOR_RESTORED:  PumpState.MONITORING,
    },
}

class PumpFSM:
    """
    Deterministic FSM driving pump operational mode.
    Illegal (state, event) pairs raise immediately rather than silently continuing.
    """
    def __init__(self):
        self._current_state = PumpState.MONITORING
        self.fault_ticks = 0

    @property
    def current_state(self) -> str:
        return self._current_state

    def process_event(self, event: str) -> str:
        state_transitions = TRANSITION_TABLE.get(self._current_state)

        if state_transitions is None:
            raise ValueError(f"CRITICAL: System in unconfigured state: {self._current_state}")

        if event not in state_transitions:
            raise ValueError(
                f"ILLEGAL TRANSITION: State '{self._current_state}' "
                f"does not accept Event '{event}'"
            )

        next_state = state_transitions[event]
        if next_state != self._current_state:
            self._current_state = next_state
            if next_state != PumpState.SENSOR_FAULT:
                self.fault_ticks = 0

        return self._current_state

    def update_fault_timer(self) -> str:
        if self._current_state == PumpState.SENSOR_FAULT:
            self.fault_ticks += 1
            if self.fault_ticks >= FAULT_TIMEOUT_LIMIT:
                return self.process_event(PumpEvent.FAULT_TIMEOUT)

        elif self._current_state == PumpState.SAFE_FALLBACK:
            self.fault_ticks += 1
            if self.fault_ticks >= (FAULT_TIMEOUT_LIMIT * 2):
                return self.process_event(PumpEvent.FAULT_TIMEOUT)

        return self._current_state