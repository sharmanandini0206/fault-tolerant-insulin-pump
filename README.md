# Fault-Tolerant Medical Pump Guard

Modern insulin pumps rely on continuous glucose monitor (CGM) sensors to make dosing decisions. While today's CGM systems are highly accurate, they can still experience temporary signal loss, sensor drift, electrical noise, and communication failures. Because insulin dosing depends directly on these measurements, detecting unreliable sensor data and responding safely is critical.

This project simulates a closed-loop insulin pump using real CGM data from the **GlucoBench: Glucose Monitoring and Lifestyle Data** dataset. By injecting deterministic hardware faults into realistic glucose streams, it evaluates how a safety-critical control system can detect anomalies, transition into safe operating modes, and prevent autonomous insulin delivery based on corrupted sensor inputs.

**Goal:** Explore fault-tolerant software architecture for medical devices by designing a deterministic control system that prioritizes safe degradation, predictable behavior, and reliable failure handling under adverse sensor conditions.

---

## Overview

Modern insulin pumps rely on continuous glucose sensors to make dosing decisions. If sensor data becomes corrupted, delayed, frozen, or disconnected, continuing autonomous insulin delivery can become dangerous.

This project simulates that environment by combining:

* Real clinical CGM datasets
* Synthetic hardware fault injection
* Constant-time statistical anomaly detection
* A deterministic finite state machine (FSM)
* A discrete PID controller
* Automated safety tests

Rather than optimizing glucose control alone, the emphasis is on **fault tolerance**, **safe degradation**, and **predictable system behavior**.

---

## Features

## Real Clinical Data

This project uses the **GlucoBench: Glucose Monitoring and Lifestyle Data** dataset from Kaggle, which contains de-identified continuous glucose monitor (CGM) readings collected at regular intervals.

The simulator streams glucose measurements incrementally rather than loading the entire dataset into memory. Each reading is processed sequentially and interpolated into per-second updates to emulate how an embedded medical device would receive live sensor data.

Using real-world CGM data allows the safety algorithms to be evaluated against realistic glucose trends instead of synthetic signals.

---

### Fault Injection Engine

The telemetry stream can be corrupted using deterministic hardware fault models.

Supported fault modes include:

| Fault             | Description                                         |
| ----------------- | --------------------------------------------------- |
| Sensor Disconnect | Glucose immediately drops to 0 mg/dL                |
| Transient Spike   | Single-frame electrical noise                       |
| Signal Freeze     | Sensor repeats identical values for multiple frames |

These simulate realistic embedded hardware failures without modifying the original dataset.

---

### O(1) Rolling Statistics

A custom circular buffer maintains:

* Running sum
* Running sum of squares
* Fixed-size rolling window

allowing mean and variance to be computed in constant time.

No NumPy or third-party statistics libraries are used.

The detector identifies:

* Sudden physiological drops
* Frozen telemetry
* Excessive signal noise

---

### Deterministic Finite State Machine

System behavior is governed entirely through an immutable transition table.

```
MONITORING
      │
      ▼
SENSOR_FAULT
      │
      ▼
SAFE_FALLBACK
      │
      ▼
EMERGENCY_ALARM
```

Undefined state transitions immediately raise an exception rather than allowing unpredictable behavior.

This guarantees that every operating condition is explicitly defined.

---

### PID Controller

A discrete PID controller computes insulin dose adjustments during normal operation.

Safety constraints include:

* Controller disabled during fault states
* Output clamped to configurable dose limits
* Integral accumulation managed internally
* Zero third-party control libraries

Whenever the FSM exits the monitoring state, insulin delivery is bypassed until safe operation is restored.

---

## Project Structure

```text
fault_tolerant_pump/
│
├── main.py                  # Main simulation loop
├── config.py                # System configuration
│
├── data/
│   └── patient_cgm.csv
│
├── telemetry/
│   ├── parser.py            # CSV streaming & interpolation
│   └── injector.py          # Fault injection
│
├── core/
│   ├── fsm.py               # Finite State Machine
│   ├── pid.py               # PID controller
│   └── stats.py             # O(1) rolling statistics
│
└── tests/
    └── test_safety_bounds.py
```

---

## Safety Architecture

```
Real CGM Data
       │
       ▼
CSV Stream Parser
       │
       ▼
Fault Injection
       │
       ▼
Rolling Statistics
       │
       ▼
Anomaly Detection
       │
       ▼
Finite State Machine
       │
       ├──────────────► Safe Fallback
       │
       ▼
PID Controller
       │
       ▼
Insulin Dose Output
```

---

## Safety Guarantees

The simulator is designed to fail safely.

When corrupted telemetry is detected:

* PID control is immediately suspended
* Previous safe basal delivery is maintained
* Safe fallback mode is entered if faults persist
* Mechanical delivery is halted during emergency conditions
* Undefined transitions are impossible by design

---

## Testing

The project includes automated safety tests covering scenarios such as:

* Invalid or malformed telemetry
* Sensor disconnects
* Frozen sensor readings
* Extreme glucose values
* Illegal FSM transitions
* PID output saturation

The objective is to verify that failures always produce deterministic and safe system behavior.

---

## Technologies

* Python 3
* Dataclasses
* Generators
* Circular buffers
* Finite State Machines
* PID Control
* Unit Testing
* Clinical Time-Series Data

No machine learning frameworks or numerical libraries are required for the core algorithms.

---

## Engineering Concepts Demonstrated

* Safety-critical software design
* Fault-tolerant systems
* Embedded systems architecture
* Real-time data streaming
* Deterministic state machines
* Constant-time statistical algorithms
* Defensive programming
* Control systems engineering
* Software verification through automated testing

---

## Future Improvements

* Multiple concurrent sensor simulation
* Sensor fusion and redundancy
* Model Predictive Control (MPC)
* Interactive dashboard for live telemetry
* Dose history visualization
* Event logging and replay
* Configurable fault scheduling
* Hardware-in-the-loop simulation

---

## Disclaimer

This project is intended **for educational and research purposes only**.

It is **not** a medical device and must never be used for diagnosis, treatment, or real insulin dosing decisions.
