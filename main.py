import sys
import time
from fault_tolerant_pump.config import (
    DATA_FILE_PATH,
    STATS_WINDOW_SIZE,
    DEFAULT_BASAL_RATE,
    SAFE_FALLBACK_RATE
)
from fault_tolerant_pump.telemetry.parser import parse_cgm_stream
from fault_tolerant_pump.telemetry.injector import fault_injector_stream
from fault_tolerant_pump.core.stats import RollingStatsTracker
from fault_tolerant_pump.core.fsm import PumpFSM, PumpState, PumpEvent
from fault_tolerant_pump.core.pid import InsulinPIDController

def run_system_simulator():
    print("======================================================================")
    print("      INITIALIZING FAULT-TOLERANT MEDICAL PUMP GUARD SIMULATOR        ")
    print("======================================================================\n")

    # 1. Instantiate Core Engine Architectures
    try:
        raw_stream = parse_cgm_stream(DATA_FILE_PATH)
        corrupted_stream = fault_injector_stream(raw_stream)
    except FileNotFoundError:
        print(f"CRITICAL ERROR: Sourced dataset file not found at: '{DATA_FILE_PATH}'")
        print("Please check your configuration path configuration settings.")
        sys.exit(1)

    tracker = RollingStatsTracker(window_size=STATS_WINDOW_SIZE)
    fsm = PumpFSM()
    pid = InsulinPIDController()

    print(f"[*] Core components online. Active State Target: {fsm.current_state}")
    print("[*] Streaming real-time micro-dose evaluation logs below...\n")
    print(f"{'Timestamp (s)':<15}{'Raw Glucose':<15}{'Sensor Bus':<15}{'System State':<20}{'Insulin Dose (U/h)':<18}")
    print("-" * 83)

    # 2. Start Closed-Loop Runtime Execution Bus
    frame_count = 0
    
    try:
        for frame in corrupted_stream:
            frame_count += 1
            
            # Extract values from immutable sensor packets
            timestamp = frame.timestamp
            current_reading = frame.glucose

            # Update rolling statistics variance registers (O(1) updates)
            tracker.update(current_reading)
            
            # 3. Dynamic Real-Time Anomaly Analysis Block
            anomaly_signature = tracker.analyze_anomaly(current_reading)
            
            # Determine state machine trigger transitions
            if anomaly_signature is not None:
                event = PumpEvent.ANOMALY_DETECTED
            else:
                event = PumpEvent.DATA_RECEIVED

            # Route event to FSM and capture updated operational state
            try:
                active_state = fsm.process_event(event)
            except ValueError as fsm_err:
                print(f"\n[CRITICAL RUNTIME EXCEPTION TRAYS]: {fsm_err}")
                print("[!] HARD LOCKOUT ENGAGED: Halting mechanical actuator safety arrays instantly.")
                break

            # Process fault clock timers if trapped inside hardware degradation states
            active_state = fsm.update_fault_timer()

            # 4. Actuator Delivery Allocation Logic
            if active_state == PumpState.MONITORING:
                # Continuous loop closed control calculation mode
                calculated_dose = pid.calculate_dose(current_reading, active_state)
            elif active_state == PumpState.SENSOR_FAULT:
                # Hold delivery static at safe baseline tracking rates
                calculated_dose = DEFAULT_BASAL_RATE
            elif active_state == PumpState.SAFE_FALLBACK:
                # Mitigate risk profile with hardcoded minimum basal profiles
                calculated_dose = SAFE_FALLBACK_RATE
            elif active_state == PumpState.EMERGENCY_ALARM:
                # Catastrophic system hardware isolation loop trigger
                calculated_dose = 0.0

            # 5. Output Telemetry Matrix Log Arrays
            # Format inputs gracefully for monitoring
            raw_glucose_str = f"{frame.glucose:.1f}" if frame.glucose > 0 else "0.0"
            
            print(f"{timestamp:<15.1f}{raw_glucose_str:<15}{anomaly_signature or 'CLEAN':<15}{active_state:<20}{calculated_dose:<18.4f}")

            # Artificially limit loop speed to human-readable interval loops if testing locally
            # time.sleep(0.05) 

    except KeyboardInterrupt:
        print("\n\n[!] Simulation terminated safely via user keyboard interrupt command structure.")
    
    print("\n======================================================================")
    print(f"  SIMULATION STOPPED. TOTAL EVALUATED TELEMETRY PACETS: {frame_count}")
    print("======================================================================")

