from operator import truediv
from control_toolbox.tools.information import get_fmu_names, get_model_description, get_all_model_descriptions
from control_toolbox.tools.simulation import simulate, simulate_step_response, simulate_impulse_response, SimulationProps
from control_toolbox.tools.timeseries import generate_step, StepProps, TimeRange, generate_impulse, ImpulseProps

########################################################
# INFORMATION TOOLS
########################################################
# get model names
model_names = get_fmu_names()
print(80*"=")
print("Model Names:")
print(model_names.model_dump_json(indent=2))
print(80*"=")

# get model description
model_description = get_model_description(model_names.payload[0])
print(80*"=")
print("Model Description:")
print(model_description.model_dump_json(indent=2))
print(80*"=")

# get all model descriptions
all_model_descriptions = get_all_model_descriptions()
print(80*"=")
print("All Model Descriptions:")
print(all_model_descriptions.model_dump_json(indent=2))
print(80*"=")
########################################################
# TIMESETIES TOOLS
########################################################
step_props = StepProps(
    signal_name="input",
    time_range=TimeRange(start=0.0, stop=2.0, sampling_time=0.4),
    step_time=0.4,
    initial_value=0.0,
    final_value=1.0
)
step_results = generate_step(step_props)
print(80*"=")
print("Step Results:")
print(step_results.model_dump_json(indent=2))
print(80*"=")

# impulse
impulse_props = ImpulseProps(
    signal_name="input",
    time_range=TimeRange(start=0.0, stop=30.0, sampling_time=0.1),
    impulse_time=0.0,
    magnitude=1.0
)
impulse_results = generate_impulse(impulse_props)
print(80*"=")
print("Impulse Results:")
print(impulse_results.model_dump_json(indent=2))

########################################################
# SIMULATION TOOLS
########################################################
# Create simulation properties
simulation_props = SimulationProps(
        fmu_name="PI_FOPDT",
        start_time=0.0,
        stop_time=30.0,
        output_interval=0.1,
        start_values={
            "mode": False,
        }
    )


# simulate
simulation_results = simulate(sim_props=simulation_props, generate_plot=False)

print(80*"=")
print("Simulated Data:")
print(simulation_results.model_dump_json(indent=2))
print(80*"=")

# simulate step response
simulation_results = simulate_step_response(sim_props=simulation_props, step_props=step_props, generate_plot=False)

print(80*"=")
print("Simulated Step Response:")
print(simulation_results.model_dump_json(indent=2))
print(80*"=")

# simulate impulse response
simulation_results = simulate_impulse_response(sim_props=simulation_props, impulse_props=impulse_props, generate_plot=True)

print(80*"=")
print("Simulated Impulse Response:")
print(simulation_results.model_dump_json(indent=2))
print(80*"=")

# plot simulation results
import plotly.graph_objects as go
for figure in simulation_results.figures:
    fig = go.Figure(figure.spec)
    fig.show()