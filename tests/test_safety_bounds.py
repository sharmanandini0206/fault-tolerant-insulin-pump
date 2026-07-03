import unittest
from fault_tolerant_pump.config import MAX_DOSE_CEILING, STATS_WINDOW_SIZE
from fault_tolerant_pump.core.fsm import PumpFSM, PumpState, PumpEvent
from fault_tolerant_pump.core.pid import InsulinPIDController
from fault_tolerant_pump.core.stats import RollingStatsTracker

class TestPumpSafetyBounds(unittest.TestCase):
    """
    automated safety validation suite verifying algorithmic stability,
    hard boundary constraints, and error containment zones.
    """
    def setUp(self):
        self.fsm = PumpFSM()
        self.pid = InsulinPIDController()
        self.tracker = RollingStatsTracker(window_size=STATS_WINDOW_SIZE)

    def test_overflow_injection_guardrail(self):
        """
        safety Test: Asserts that an extreme glycemic value cannot trick 
        the controller into exceeding the strict maximum dose delivery limits.
        """
        extreme_glucose = 999.0
        
        #calculate dose during normal monitoring mode
        output_dose = self.pid.calculate_dose(extreme_glucose, PumpState.MONITORING)
        
        self.assertTrue(
            output_dose <= MAX_DOSE_CEILING,
            f"SAFETY FAILURE: Controller exceeded maximum allowance ceiling! Output: {output_dose}"
        )
        self.assertEqual(output_dose, MAX_DOSE_CEILING)

    def test_zero_drop_disconnect_detection(self):
        """
        safety Test: Asserts that a sudden physical sensor disconnect (0.0 mg/dL)
        immediately triggers a SIGNAL_DROPPED anomaly signature on the first frame.
        """
        dropped_glucose = 0.0
        
        # analyze reading through stats buffer
        signature = self.tracker.analyze_anomaly(dropped_glucose)
        self.assertEqual(signature, "SIGNAL_DROPPED")
        
        # dispatch event to the FSM and verify safe routing to fault containment mode
        next_state = self.fsm.process_event(PumpEvent.ANOMALY_DETECTED)
        self.assertEqual(next_state, PumpState.SENSOR_FAULT)

    def test_firmware_freeze_detection(self):
        """
        safety Test: Asserts that a frozen telemetry transmission pipeline 
        collapses sliding variance to exactly 0.0 and transitions out of monitoring.
        """
        static_glucose = 125.4
        
        # feed identical readings to satisfy full capacity of the window
        for _ in range(STATS_WINDOW_SIZE):
            self.tracker.update(static_glucose)
            
        signature = self.tracker.analyze_anomaly(static_glucose)
        self.assertEqual(signature, "TELEMETRY_FROZEN")
        self.assertEqual(self.tracker.variance, 0.0)

    def test_illegal_transition_lockout(self):
        """
        safety Test: Asserts that an undefined or illegal transition sequence 
        causes an immediate exception rather than letting the device run corrupted.
        """
        # step into fallback mode
        self.fsm.process_event(PumpEvent.ANOMALY_DETECTED)
        self.fsm.process_event(PumpEvent.FAULT_TIMEOUT)
        self.assertEqual(self.fsm.current_state, PumpState.SAFE_FALLBACK)
        
        # it is illegal to step from SAFE_FALLBACK back to standard operations 
        # without explicitly clearing anomalies via a SENSOR_RESTORED token.
        with self.assertRaises(ValueError):
            self.fsm.process_event(PumpEvent.DATA_RECEIVED)

    def test_pid_bypass_on_fault(self):
        """
        safety Test: Asserts that the controller completely cuts off active PID math 
        and sets output to 0.0 immediately when a non-monitoring state is active.
        """
        hyperglycemia_glucose = 250.0
        
        # ensure standard calculations are working normally first
        active_dose = self.pid.calculate_dose(hyperglycemia_glucose, PumpState.MONITORING)
        self.assertTrue(active_dose > 0.0)
        
        # confirm complete calculation bypass when a fault state takes over
        safe_bypassed_dose = self.pid.calculate_dose(hyperglycemia_glucose, PumpState.SENSOR_FAULT)
        self.assertEqual(safe_bypassed_dose, 0.0)

if __name__ == "__main__":
    unittest.main()