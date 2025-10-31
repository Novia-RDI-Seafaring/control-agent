# server.py

from typing import List
from pathlib import Path

from fastapi._compat.v1 import BaseModel
from matplotlib.pyplot import cla
from pydantic import Field
from typing import Literal

from agent.tools.functions.inputs import create_signal, merge_signals, data_model_to_ndarray, ndarray_to_data_model
from agent.tools.functions.schema import (
    FMUCollection, DataModel, FMUInfo,
    SimulationModel, StepProps, StepResponseAnalysis,
    CharacteristicPoints, AnalysisProps, Signal,
    UltimateTuningProps, PIDParameters,
    )
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
    ### Tool: simulate_fmu_model

    Args:
        sim: SimulationModel containing the simulation parameters
        
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

    Usage: 
    - Make sure thaht the step signal is generated with the correct signal name when passed to other tools as input.
    - Make sure the lists of timestamps and values are the same length
    - Make sure the timestamps are in ascending order
    - Keep the timestamp and value lists as short as possible. It is enough to define the singal only at timestamps where change happens.

    Example: Generate a step at t=1 seconds on the time interval [0, 10.0] seconds.
    ```json
    {
        "signal_name": "input",
        "time_range": {
            "start": 0.0,
            "stop": 10.0,
            "sampling_time": 0.1
        },
        "step_time": 1.0,
        "initial_value": 0.0,
        "final_value": 1.0
    }
    ```

    """
    start = step.time_range.start
    stop = step.time_range.stop
    dt = step.time_range.sampling_time

    # number of samples in interval
    dt = step.time_range.sampling_time
    timestamps = np.array([start, step.step_time - dt, step.step_time, step.step_time + dt, stop])
    values = np.array([step.initial_value, step.initial_value, step.final_value, step.final_value, step.final_value])
    # number of samples in interval
    #N = int(round((stop - start) / dt))

    #timestamps = np.linspace(start, start + N * dt, N + 1, dtype=float)
    #values = np.full_like(timestamps, step.initial_value, float)
    #values[timestamps >= step.step_time] = step.final_value
    return DataModel(
        timestamps=timestamps,
        signals=[Signal(name=step.signal_name, values=values.tolist())]
        )

def _emit_simulation_plot(fmu_name: str, data: DataModel, start_time: float, stop_time: float) -> None:
    """Emit a UI component for simulation results visualization."""
    import json

    # Extract time and outputs
    time_data = list(map(float, data.timestamps))
    output_data = {s.name: list(map(float, s.values)) for s in data.signals}

    # Component spec for your UI
    component_spec = {
        "type": "component",
        "name": "SimulationPlot",
        "props": {
            "title": f"{fmu_name} Simulation Results",
            "time": time_data,
            "outputs": output_data,
            "startTime": float(start_time),
            "stopTime": float(stop_time),
            "fmuName": fmu_name,
        },
    }

    # Emit as AG-UI component event
    print(f"data: {json.dumps(component_spec)}\n\n")

'''
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
'''

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

'''
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
'''

def analyse_step_response(
    signal_name: str,
    data: DataModel,
    props: AnalysisProps,
) -> StepResponseAnalysis:
    """
    Analyses a step response.

    Args:
        signal_name: Name of the signal
        data: DataModel containing the data
        props: AnalysisProps containing the analysis properties

    Returns:
        StepResponseAnalysis: Step response analysis

    Usage: Use this tool when analysing step response data. This tool returns characteristic points (time, value):
        - p0 = (t0,y0) point when output starts to change from initial value.
        - p10 = (t10,y10) point when output first reachest 10% of total change.
        - p63 = (t63,y63) point when output first reachest 63% of total change. Can be used to determine the time constant T of a FOPDT system.
        - p90 = (t90,y90) point when output first reachest 90% of total change.
        - p98 = (t98,y98) point when output first reachest 98% of total change.
        - pRT0 = (tRT0,yRT0) point when output first reachest RT(0) of total change.
        - pRT1 = (tRT1,yRT1) point when output first reachest RT(1) of total change.
        - pST = (tST,yST) point when output first reachest ST of total change.
        - pPeak = (tPeak,yPeak) point when output first reachest Peak of total change.
        - pUndershoot = (tUndershoot,yUndershoot) point when output first reachest Undershoot of total change.
    - Rise time: time it takes for the response to rise from 10% to 90% of the final value. **This is useful when evaluating of finetuning controller performance.**
    - Settling time: time it takes for the response to settle within 2% of the final value. **This is useful when evaluating of finetuning controller performance.**
    - Settling min: minimum response value observed while evaluating settling behavior. **This is useful when evaluating of finetuning controller performance.**
    - Settling max: maximum response value observed while evaluating settling behavior. **This is useful when evaluating of finetuning controller performance.**
    - Overshoot: percentage of the final value that the response exceeds. **This is useful when evaluating of finetuning controller performance.**
    - Undershoot: percentage of the final value that the response undershoots. **This is useful when evaluating of finetuning controller performance.**
    """
    t = np.asarray(data.timestamps, dtype=float)
    for s in data.signals:
        if s.name == signal_name:
            y = np.asarray(s.values, dtype=float)
            break
    else:
        raise ValueError(f"Signal {signal_name} not found in DataModel")

    # Basic quantities
    y_start, y_final = float(y[0]), float(y[-1])
    dy = y_final - y_start
    abs_dy = abs(dy) if abs(dy) > 0 else 1.0
    is_upward = dy >= 0

    # Initial response: first deviation > 1% of total change
    eps = 0.01 * abs_dy
    dev_idx = np.where(np.abs(y - y_start) > eps)[0]
    t_initial = float(t[dev_idx[0]]) if dev_idx.size else float(t[0])
    i_initial = int(np.searchsorted(t, t_initial, side="left"))

    # Helper: get value at time (with interpolation)
    def get_value(t_val: float) -> float:
        if not np.isfinite(t_val):
            return float("nan")
        idx = np.searchsorted(t, t_val, side="left")
        if idx == 0:
            return float(y[0])
        if idx >= len(y):
            return float(y[-1])
        if t[idx] == t_val:
            return float(y[idx])
        # Linear interpolation
        t0, t1, y0, y1 = t[idx - 1], t[idx], y[idx - 1], y[idx]
        return float(y0 + (y1 - y0) * (t_val - t0) / (t1 - t0))

    # Helper: first crossing of threshold
    def first_cross(threshold: float) -> float:
        if is_upward:
            idx = np.where(y[i_initial:] >= threshold)[0]
        else:
            idx = np.where(y[i_initial:] <= threshold)[0]
        return float(t[i_initial + idx[0]]) if idx.size else float("nan")

    # Characteristic crossing times
    levels = {name: y_start + frac * dy for name, frac in [
        ('10', 0.10), ('63', 0.63), ('90', 0.90), ('98', 0.98),
        ('RT0', props.rise_time_limits[0]), ('RT1', props.rise_time_limits[1])
    ]}
    crossings = {name: first_cross(level) for name, level in levels.items()}
    t_10, t_63, t_90, t_98 = crossings['10'], crossings['63'], crossings['90'], crossings['98']
    t_RT0, t_RT1 = crossings['RT0'], crossings['RT1']

    # Rise time
    rise_time = (t_90 - t_10) if np.isfinite(t_10) and np.isfinite(t_90) else float("nan")

    # Settling time: last exit point where signal then stays within band
    band = props.settling_time_treshhold * abs_dy
    inside = np.abs(y - y_final) <= band
    
    if np.all(inside):
        settling_time_abs = float(t[0])
    elif np.any(~inside):
        last_out = int(np.where(~inside)[0][-1])
        if last_out + 1 < len(y) and np.all(inside[last_out + 1:]):
            settling_time_abs = float(t[last_out + 1])
        else:
            settling_time_abs = float("nan")
    else:
        settling_time_abs = float("nan")
    
    # Settling time relative to initial response
    settling_time = (settling_time_abs - t_initial) if np.isfinite(settling_time_abs) else float("nan")

    # Settling min/max: after RT1
    i_RT1 = int(np.searchsorted(t, t_RT1, side="left")) if np.isfinite(t_RT1) else 0
    y_settling = y[i_RT1:] if i_RT1 < len(y) else y
    settling_min, settling_max = float(np.min(y_settling)), float(np.max(y_settling))

    # Peak: maximum after rise time (after t_90)
    if np.isfinite(t_90):
        i_start = int(np.searchsorted(t, t_90, side="left"))
        if i_start < len(y):
            idx = i_start + (np.argmax if is_upward else np.argmin)(y[i_start:])
            peak, peak_time = float(y[idx]), float(t[idx])
        else:
            peak, peak_time = float(y[-1]), float(t[-1])
    else:
        # Fallback: peak after initial response
        idx = i_initial + (np.argmax if is_upward else np.argmin)(y[i_initial:])
        peak, peak_time = float(y[idx]), float(t[idx])

    # Overshoot: peak exceeds final value
    if (is_upward and peak > y_final) or (not is_upward and peak < y_final):
        overshoot = abs(peak - y_final) / abs_dy * 100.0
    else:
        overshoot = None

    # Undershoot: smallest value after RT1 relative to final value, as percentage
    # Find the time point where undershoot occurs
    undershoot_time = float("nan")
    undershoot_value = float("nan")
    
    if np.isfinite(t_RT1) and len(y_settling) > 0:
        # Find index of minimum value after RT1
        if is_upward:
            # Find index of settling_min in y_settling
            min_idx_in_settling = int(np.argmin(y_settling))
            undershoot_idx = i_RT1 + min_idx_in_settling
            if undershoot_idx < len(t):
                undershoot_time = float(t[undershoot_idx])
                undershoot_value = settling_min
        else:
            # Find index of settling_max in y_settling
            max_idx_in_settling = int(np.argmax(y_settling))
            undershoot_idx = i_RT1 + max_idx_in_settling
            if undershoot_idx < len(t):
                undershoot_time = float(t[undershoot_idx])
                undershoot_value = settling_max
        
        # Calculate undershoot percentage
        if is_upward:
            if settling_min < y_final:
                undershoot = abs(settling_min - y_final) / abs_dy * 100.0
            else:
                undershoot = None
        else:
            if settling_max > y_final:
                undershoot = abs(settling_max - y_final) / abs_dy * 100.0
            else:
                undershoot = None
    else:
        undershoot = None

    # Helper: create characteristic point tuple
    def cp(t_val: float, y_val: float = None) -> tuple:
        t_safe = t_val if np.isfinite(t_val) else float("nan")
        y_safe = y_val if y_val is not None else get_value(t_val)
        return (t_safe, y_safe)

    return StepResponseAnalysis(
        characteristic_points=CharacteristicPoints(
            p0=cp(t_initial, y_start),
            p10=cp(t_10), p63=cp(t_63), p90=cp(t_90), p98=cp(t_98),
            pRT0=cp(t_RT0), pRT1=cp(t_RT1),
            pST=cp(settling_time_abs), pPeak=cp(peak_time, peak),
            pUndershoot=cp(undershoot_time, undershoot_value),
        ),
        rise_time=rise_time,
        settling_time=settling_time,
        settling_min=settling_min,
        settling_max=settling_max,
        overshoot=overshoot,
        undershoot=undershoot,
    )

def zn_pid_tuning(props: UltimateTuningProps) -> PIDParameters:
    """
    Compute PID controller parameters using the Ziegler-Nichols closed-loop
    (also called ultimate gain or continuous-cycling) tuning method.

    This function implements the standard Ziegler-Nichols closed-loop tuning rules.
    It uses the experimentally determined **ultimate gain (Ku)** and **ultimate period (Pu)**
    obtained from a continuous-cycling test (sustained oscillation test).
    
    The function supports several controller configurations (P, PI, PD, PID)
    and tuning rule variants ("classic", "some_overshoot", "no_overshoot").

    ---
    ### Usage logic
    - For controllers `p`, `pi`, or `pd`, only the `"classic"` method is valid.
    - For `pid` controllers, all three methods are supported.
    - Any other `(controller, method)` combination raises a `ValueError`.

    ---
    ### Args:
        props (UltimateTuningProps):
            A model specifying:
              - `params.Ku` (float): the ultimate gain determined experimentally.
              - `params.Pu` (float): the oscillation period at the ultimate gain.
              - `controller` (Literal["p", "pi", "pd", "pid"]): the controller type.
              - `method` (Literal["classic", "some_overshoot", "no_overshoot"]):
                the tuning variant to apply. Defaults to `"classic"`.

    ---
    ### Returns:
        PIDParameters:
            A data model containing:
              - `Kp` (float): proportional gain.
              - `Ti` (float): integral time constant (∞ if not applicable).
              - `Td` (float): derivative time constant (0 if not applicable).

    ---
    ### Raises:
        ValueError:
            If the controller/method combination is unsupported or invalid.

    ---
    ### Example usage:
    - Before using this method, perform a closed-loop tuning test with a P-only controller (set I = 0, D = 0).
    - Gradually increase the proportional gain until the system exhibits sustained oscillations.
    - The gain at this point is the ultimate gain (Ku).
    - The oscillation period is the ultimate period (Pu).
    - Pass these values to the function using an argument that complies with the UltimateTuningProps schema.
    ```json
    {
        "params": {
            "Ku": ...,
            "Pu": ...
        },
        "controller": ...,
        "method": ...
    }
    ```
    """
    Ku, Pu = props.params.Ku, props.params.Pu
    ctrl, method = props.controller, props.method

    match (ctrl, method):
        # --- P controller ---
        case ("p", "classic"):
            return PIDParameters(Kp=0.5 * Ku)

        # --- PI controller ---
        case ("pi", "classic"):
            return PIDParameters(Kp=0.45 * Ku, Ti=Pu / 1.2)

        # --- PD controller ---
        case ("pd", "classic"):
            return PIDParameters(Kp=0.8 * Ku, Td=Pu / 8.0)

        # --- PID controller: variants ---
        case ("pid", "classic"):
            return PIDParameters(Kp=0.6 * Ku, Ti=Pu / 2.0, Td=Pu / 8.0)

        case ("pid", "some_overshoot"):
            # Slightly less aggressive than classic Z–N
            return PIDParameters(Kp=(1.0 / 3.0) * Ku, Ti=Pu / 2.0, Td=Pu / 3.0)

        case ("pid", "no_overshoot"):
            # Conservative, smooth response
            return PIDParameters(Kp=0.20 * Ku, Ti=Pu / 2.0, Td=Pu / 3.0)
            
        #anything else
        case _:
            raise ValueError(
                f"Unsupported controller/method combination: "
                f"controller='{ctrl}', method='{method}'"
            )