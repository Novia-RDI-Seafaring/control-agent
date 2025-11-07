from pathlib import Path
from typing import Dict, List, Optional, Union
from fmpy import simulate_fmu as fmpy_simulate_fmu
from pydantic import BaseModel, Field
from typing import Any

from control_toolbox.schema import DataModel, ResponseModel, Source, FigureModel
from control_toolbox.tools.utils import data_model_to_ndarray, ndarray_to_data_model
from control_toolbox.config import get_fmu_dir
from control_toolbox.tools.timeseries import generate_step, StepProps, generate_impulse, ImpulseProps

########################################################
# SCHEMAS
########################################################
class SimulationProps(BaseModel):
    fmu_name: str = Field(
        description="Name of the FMU model to simulate"
    )
    start_time: Optional[Union[float, str]] = Field(
        default=0.0,
        description="Simulation start time"
    )
    stop_time: Optional[Union[float, str]] = Field(
        default=1.0,
        description="Simulation stop time"
    )
    step_size: Optional[Union[float, str]] = Field(
        default=None,
        description="Simulation step size. Must be integer multiple ofthe FMU models internal step size."
    )
    input: Optional[DataModel] = Field(
        default=None,
        description="DataModel containing input signals"
    )
    output: Optional[List[str]] = Field(
        default=None,
        description="Sequence of output variable names to record"
    )
    output_interval: Union[float, str] = Field(
        default=None,
        description="Interval for sampling the output. Must be integer multiple of FMU models internal step size."
    )
    start_values: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Dictionary of initial parameter and input values. "
            "Use this function to change the values of parameters and "
            "inputs from their default values."
        )
    )

########################################################
# PLOTTING
########################################################
import plotly.graph_objs as go

def plotly_simulation(data: DataModel):
    timestamps = data.timestamps
    signals = data.signals

    # Create a list to hold the individual figures
    figures = []

    for signal in signals:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=signal.values,
            mode='lines',
            name=signal.name
        ))
        fig.update_layout(
            title=f"Simulation Result - {signal.name}",
            xaxis_title="Time (seconds)",
            yaxis_title=f"{signal.name} Value",
            template="plotly_white"
        )
        # Convert Plotly figure to FigureModel
        figure_model = FigureModel(
            spec=fig.to_dict(),
            caption=f"Simulation result for {signal.name}"
        )
        figures.append(figure_model)

    return figures

########################################################
# TOOLS
########################################################

def simulate(sim_props: SimulationProps, FMU_DIR: Optional[Path] = None, generate_plot: bool = False) -> DataModel:
    """
    ### Tool: simulate_fmu

    Args:
        sim_props: SimulationProps containing the simulation parameters
        
    Returns:
        DataModel: simulation results

    **Purpose:**  
    Run a time-domain simulation of a Functional Mock-up Unit (FMU) model using the specified parameters and input signals.

    **When to use:**  
    Use this tool whenever you need to simulate the dynamic response of an FMU model.

    **IMPORTANT**  
    - Do **not** approximate or reason about simulation results — always call this tool to obtain actual simulated outputs.

    **Inputs:**  
    Accepts a JSON object matching the `SimulationModel` schema with the following fields:  
    - `fmu_name` (string) — Name of the FMU to simulate.
    - `start_time` (float) — Simulation start time (in seconds). Typically 0.0 seconds.
    - `stop_time` (float) — Simulation stop time (in seconds).  
    - `input` (DataModel) — Input signal(s) defined over the time interval.
    - `output` (list[string]) — Names of FMU output variables to record.  
    - `output_interval` (float) — Sampling interval for recorded outputs. Use an interval that is neither too short nor too long.
    - `start_values` (object) — Use this to set parameter values or initial states for the FMU (e.g., controller gains).

    **Outputs:**  
    Returns a `DataModel` object containing the simulation results, including:  
    - `timestamps` — Time points where output values are sampled.  
    - `signals` — Recorded outputs corresponding to the requested variables.

    **Usage notes:**
    - `fmu_name` is the name of the FMU model to simulate. Use the `get_fmu_names` tool to list available model names.   
    - `start_time` and `stop_time` define the simulation interval.
    - `input` is a `DataModel` describing the input signal. Step inputs can be generated using the `generate_step_tool`.  
    - `output` lists only the desired output variables to record. Not all FMU outputs must be returned.  
    - `output_interval` controls the sampling rate of recorded outputs.

    **Rules:**  
    - Always provide a valid FMU name available to the simulation environment.  
    - Ensure that `start_values` contain all paramteters required by the FMU.  
    """
    if FMU_DIR is None:
        FMU_DIR = get_fmu_dir()
    fmu_path = FMU_DIR / f"{sim_props.fmu_name}.fmu"

    if sim_props.start_values is None:
        sim_props.start_values = {}
    
    if not fmu_path.is_file():
        raise FileNotFoundError(f"FMU not found: {fmu_path}")

    # Convert DataModel input to numpy array if provided and not empty
    input_array = None
    if sim_props.input is not None and hasattr(sim_props.input, 'timestamps') and sim_props.input.timestamps:
        input_array = data_model_to_ndarray(sim_props.input)

    results = fmpy_simulate_fmu(
        filename=str(fmu_path),
        start_time=sim_props.start_time,
        stop_time=sim_props.stop_time,
        step_size=sim_props.step_size,
        start_values=sim_props.start_values,
        input=input_array,
        output=sim_props.output,
        output_interval=sim_props.output_interval,
        apply_default_start_values=True,
        record_events=True
    )

    data_model = ndarray_to_data_model(results)
    
    return ResponseModel(
        source=Source(
            tool_name="simulate",
            arguments={"sim_props": sim_props}
        ),
        data=data_model,
        figures=plotly_simulation(data_model) if generate_plot else None
    )


def simulate_step_response(sim_props: SimulationProps, step_props: StepProps, FMU_DIR: Optional[Path] = None, generate_plot: bool = False) -> DataModel:
    """
    ### Tool: simulate_fmu_step

    Args:
        sim_props: SimulationProps containing the simulation parameters
        step_props: StepProps containing the step signal properties
        
    Returns:
        DataModel: simulation results
    """
    # generate inputs
    sim_props.input = generate_step(step_props).data
    result = simulate(sim_props, FMU_DIR, generate_plot)
    
    return ResponseModel(
        source=Source(
            tool_name="simulate_step_response",
            arguments={"sim_props": sim_props, "step_props": step_props}
        ),
        data=result.data,
        figures=result.figures
    )

def simulate_impulse_response(sim_props: SimulationProps, impulse_props: ImpulseProps, FMU_DIR: Optional[Path] = None, generate_plot: bool = False) -> DataModel:
    """
    ### Tool: simulate_fmu_step

    Args:
        sim_props: SimulationProps containing the simulation parameters
        impulse_props: ImpulseProps containing the impulse signal properties at time 'impulse_time' with magnutude 'magnitude'
        
    Returns:
        DataModel: simulation results
    """
    # generate inputs
    sim_props.input = generate_impulse(impulse_props).data
    result = simulate(sim_props, FMU_DIR, generate_plot)

    return ResponseModel(
        source=Source(
            tool_name="simulate_impulse_response",
            arguments={"sim_props": sim_props, "impulse_props": impulse_props}
        ),
        data=result.data,
        figures=result.figures
    )

