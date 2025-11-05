from operator import truediv
from control_toolbox.tools.information import get_fmu_names, get_model_description, get_all_model_descriptions
from control_toolbox.tools.simulation import simulate, simulate_step_response, SimulationProps
from control_toolbox.tools.timeseries import generate_step, StepProps, TimeRange

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

########################################################
# SIMULATION TOOLS
########################################################
# Create simulation properties
simulation_props = SimulationProps(
        fmu_name="PI_FOPDT",
        start_time=0.0,
        stop_time=2.0,
        output_interval=0.4,
        start_values={
            "mode": False,
        }
    )


# simulate
simulation_results = simulate(sim_props=simulation_props)

print(80*"=")
print("Simulated Data:")
print(simulation_results.model_dump_json(indent=2))
print(80*"=")

# simulate step response
simulation_results = simulate_step_response(sim_props=simulation_props, step_props=step_props)

print(80*"=")
print("Simulated Step Response:")
print(simulation_results.model_dump_json(indent=2))
print(80*"=")