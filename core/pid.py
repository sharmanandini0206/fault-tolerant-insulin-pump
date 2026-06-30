from fault_tolerant_pump.config import (
    GLUCOSE_SETPOINT, 
    KP, KI, KD, 
    MAX_DOSE_CEILING, 
    DEFAULT_BASAL_RATE
)
from fault_tolerant_pump.core.fsm import PumpState

class InsulinPIDController:
    """
    A discrete PID control loop engineered without external mathematical libraries.
    Features safety clamping limits to prevent integral windup.
    """
    def __init__(self):
        # get coefficients mapped from core config
        self.kp = KP
        self.ki = KI
        self.kd = KD
        self.setpoint = GLUCOSE_SETPOINT

        # controller state variables
        self.integral_err = 0.0
        self.prev_error = None

    def calculate_dose(self, current_glucose: float, current_state: str, delta_t: float = 1.0) -> float:
        """
        Calculates the required insulin adjustment based on a target setpoint.
        Enforces system safety overrides if the state is anything other than MONITORING.
        """
        # Safety gate 1: if the sensor environment is corrupted, instantly bypass PID calculations
        if current_state != PumpState.MONITORING:
            return 0.0

        # calculate tracking error (positive means glucose is over the 100 mg/dL target)
        error = current_glucose - self.setpoint

        # 1. Proportional term (immediate correction response)
        p_term = self.kp * error

        # 2. Integral term (accumulates over time to resolve steady-state error offset)
        self.integral_err += error * delta_t
        
        # Anti-windup guardrail: clamp the total integral term calculation to bounds
        # preventing systemic error accumulation from overwhelming the engine profile
        integral_max_clip = MAX_DOSE_CEILING / (self.ki if self.ki > 0 else 1.0)
        self.integral_err = max(-integral_max_clip, min(self.integral_err, integral_max_clip))
        i_term = self.ki * self.integral_err

        # 3. Derivative term (rates of change tracking to counter future drops/spikes)
        if self.prev_error is None:
            d_term = 0.0
        else:
            d_term = self.kd * ((error - self.prev_error) / delta_t)

        # Store error baseline for next iteration loop reference point
        self.prev_error = error

        # Combine terms and add the baseline system background delivery value
        calculated_output = DEFAULT_BASAL_RATE + p_term + i_term + d_term

        # Safety gate 2: clamp the final dosage limits between complete cessation and maximum allowed delivery
        final_safe_dose = max(0.0, min(calculated_output, MAX_DOSE_CEILING))
        return round(final_safe_dose, 4)

    def reset(self) -> None:
        """Clears memory vectors to avoid historical leakage when system auto-recovers."""
        self.integral_err = 0.0
        self.prev_error = None