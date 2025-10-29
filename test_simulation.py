"""Test simulation with input signals."""

from agent.tools import create_step_signal_tool, simulate_fmu_tool, set_fmu_parameters_tool

# Set parameters
params = set_fmu_parameters_tool.invoke({"mode": 'manual'})
print(f"Parameters: {params}")

# Create signal
signal = create_step_signal_tool.invoke({
    "signal_name": 'u_manual',
    "step_time": 10.0,
    "step_level": 1.0
})
print(f"Signal created: {len(signal['time'])} samples")

# Simulate
result = simulate_fmu_tool.invoke({
    "fmu_path": 'models/fmus/fopdt_pi.fmu',
    "parameters": params['parameters'],
    "input_signals": [signal]
})

print(f"✓ Success! Simulated {len(result['time'])} samples")
print(f"First few time values: {result['time'][:5]}")
print(f"Last few time values: {result['time'][-5:]}")

