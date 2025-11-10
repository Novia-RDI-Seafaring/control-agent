from control_toolbox.tools.information import ModelDescription
from control_toolbox.tools.simulation import SimulationProps, simulate_step_response
from control_toolbox.tools.identification import identify_fopdt_from_step, IdentificationProps, FOPDTModel
from control_toolbox.tools.signals import generate_step, StepProps, TimeRange, generate_impulse, ImpulseProps

from control_toolbox.config import *
fmu_path = (Path(__file__).resolve().parent / "models" / "fmus").resolve()
set_fmu_dir(fmu_path)

#simulate step response
simulation_props = SimulationProps(
    fmu_name = "PI_FOPDT_2",
    start_time = 0,
    stop_time = 10,
    step_size = 1,
    output_interval = 0.5,
    start_values = {
        "mode": False,
    }
)

step_props = StepProps(
    signal_name = "input",
    time_range = TimeRange(start=0, stop=10, sampling_time=0.1),
    step_time = 1.0,
    initial_value = 0,
    final_value = 1,
)

simulation_response = simulate_step_response(
    sim_props = simulation_props,
    step_props = step_props
)

print(simulation_response.model_dump_json(indent=2))

# identify system

identification_props = IdentificationProps(
    input_name = "u",
    output_name = "y",
    method = "tangent",
    model = "fopdt"
)

identificaiotn_response = identify_fopdt_from_step(
    data = simulation_response.data,
    props = identification_props,
)

print(identificaiotn_response.model_dump_json(indent=2))
