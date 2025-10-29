# server.py

from typing import List
from pathlib import Path

from agent.tools.functions.inputs import create_signal, merge_signals, data_model_to_ndarray, ndarray_to_data_model
from agent.tools.functions.schema import FMUCollection, DataModel, FMUInfo, SimulationModel, StepProps
from agent.tools.functions.information import _get_model_description, _get_all_model_descriptions, _get_fmu_names
from fmpy import simulate_fmu

import numpy as np

# Default FMU directory path
DEFAULT_FMU_DIR = (Path(__file__).parents[3] / "models" / "fmus").resolve()


######### TOOLS #########
#GET_ALL_MODEL_DESCRIPTIONS_DESCRIPTION
# name="get_model_descriptions", 
# description=GET_ALL_MODEL_DESCRIPTIONS_DESCRIPTION

def get_all_model_descriptions() -> FMUCollection:
    """
        Lists all FMU models in the directory and their information.
        
        Returns:
            FMUCollection: Collection of FMU models
    """
    FMU_DIR = DEFAULT_FMU_DIR
    
    return _get_all_model_descriptions(FMU_DIR)

# GET_MODEL_DESCRIPTION_DESCRIPTION = 
# name="get_model_description", description=GET_MODEL_DESCRIPTION_DESCRIPTION

def get_model_description(fmu_name: str) -> FMUInfo:
    """
        Gets the model description of a specific FMU model.

        Args:
            fmu_name: Name of the FMU model

        Returns:
            FMUInfo: Full FMU information object
    """
    FMU_DIR = DEFAULT_FMU_DIR
    fmu_info = _get_model_description(FMU_DIR, fmu_name)
    
    # Emit UI component for model information
    _emit_model_info_card(fmu_info)
    
    return fmu_info


def _emit_model_info_card(fmu_info: FMUInfo):
    """Emit a UI component for FMU model information display."""
    import json
    
    # Create component spec
    component_spec = {
        "type": "component",
        "name": "ModelInfoCard",
        "props": {
            "name": fmu_info.name,
            "description": fmu_info.description,
            "fmiVersion": fmu_info.metadata.fmi_version,
            "author": fmu_info.metadata.author,
            "version": fmu_info.metadata.version,
            "inputs": fmu_info.variables.inputs,
            "outputs": fmu_info.variables.outputs,
            "parameters": fmu_info.variables.parameters,
            "simulation": {
                "startTime": fmu_info.simulation.start_time,
                "stopTime": fmu_info.simulation.stop_time,
                "tolerance": fmu_info.simulation.tolerance
            }
        }
    }
    
    # Emit as AG-UI component event
    print(f"data: {json.dumps(component_spec)}\n\n")

# GET_FMU_NAMES_DESCRIPTION = 
# name="get_fmu_names", description=GET_FMU_NAMES_DESCRIPTION
def get_fmu_names() -> List[str]:
    """
        Lists the models in the FMU directory.
        
        Returns:
            List[str]: List of model names
    """
    FMU_DIR = DEFAULT_FMU_DIR
    return _get_fmu_names(FMU_DIR)

