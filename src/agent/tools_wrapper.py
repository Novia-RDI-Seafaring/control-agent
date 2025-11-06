"""Tool definitions for FMI agent using OpenAI Agents SDK."""

import os
from pathlib import Path
from typing import List

import numpy as np
from agents import function_tool
from fmpy import simulate_fmu
from scipy.signal import find_peaks

from .tool_functions.information import _get_model_description, _get_all_model_descriptions, _get_fmu_names
from .tool_functions.inputs import create_signal, merge_signals, data_model_to_ndarray, ndarray_to_data_model
from .tool_functions.schema import (
    FMUCollection, DataModel, FMUInfo,
    SimulationModel, StepProps, StepResponseAnalysis,
    CharacteristicPoints, AnalysisProps, Signal,
    UltimateTuningProps, PIDParameters,
    FindPeaksProps, FindPeaksResult, Peak, PlotHttpURL
)

# Default FMU directory path
DEFAULT_FMU_DIR = Path(os.getenv("DEFAULT_FMU_PATH", "models/fmus")).resolve()


@function_tool(strict_mode=False)
def get_all_model_descriptions() -> FMUCollection:
    """
    Lists all FMU models in the directory and their information.
    
    Returns:
        FMUCollection: Collection of FMU models
    """
    return _get_all_model_descriptions(DEFAULT_FMU_DIR)


@function_tool(strict_mode=False)
def get_model_description(fmu_name: str) -> FMUInfo:
    """
    Gets the model description of a specific FMU model.

    Args:
        fmu_name: Name of the FMU model

    Returns:
        FMUInfo: Full FMU information object
    """
    return _get_model_description(DEFAULT_FMU_DIR, fmu_name)


@function_tool(strict_mode=False)
def get_fmu_names() -> List[str]:
    """
    Lists the models in the FMU directory.
    
    Returns:
        List[str]: List of model names
    """
    return _get_fmu_names(DEFAULT_FMU_DIR)


@function_tool(strict_mode=False)
def simulate_tool(sim: SimulationModel) -> DataModel:
    """
    Run a time-domain simulation of a Functional Mock-up Unit (FMU) model using the specified parameters and input signals.

    Args:
        sim: SimulationModel containing the simulation parameters
        
    Returns:
        DataModel: simulation results
    """
    if sim.start_values is None:
        sim.start_values = {}
    
    fmu_path = DEFAULT_FMU_DIR / f"{sim.fmu_name}.fmu"
    if not fmu_path.is_file():
        raise FileNotFoundError(f"FMU not found: {fmu_path}")

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

    return ndarray_to_data_model(results)


@function_tool(strict_mode=False)
def generate_step_tool(step: StepProps) -> DataModel:
    """
    Generates a step signal.
    
    Args:
        step: StepProps containing the step signal properties
        
    Returns:
        DataModel: Step signal
    """
    start = step.time_range.start
    stop = step.time_range.stop
    dt = step.time_range.sampling_time

    timestamps = np.array([start, step.step_time - dt, step.step_time, step.step_time + dt, stop])
    values = np.array([step.initial_value, step.initial_value, step.final_value, step.final_value, step.final_value])

    return DataModel(
        timestamps=timestamps.tolist(),
        signals=[Signal(name=step.signal_name, values=values.tolist())]
    )


@function_tool(strict_mode=False)
def find_peaks_tool(signal_name: str, data: DataModel, props: FindPeaksProps) -> FindPeaksResult:
    """
    Find peaks inside a signal based on peak properties.

    This function takes DataModel and finds all local maxima by simple comparison of neighboring values.
    Optionally, a subset of these peaks can be selected by specifying conditions for a peak's properties.
    """
    t = np.asarray(data.timestamps, dtype=float)
    for s in data.signals:
        if s.name == signal_name:
            x = np.asarray(s.values, dtype=float)
            break
    else:
        raise ValueError(f"Signal {signal_name} not found in DataModel")

    peaks, properties = find_peaks(
        x, 
        height=props.height, 
        threshold=props.threshold, 
        distance=props.distance, 
        prominence=props.prominence, 
        width=props.width, 
        wlen=props.wlen, 
        rel_height=props.rel_height, 
        plateau_size=props.plateau_size
    )
    
    peak_timestamps = [t[p] for p in peaks]
    if len(peak_timestamps) >= 2:
        average_peak_period = float(np.mean(np.diff(peak_timestamps)))
    else:
        average_peak_period = float("nan")

    return FindPeaksResult(
        peaks=[Peak(timestamp=t[p], value=x[p]) for p in peaks], 
        average_peak_period=average_peak_period, 
        properties=properties
    )


