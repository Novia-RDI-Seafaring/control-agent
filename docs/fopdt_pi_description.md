# FOPDT PI Controller FMU

## Overview

This FMU (`fopd_pi.fmu`) represents a **First-Order Plus Dead-Time (FOPDT)** process controlled by a **PI controller**.  
It was exported from MATLAB®/Simulink® R2024b as a **Co-Simulation FMU (FMI 2.0)** for development, testing, and integration in external simulation environments.

The FMU can operate in two modes:

- **Automatic mode** (`mode = true`):  
  The internal PI controller controls the process output to the a setpoint.
- **Manual mode** (`mode = false`):  
  The controller is bypassed and a manual control signal that is directly applied to the process.

## I/O Description

### Inputs

| Name        | Type   | Unit | Default | Description |
|--------------|--------|------|----------|-------------|
| `setpoint`   | Real   | —    | 0.0 | Controller setpoint signal. Active when the controller is in automatic mode. |
| `u_manual`   | Real   | —    | 0.0 | Manual control signal. Active when the controller is in manual mode. |

### Outputs

| Name | Type | Unit | Default | Description |
|------|------|------|----------|-------------|
| `y`  | Real | — | 0.0 | Process output signal. |
| `u`  | Real | — | 0.0 | Controller output (control effort). |

---

## Tunable Parameters

| Name  | Type     | Unit | Default | Description |
|-------|-----------|------|----------|-------------|
| `K`   | Real     | —    | 1.0 | Process gain — defines how strongly the process output responds to input changes. |
| `T`   | Real     | —     | 2.0 | Process time constant — determines how quickly the process reacts to changes. |
| `L`   | Real     | —     | 1.0 | Process dead time — delay between control action and process response. |
| `Kp`  | Real     | —    | 1.0 | PI controller proportional gain — amplifies the control error. |
| `Ti`  | Real     | —     | 1.0 | PI controller integral time constant — controls how quickly steady-state error is eliminated. |
| `mode`| Boolean  | —    | `false` *(manual)* | Controller mode flag: `false = manual`, `true = automatic`. |



## Model Summary

| Feature              | Description |
|-----------------------|-------------|
| **FMU Type**          | Co-Simulation (FMI 2.0) |
| **Model Name**        | `fopd_pi` |
| **Exported From**     | Simulink R2024b |
| **Solver**            | Discrete fixed-step |
| **Default Stop Time** | 60 s |
| **Sample Time**       | 0.1 s |
