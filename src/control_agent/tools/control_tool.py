# fmi_tools.py - Using control_toolbox

from typing import List
from pathlib import Path

from control_toolbox.core import DataModel, Signal, ResponseModel, Source
from control_toolbox.tools.utils import data_model_to_ndarray, ndarray_to_data_model
from control_toolbox.tools.simulation import (
    simulate as _simulate,
    SimulationProps,
    simulate_step_response as _simulate_step_response,
)
from control_toolbox.tools.signals import (
    generate_step as _generate_step,
    StepProps as ControlStepProps,
    TimeRange,
)
from control_toolbox.tools.information import (
    get_fmu_names as _get_fmu_names,
    get_model_description as _get_model_description,
    FMUInfo,
    FMUCollection,
)
from control_toolbox.tools.analysis import (
    find_peaks as _find_peaks,
    find_characteristic_points as _find_characteristic_points,
    find_settling_time as _find_settling_time,
    FindPeaksProps as ControlFindPeaksProps,
    SettlingTimeProps,
)
from control_toolbox.config import get_fmu_dir
from fmpy import simulate_fmu
from scipy.signal import find_peaks
import numpy as np

# Re-export schemas that match the original interface
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, Literal

# Default FMU directory path
DEFAULT_FMU_DIR = (Path(__file__).parents[2] / "models" / "fmus").resolve()

# Schema compatibility layer
class StepProps(BaseModel):
    signal_name: str = Field(default="input", description="Name of the signal")
    time_range: TimeRange = Field(
        default_factory=lambda: TimeRange(start=0.0, stop=1.0, sampling_time=0.1),
        description="Time range over which the step signal is generated",
    )
    step_time: float = Field(default=0.1, description="Time at which the step occurs")
    initial_value: float = Field(default=0.0, description="Initial value of the step signal")
    final_value: float = Field(default=1.0, description="Final value of the step signal")

class SimulationModel(BaseModel):
    fmu_name: str = Field(description="Name of the FMU model to simulate")
    start_time: Optional[float] = Field(default=0.0, description="Simulation start time")
    stop_time: Optional[float] = Field(default=1.0, description="Simulation stop time")
    step_size: Optional[float] = Field(default=None, description="Simulation step size")
    input: Optional[DataModel] = Field(default=None, description="DataModel containing input signals")
    output: Optional[List[str]] = Field(default=None, description="Sequence of output variable names to record")
    output_interval: Optional[float] = Field(default=None, description="Interval for sampling the output")
    start_values: Optional[Dict[str, Any]] = Field(default=None, description="Dictionary of initial parameter and input values")

class AnalysisProps(BaseModel):
    settling_time_treshhold: float = Field(default=0.02, description="Threshold for settling time")
    rise_time_limits: List[float] = Field(default=[0.1, 0.9], description="Rise time limits")

class FindPeaksProps(BaseModel):
    height: Optional[float] = None
    threshold: Optional[float] = None
    distance: Optional[float] = None
    prominence: Optional[float] = None
    width: Optional[float] = None
    wlen: Optional[int] = None
    rel_height: Optional[float] = 0.5
    plateau_size: Optional[int] = None

class Peak(BaseModel):
    timestamp: float
    value: float

class FindPeaksResult(BaseModel):
    peaks: List[Peak]
    average_peak_period: float
    properties: Dict[str, Any]

class CharacteristicPoints(BaseModel):
    p0: List[float]
    p10: List[float]
    p63: List[float]
    p90: List[float]
    p98: List[float]
    pRT0: List[float]
    pRT1: List[float]
    pST: List[float]
    pPeak: List[float]
    pUndershoot: List[float]

class StepResponseAnalysis(BaseModel):
    characteristic_points: CharacteristicPoints
    rise_time: float
    settling_time: float
    settling_min: float
    settling_max: float
    overshoot: Optional[float] = None
    undershoot: Optional[float] = None
    peaks: List[Peak]

class UltimateGainParameters(BaseModel):
    Ku: float
    Pu: float

class UltimateTuningProps(BaseModel):
    params: UltimateGainParameters
    controller: Literal["p", "pi", "pd", "pid"]
    method: Literal["classic", "some_overshoot", "no_overshoot"] = "classic"

class PIDParameters(BaseModel):
    Kp: float = 1.0
    Ti: float = float("inf")
    Td: float = 0.0

class PlotHttpURL(BaseModel):
    description: str
    url: HttpUrl

#### Figures ####
def get_figure() -> Signal:
    """Use the signal and title from the final datamodel to generate figure"""
    # Placeholder - implement based on your needs
    pass

def make_dash_layout(inputs: DataModel, outputs: DataModel, port: int = 8051) -> PlotHttpURL:
    # Placeholder - implement based on your needs
    pass

######### Simulation TOOLS #########

