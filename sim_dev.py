# pip install fmpy matplotlib
from math import inf
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from fmpy import read_model_description, simulate_fmu

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
fmu_path = Path("models/fmus/fopd_pi.fmu").as_posix()


step_time = 10.0             # seconds
step_level = 2.0             # step magnitude

# Controller parameters
CONTROLLER_MODE = True       # True = automatic, False = manual
KP_VALUE = 1                 # proportional gain
TI_VALUE = 2                 # integral time constant [s]
# -------------------------------------------------------------------------

# --- Read FMU metadata ----------------------------------------------------
model_description = read_model_description(fmu_path)
default_experiment = getattr(model_description, "defaultExperiment", None)

start_time = getattr(default_experiment, "startTime", 0.0)
stop_time  = getattr(default_experiment, "stopTime",  60.0)
sample_time = getattr(default_experiment, "stepSize",  0.1)

print(f"Simulating FMU '{fmu_path}' from {start_time}s to {stop_time}s with dt={sample_time}s")

# --- Time vector ----------------------------------------------------------
time_vector = np.arange(start_time, stop_time + sample_time / 2, sample_time)

# --- Build input signals --------------------------------------------------
if CONTROLLER_MODE:
    # Automatic: step in setpoint, keep manual input at zero
    setpoint_signal = np.where(time_vector >= step_time, step_level, 0.0)
    manual_signal   = np.zeros_like(time_vector)
else:
    # Manual: step in manual input, keep setpoint constant
    setpoint_signal = np.zeros_like(time_vector)
    manual_signal   = np.where(time_vector >= step_time, step_level, 0.0)

# Structured array with FMU input names
input_signals = np.zeros(
    time_vector.size,
    dtype=[('time', np.float64),
           ('setpoint', np.float64),
           ('u_manual', np.float64)]
)
input_signals['time'] = time_vector
input_signals['setpoint'] = setpoint_signal
input_signals['u_manual'] = manual_signal

# --- Set FMU parameters ---------------------------------------------------
# The FMU exposes: mode (Boolean), Kp (Real), Ti (Real)
start_values = {
    'mode': bool(CONTROLLER_MODE),
    'Kp': float(KP_VALUE),
    'Ti': float(TI_VALUE)
}

print(f"Start parameters: mode={CONTROLLER_MODE}, Kp={KP_VALUE}, Ti={TI_VALUE}")

# --- Simulate FMU ---------------------------------------------------------
simulation_result = simulate_fmu(
    filename=fmu_path,
    input=input_signals,
    output=None,                # record all variables
    record_events=True,
    output_interval=sample_time,
    start_values=start_values
)

# --- Extract results ------------------------------------------------------
time_result = simulation_result['time']

# --- Plot both outputs in subplots ---------------------------------------
fig, axes = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
fig.suptitle(
    f"FMU Outputs (Controller mode = {'automatic' if CONTROLLER_MODE else 'manual'}, "
    f"Kp = {KP_VALUE}, Ti = {TI_VALUE})"
)

# Process output (y)
if 'y' in simulation_result.dtype.names:
    axes[0].plot(time_result, simulation_result['y'], label='y (process output)')
    axes[0].plot(time_vector, setpoint_signal, '--', label='setpoint')
    axes[0].set_ylabel('y')
    axes[0].legend()
    axes[0].grid(True)

# Controller output (u)
if 'u' in simulation_result.dtype.names:
    axes[1].plot(time_result, simulation_result['u'], label='u (controller output)', color='tab:orange')
    axes[1].set_xlabel('Time [s]')
    axes[1].set_ylabel('u')
    axes[1].legend()
    axes[1].grid(True)

plt.tight_layout()
plt.show()
