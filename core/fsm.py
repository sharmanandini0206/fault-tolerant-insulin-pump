from fault_tolerant_pump.config import FAULT_TIMEOUT_LIMIT

class PumpState:
    MONITORING = "MONITORING"
    SENSOR_FAULT = "SENSOR_FAULT"
    SAFE_FALLBACK = "SAFE_FALLBACK"
    EMERGENCY_ALARM = "EMERGENCY_ALARM"

class PumpEvent:
    DATA_RECEIVED = "DATA_RECEIVED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    SENSOR_RESTORED = "SENSOR_RESTORED"
    FAULT_TIMEOUT = "FAULT_TIMEOUT"

# Hardened Immutable State Transition Lookup Matrix
TRANSITION_TABLE = {
    PumpState.MONITORING: {
        PumpEvent.DATA_RECEIVED: PumpState.MONITORING,
        PumpEvent.ANOMALY_DETECTED: PumpState.SENSOR_FAULT,
    },
    PumpState.SENSOR_FAULT: {
        PumpEvent.SENSOR_RESTORED: PumpState.MONITORING,
        PumpEvent.ANOMALY_DETECTED: PumpState.SENSOR_FAULT,
        PumpEvent.FAULT_TIMEOUT: PumpState.SAFE_FALLBACK,
    },
    PumpState.SAFE_FALLBACK: {
        PumpEvent.SENSOR_RESTORED: PumpState.MONITORING,
        PumpEvent.FAULT_TIMEOUT: PumpState.EMERGENCY_ALARM,
    },
    PumpState.EMERGENCY_ALARM: {
        PumpEvent.SENSOR_RESTORED: PumpState.EMERGENCY_ALARM,
    },
}

class PumpFSM:
    """
    A deterministic Finite State Machine that drives the operational mode 
    of the pump and safeguards against illegal state changes.
    """
    def __init__(self):
        self._current_state = PumpState.MONITORING
        self.fault_ticks = 0

    @property
    def current_state(self) -> str:
        return self._current_state

    def process_event(self, event: str) -> str:
        """
        Transitions the system state via the lookup table based on incoming events.
        Raises an explicit ValueError if an illegal state transition is attempted.
        """
        state_transitions = TRANSITION_TABLE.get(self._current_state)
        
        # Defensive check: verify the current state exists in our schema
        if state_transitions is None:
            raise ValueError(f"CRITICAL: System is in an unconfigured state: {self._current_state}")

        if event not in state_transitions:
            raise ValueError(
                f"ILLEGAL TRANSITION TRIED: State '{self._current_state}' "
                f"does not accept Event '{event}'"
            )

        next_state = state_transitions[event]
        
        if next_state != self._current_state:
            # State change occurred
            self._current_state = next_state
            # Reset the fault tracking clock if transitioning out of SENSOR_FAULT
            if next_state != PumpState.SENSOR_FAULT:
                self.fault_ticks = 0

        return self._current_state

    def update_fault_timer(self) -> str:
        """
        Increments the consecutive fault execution loop count. If the threshold 
        is passed, it automatically steps down to the next graceful fallback state.
        """
        if self._current_state == PumpState.SENSOR_FAULT:
            self.fault_ticks += 1
            if self.fault_ticks >= FAULT_TIMEOUT_LIMIT:
                return self.process_event(PumpEvent.FAULT_TIMEOUT)
                
        elif self._current_state == PumpState.SAFE_FALLBACK:
            self.fault_ticks += 1
            # If the fallback state stays blinded for an extended period, trigger emergency stop
            if self.fault_ticks >= (FAULT_TIMEOUT_LIMIT * 2):
                return self.process_event(PumpEvent.FAULT_TIMEOUT)

        return self._current_state