def get_all_model_descriptions() -> FMUCollection:
    """Lists all FMU models in the directory and their information."""
    FMU_DIR = get_fmu_dir()
    result = _get_model_description(FMU_DIR)
    # Convert ResponseModel to FMUCollection
    if isinstance(result.payload, list):
        fmus_dict = {fmu.name: fmu for fmu in result.payload}
        return FMUCollection(fmus=fmus_dict)
    return result.payload if isinstance(result.payload, FMUCollection) else FMUCollection(fmus={})

def get_model_description(fmu_name: str) -> FMUInfo:
    """Gets the model description of a specific FMU model."""
    print(f"[DEBUG] running description tool")
    FMU_DIR = get_fmu_dir()
    result = _get_model_description(fmu_name, FMU_DIR)
    return result.payload if isinstance(result.payload, FMUInfo) else result.payload

def get_fmu_names() -> List[str]:
    """Lists the models in the FMU directory."""
    print(f"[DEBUG] running get fmu names tool")
    FMU_DIR = get_fmu_dir()
    print(f"[DEBUG] Looking for FMUs in: {FMU_DIR}")
    print(f"[DEBUG] Directory exists: {FMU_DIR.exists()}")
    
    if not FMU_DIR.exists():
        print(f"[ERROR] FMU directory does not exist: {FMU_DIR}")
        return []
    
    try:
        result = _get_fmu_names(FMU_DIR)
        names = result.payload if isinstance(result.payload, list) else []
        print(f"[DEBUG] Found {len(names)} FMU models: {names}")
        return names
    except Exception as e:
        print(f"[ERROR] Error getting FMU names: {e}")
        return []

def simulate_tool(sim: SimulationModel) -> DataModel:
    """
    ### Tool: simulate_fmu_model

    Args:
        sim: SimulationModel containing the simulation parameters
        
    Returns:
        DataModel: simulation results
    """
    print(f"[DEBUG] running simulation tool")
    FMU_DIR = get_fmu_dir()
    if sim.start_values is None:
        sim.start_values = {}
    
    fmu_path = FMU_DIR / f"{sim.fmu_name}.fmu"
    if not fmu_path.is_file():
        raise FileNotFoundError(f"FMU not found: {fmu_path}")
    
    
    # Convert to control_toolbox SimulationProps
    sim_props = SimulationProps(
        fmu_name=sim.fmu_name,
        start_time=sim.start_time,
        stop_time=sim.stop_time,
        step_size=sim.step_size, # sim.step_size,
        input=sim.input,
        output=sim.output,
        output_interval=sim.output_interval, # sim.output_interval,
        start_values=sim.start_values,
    )

    # Use control_toolbox simulate, but extract DataModel
    result = _simulate(sim_props, FMU_DIR, generate_plot=False)
    return result.data if result.data else DataModel(timestamps=[], signals=[])

'''
def generate_step_tool(step: StepProps) -> DataModel:
    """Generates a step signal."""
    # Convert to control_toolbox StepProps
    control_step = ControlStepProps(
        signal_name=step.signal_name,
        time_range=step.time_range,
        step_time=step.step_time,
        initial_value=step.initial_value,
        final_value=step.final_value,
    )
    
    result = _generate_step(control_step)
    return result.data if result.data else DataModel(timestamps=[], signals=[])
'''
def generate_step_tool(step: StepProps) -> DataModel:
    """Generates a step signal."""
    print(f"[DEBUG] running generating step (signal) tool")
    # Convert to control_toolbox StepProps
    control_step = ControlStepProps(
        signal_name=step.signal_name,
        time_range=step.time_range,
        step_time=step.step_time,
        initial_value=step.initial_value,
        final_value=step.final_value,
    )
    
    result = _generate_step(control_step)
    if not result.data:
        return DataModel(timestamps=[], signals=[])
    
    data = result.data
    
    # Validate lengths match (control_toolbox should create matching arrays, but verify)
    timestamp_count = len(data.timestamps)
    validated_signals = []
    for signal in data.signals:
        values = list(signal.values)  # Convert to list
        if len(values) != timestamp_count:
            # Fix mismatch - this shouldn't happen with control_toolbox, but safety check
            if len(values) < timestamp_count:
                # Pad with last value
                values.extend([values[-1] if values else step.final_value] * (timestamp_count - len(values)))
            else:
                # Truncate
                values = values[:timestamp_count]
        
        validated_signals.append(Signal(
            name=signal.name,
            values=values,
            unit=getattr(signal, 'unit', None)
        ))
    
    # Create new DataModel to ensure validation passes
    return DataModel(timestamps=list(data.timestamps), signals=validated_signals)

