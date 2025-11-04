from control_toolbox.tools.information import get_fmu_names, get_model_description, get_all_model_descriptions
from control_toolbox.tools.simulation import simulate_tool, SimulationProps
from control_toolbox.config import set_fmu_dir
from pathlib import Path

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
# SIMULATION TOOLS
########################################################
# Create simulation properties
simulation_props = SimulationProps(
    fmu_name=model_names.payload[0],
    start_time=0.0,
    stop_time=10.0,
    output_interval=0.1
)
# simulate
simulation_results = simulate_tool(simulation_props.fmu_name, simulation_props)
print(80*"=")
print("Simulated Data:")
print(simulation_results.model_dump_json(indent=2))
print(80*"=")