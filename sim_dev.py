# pip install fmpy matplotlib

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from fmpy import read_model_description, simulate_fmu

# --- Paths & metadata ---
fmu_path = Path("models/fmus/fopd.fmu").as_posix()
md = read_model_description(fmu_path)

# Use FMU defaults if available
start_time = getattr(getattr(md, "defaultExperiment", None), "startTime", 0.0)
stop_time  = getattr(getattr(md, "defaultExperiment", None), "stopTime",  20.0)
output_dt  = getattr(getattr(md, "defaultExperiment", None), "stepSize",  0.01)

# --- Build step input for 'setpoint' at t = 10 s ---
t = np.arange(start_time, stop_time + output_dt/2, output_dt)
u = np.where(t >= 10.0, 1.0, 0.0)

# Structured array with *named* columns: 'time' and *exact* input var name
input_signal = np.zeros(t.size, dtype=[('time', np.float64), ('setpoint', np.float64)])
input_signal['time'] = t
input_signal['setpoint'] = u

# (Optional) choose outputs marked as outputs; or set to None to record all
outputs = [v.name for v in md.modelVariables if v.causality == 'output'] or None

# --- Simulate ---
result = simulate_fmu(
    filename=fmu_path,
    start_time=start_time,
    stop_time=stop_time,
    input=input_signal,          # structured input with field 'setpoint'
    output=outputs,              # None => all variables
    record_events=True,
    output_interval=output_dt,   # ensures regular sampling in the result
    # solver='CVode',            # used for Model Exchange FMUs
    # step_size=0.01,            # you can set this explicitly for CS FMUs
    debug_logging=False
)

# --- Plot: response(s) vs step input ---
time = result['time']
for name in result.dtype.names:
    if name in ('time', 'setpoint'):
        continue
    plt.figure()
    plt.plot(time, result[name], label=name)
    plt.plot(t, u, '--', label='setpoint (input)')
    plt.xlabel('Time [s]')
    plt.ylabel(name)
    plt.title(f'{name} response to 0→1 step at t=10 s')
    plt.legend()
    plt.grid(True)
    plt.show()