def find_peaks_tool(signal_name: str, data: DataModel, props: FindPeaksProps) -> FindPeaksResult:
    """Find peaks inside a signal based on peak properties."""
    print(f"[DEBUG] running finding peak tool")
    # Convert to control_toolbox FindPeaksProps
    control_props = ControlFindPeaksProps(
        height=props.height,
        threshold=props.threshold,
        distance=props.distance,
        prominence=props.prominence,
        width=props.width,
        wlen=props.wlen,
        rel_height=props.rel_height,
        plateau_size=props.plateau_size,
    )
    
    result = _find_peaks(data, control_props)
    
    # Extract peak data from ResponseModel
    if result.attributes and len(result.attributes) > 0:
        peak_attrs = result.attributes[0].attributes
        if peak_attrs and len(peak_attrs) > 0:
            # Find the signal we're looking for
            for attr in peak_attrs:
                if hasattr(attr, 'signal_name') and attr.signal_name == signal_name:
                    peaks = [
                        Peak(timestamp=t, value=v)
                        for t, v in zip(attr.timestamps, attr.peak_values)
                    ]
                    return FindPeaksResult(
                        peaks=peaks,
                        average_peak_period=attr.average_peak_period,
                        properties=attr.properties,
                    )
    
    # Fallback: use scipy directly
    t = np.asarray(data.timestamps, dtype=float)
    for s in data.signals:
        if s.name == signal_name:
            x = np.asarray(s.values, dtype=float)
            peaks_indices, properties = find_peaks(
                x,
                height=props.height,
                threshold=props.threshold,
                distance=props.distance,
                prominence=props.prominence,
                width=props.width,
                wlen=props.wlen,
                rel_height=props.rel_height,
                plateau_size=props.plateau_size,
            )
            peak_timestamps = [t[p] for p in peaks_indices]
            peaks = [Peak(timestamp=t[p], value=x[p]) for p in peaks_indices]
            avg_period = float(np.mean(np.diff(peak_timestamps))) if len(peak_timestamps) >= 2 else float("nan")
            return FindPeaksResult(
                peaks=peaks,
                average_peak_period=avg_period,
                properties={k: float(v) if isinstance(v, (list, np.ndarray)) and len(v) > 0 else v
                           for k, v in properties.items()},
            )
    
    raise ValueError(f"Signal {signal_name} not found in DataModel")

def analyse_step_response(
    signal_name: str,
    data: DataModel,
    props: AnalysisProps,
) -> StepResponseAnalysis:
    """
    Analyses a step response using control_toolbox functions.
    """
    print(f"[DEBUG] running analysing tool")
    t = np.asarray(data.timestamps, dtype=float)
    for s in data.signals:
        if s.name == signal_name:
            y = np.asarray(s.values, dtype=float)
            break
    else:
        available_signals = [s.name for s in data.signals]
        raise ValueError(
            f"Signal '{signal_name}' not found in DataModel. "
            f"Available signals: {available_signals}"
        )

    # Use control_toolbox analysis functions
    settling_props = SettlingTimeProps(tolerance=props.settling_time_treshhold)
    settling_result = _find_settling_time(data, settling_props)
    
    # Extract characteristic points
    char_points_result = _find_characteristic_points(data)
    
    # Get peaks
    peaks_result = find_peaks_tool(signal_name, data, FindPeaksProps())
    
    # Extract data from results and build StepResponseAnalysis
    # This is a simplified version - you may need to adapt based on actual control_toolbox response structure
    y_start, y_final = float(y[0]), float(y[-1])
    dy = y_final - y_start
    
    # Build characteristic points (simplified - adapt based on control_toolbox output)
    char_points = CharacteristicPoints(
        p0=[float(t[0]), y_start],
        p10=[float("nan"), float("nan")],  # Extract from char_points_result
        p63=[float("nan"), float("nan")],
        p90=[float("nan"), float("nan")],
        p98=[float("nan"), float("nan")],
        pRT0=[float("nan"), float("nan")],
        pRT1=[float("nan"), float("nan")],
        pST=[float("nan"), float("nan")],
        pPeak=[float("nan"), float("nan")],
        pUndershoot=[float("nan"), float("nan")],
    )
    
    # Extract settling time
    settling_time = float("nan")
    if settling_result.attributes and len(settling_result.attributes) > 0:
        for attr in settling_result.attributes[0].attributes:
            if hasattr(attr, 'signal_name') and attr.signal_name == signal_name:
                settling_time = attr.settling_time
                break
    
    return StepResponseAnalysis(
        characteristic_points=char_points,
        rise_time=float("nan"),  # Calculate from char_points
        settling_time=settling_time,
        settling_min=float(np.min(y)),
        settling_max=float(np.max(y)),
        overshoot=None,
        undershoot=None,
        peaks=peaks_result.peaks,
    )

def zn_pid_tuning(props: UltimateTuningProps) -> PIDParameters:
    """
    Compute PID controller parameters using the Ziegler-Nichols closed-loop
    (also called ultimate gain or continuous-cycling) tuning method.
    """
    print(f"[DEBUG] running zn pid tuning tool")
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