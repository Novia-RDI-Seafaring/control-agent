"""Test the simulation fix."""
from agent.tools import create_step_signal_tool, simulate_fmu_tool, set_fmu_parameters_tool

# Set to manual mode
params = set_fmu_parameters_tool.invoke({"mode": "manual"})
print(f"✓ Parameters set: {params['parameters']}")

# Create signal
signal = create_step_signal_tool.invoke({
    "signal_name": "u_manual",
    "step_time": 10.0,
    "step_level": 1.0,
})
print(f"✓ Signal created: {len(signal['time'])} samples (from {signal['time'][0]} to {signal['time'][-1]}s)")

# Simulate with signal
result = simulate_fmu_tool.invoke({
    "fmu_path": "models/fmus/fopdt_pi.fmu",
    "parameters": params['parameters'],
    "input_signals": [signal]
})

print(f"✓ Simulation successful!")
print(f"  - Simulated {len(result['time'])} samples")
print(f"  - Time range: {result['time'][0]} to {result['time'][-1]}s")
print(f"  - Output 'y' available: {'y' in result}")
print(f"  - Output 'u' available: {'u' in result}")