# SIMULATION_DESCRIPTION = 
# name="simulate_fmu", description=SIMULATION_DESCRIPTION
def simulate_tool(sim: SimulationModel) -> DataModel:
    """
        Simulates a given FMU model.

        Args:
            sim: SimulationModel containing the simulation parameters
            
        Returns:
            DataModel: Simulation results

        Example JSON call body:
            {
                "fmu_name": "BouncingBall",
                "start_time": 0.0,
                "stop_time": 5.0,
                "output": ["h", "v"],
                "output_interval": 0.1,
                "start_values": {
                    "h": 1.0,
                    "v": 0.0,
                    "g": -9.81
                }
            }
    """
    FMU_DIR = DEFAULT_FMU_DIR
    if sim.start_values is None:
        sim.start_values = {}
    
    fmu_path = FMU_DIR / f"{sim.fmu_name}.fmu"
    if not fmu_path.is_file():
        raise FileNotFoundError(f"FMU not found: {fmu_path}")

    # Convert DataModel input to numpy array if provided and not empty
    input_array = None
    if sim.input is not None and hasattr(sim.input, 'timestamps') and sim.input.timestamps:
        input_array = data_model_to_ndarray(sim.input)

    results = simulate_fmu(
        filename=str(fmu_path),
        start_time=sim.start_time,
        stop_time=sim.stop_time,
        step_size=sim.step_size,
        start_values=sim.start_values,
        input=input_array,
        output=sim.output,
        output_interval=sim.output_interval,
        apply_default_start_values=True,
        record_events=True
    )

    data_model = ndarray_to_data_model(results)
    
    # Emit UI component for simulation results
    _emit_simulation_plot(sim.fmu_name, data_model, sim.start_time, sim.stop_time)
    
    return data_model

def generate_step_tool(step: StepProps) -> DataModel:
    """
    Generates a step signal.
    
    Args:
        step: StepProps containing the step signal properties
        
    Returns:
        DataModel: Step signal
    """
    timestamps = np.arange(step.time_range.start, step.time_range.stop, step.time_range.sampling_time)
    values = np.full(len(timestamps), step.initial_value)
    values[np.where(np.array(timestamps) >= step.step_time)] = step.final_value
    return DataModel(timestamps=timestamps, signals={step.signal_name: values})

def _emit_simulation_plot(fmu_name: str, data: DataModel, start_time: float, stop_time: float):
    """Emit a UI component for simulation results visualization."""
    import json
    
    # Extract time and output data
    time_data = data.timestamps  # Already a list per DataModel schema
    output_data = {}
    
    # Extract each output variable
    for var_name in data.signals:
        output_data[var_name] = data.signals[var_name]  # Already a list
    
    # Create component spec for AG-UI
    component_spec = {
        "type": "component",
        "name": "SimulationPlot",
        "props": {
            "title": f"{fmu_name} Simulation Results",
            "time": time_data,
            "outputs": output_data,
            "startTime": start_time,
            "stopTime": stop_time,
            "fmuName": fmu_name
        }
    }
    
    # Emit as AG-UI component event
    print(f"data: {json.dumps(component_spec)}\n\n")

# CREATE_SIGNAL_DESCRIPTION = 
# name="create_signal", description=CREATE_SIGNAL_DESCRIPTION
def create_signal_tool(
    signal_name: str,
    timestamps: List[float],
    values: List[float]
) -> DataModel:
    """
        Creates a single signal.
        
        Args:
            signal_name (str): Name of the signal
            timestamps (List(float)): List of timestamps
            values (List(float)): List of signal values corresponsing to the timestamps.

        Returns:
            DataModel
    """
    signal_data = create_signal(signal_name, timestamps, values)
    
    # Emit UI component for signal visualization
    _emit_signal_plot(signal_name, timestamps, values)
    
    return signal_data


def _emit_signal_plot(signal_name: str, timestamps: List[float], values: List[float]):
    """Emit a UI component for signal visualization."""
    import json
    
    # Create component spec
    component_spec = {
        "type": "component",
        "name": "SignalPlot",
        "props": {
            "title": f"Signal: {signal_name}",
            "time": timestamps,
            "values": values,
            "signalName": signal_name
        }
    }
    
    # Emit as AG-UI component event
    print(f"data: {json.dumps(component_spec)}\n\n")

# MERGE_SIGNALS_DESCRIPTION = 
# name="merge_signals", description=MERGE_SIGNALS_DESCRIPTION
def merge_signals_tool(signals: List[DataModel]) -> DataModel:
    """
        Merges multiple signals into single DataModel.
        
        Args:
        signals (List[DataModel]): List of signals

        Returns:
            DataModel
    """

    return merge_signals(signals)