@function_tool(strict_mode=False)
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
        StepResponseAnalysis: Step response analysis which contains critical points and metrics useful for finetuning controller performance.
    """
    t = np.asarray(data.timestamps, dtype=float)
    for s in data.signals:
        if s.name == signal_name:
            y = np.asarray(s.values, dtype=float)
            break
    else:
        raise ValueError(f"Signal {signal_name} not found in DataModel")

    y_start, y_final = float(y[0]), float(y[-1])
    dy = y_final - y_start
    abs_dy = abs(dy) if abs(dy) > 0 else 1.0
    is_upward = dy >= 0

    eps = 0.01 * abs_dy
    dev_idx = np.where(np.abs(y - y_start) > eps)[0]
    t_initial = float(t[dev_idx[0]]) if dev_idx.size else float(t[0])
    i_initial = int(np.searchsorted(t, t_initial, side="left"))

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
        t0, t1, y0, y1 = t[idx - 1], t[idx], y[idx - 1], y[idx]
        return float(y0 + (y1 - y0) * (t_val - t0) / (t1 - t0))

    def first_cross(threshold: float) -> float:
        if is_upward:
            idx = np.where(y[i_initial:] >= threshold)[0]
        else:
            idx = np.where(y[i_initial:] <= threshold)[0]
        return float(t[i_initial + idx[0]]) if idx.size else float("nan")

    levels = {name: y_start + frac * dy for name, frac in [
        ('10', 0.10), ('63', 0.63), ('90', 0.90), ('98', 0.98),
        ('RT0', props.rise_time_limits[0]), ('RT1', props.rise_time_limits[1])
    ]}
    crossings = {name: first_cross(level) for name, level in levels.items()}
    t_10, t_63, t_90, t_98 = crossings['10'], crossings['63'], crossings['90'], crossings['98']
    t_RT0, t_RT1 = crossings['RT0'], crossings['RT1']

    rise_time = (t_90 - t_10) if np.isfinite(t_10) and np.isfinite(t_90) else float("nan")

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
    
    settling_time = (settling_time_abs - t_initial) if np.isfinite(settling_time_abs) else float("nan")

    i_RT1 = int(np.searchsorted(t, t_RT1, side="left")) if np.isfinite(t_RT1) else 0
    y_settling = y[i_RT1:] if i_RT1 < len(y) else y
    settling_min, settling_max = float(np.min(y_settling)), float(np.max(y_settling))

    if np.isfinite(t_90):
        i_start = int(np.searchsorted(t, t_90, side="left"))
        if i_start < len(y):
            idx = i_start + (np.argmax if is_upward else np.argmin)(y[i_start:])
            peak, peak_time = float(y[idx]), float(t[idx])
        else:
            peak, peak_time = float(y[-1]), float(t[-1])
    else:
        idx = i_initial + (np.argmax if is_upward else np.argmin)(y[i_initial:])
        peak, peak_time = float(y[idx]), float(t[idx])

    if (is_upward and peak > y_final) or (not is_upward and peak < y_final):
        overshoot = abs(peak - y_final) / abs_dy * 100.0
    else:
        overshoot = None

    undershoot_time = float("nan")
    undershoot_value = float("nan")
    
    if np.isfinite(t_RT1) and len(y_settling) > 0:
        if is_upward:
            min_idx_in_settling = int(np.argmin(y_settling))
            undershoot_idx = i_RT1 + min_idx_in_settling
            if undershoot_idx < len(t):
                undershoot_time = float(t[undershoot_idx])
                undershoot_value = settling_min
        else:
            max_idx_in_settling = int(np.argmax(y_settling))
            undershoot_idx = i_RT1 + max_idx_in_settling
            if undershoot_idx < len(t):
                undershoot_time = float(t[undershoot_idx])
                undershoot_value = settling_max
        
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

    def cp(t_val: float, y_val: float = None) -> List[float]:
        t_safe = t_val if np.isfinite(t_val) else float("nan")
        y_safe = y_val if y_val is not None else get_value(t_val)
        return [t_safe, y_safe]

    peaks_result = find_peaks_tool(signal_name=signal_name, data=data, props=FindPeaksProps())

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
        peaks=peaks_result.peaks,
    )


@function_tool(strict_mode=False)
def zn_pid_tuning(props: UltimateTuningProps) -> PIDParameters:
    """
    Compute PID controller parameters using the Ziegler-Nichols closed-loop tuning method.

    Args:
        props: UltimateTuningProps containing Ku, Pu, controller type, and method

    Returns:
        PIDParameters: Controller parameters (Kp, Ti, Td)
    """
    Ku, Pu = props.params.Ku, props.params.Pu
    ctrl, method = props.controller, props.method

    match (ctrl, method):
        case ("p", "classic"):
            return PIDParameters(Kp=0.5 * Ku)
        case ("pi", "classic"):
            return PIDParameters(Kp=0.45 * Ku, Ti=Pu / 1.2)
        case ("pd", "classic"):
            return PIDParameters(Kp=0.8 * Ku, Td=Pu / 8.0)
        case ("pid", "classic"):
            return PIDParameters(Kp=0.6 * Ku, Ti=Pu / 2.0, Td=Pu / 8.0)
        case ("pid", "some_overshoot"):
            return PIDParameters(Kp=(1.0 / 3.0) * Ku, Ti=Pu / 2.0, Td=Pu / 3.0)
        case ("pid", "no_overshoot"):
            return PIDParameters(Kp=0.20 * Ku, Ti=Pu / 2.0, Td=Pu / 3.0)
        case _:
            raise ValueError(
                f"Unsupported controller/method combination: "
                f"controller='{ctrl}', method='{method}'"
            )


# List of all tools for agent
ALL_TOOLS = [
    get_all_model_descriptions,
    get_model_description,
    get_fmu_names,
    simulate_tool,
    generate_step_tool,
    find_peaks_tool,
    analyse_step_response,
    zn_pid_tuning,
]
