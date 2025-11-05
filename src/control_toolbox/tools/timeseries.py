from pydantic import BaseModel, Field, model_validator
from control_toolbox.schema import ResponseModel, DataModel, Signal, Source
from typing import List, Tuple, Optional, Dict
import numpy as np
from datetime import datetime, timezone
from scipy.signal import find_peaks as scipy_find_peaks

########################################################
# SCHEMAS
########################################################
class TimeRange(BaseModel):
    start: float = Field(..., description="Start time of the time range")
    stop: float = Field(..., description="Stop time of the time range")
    sampling_time: float = Field(..., gt=0, description="Sampling time of the time range")

    @model_validator(mode="after")
    def _check_bounds(self):
        if self.stop <= self.start:
            raise ValueError("stop must be greater than start")
        return self
    
    @model_validator(mode="after")
    def _check_sampling_time(self):
        if self.sampling_time <= 0:
            raise ValueError("sampling_time must be greater than 0")
        return self

class StepProps(BaseModel):
    signal_name: str = Field(default="input", description="Name of the signal")
    time_range: TimeRange = Field(
        default_factory=lambda: TimeRange(start=0.0, stop=1.0, sampling_time=0.1),
        description="Time range over which the step signal is generated",
    )
    step_time: float = Field(default=0.1, description="Time at which the step occurs")
    initial_value: float = Field(default=0.0, description="Initial value of the step signal")
    final_value: float = Field(default=1.0, description="Final value of the step signal")

    @model_validator(mode="after")
    def _check_step_time(self):
        tr = self.time_range
        if not (tr.start <= self.step_time <= tr.stop):
            raise ValueError("step_time must be within [start, stop]")
        return self

class ImpulseProps(BaseModel):
    """
    Properties for generating a discrete-time impulse (Dirac delta) signal.
    """
    signal_name: str = Field(
        default="input",
        description="Name of the signal carrying the impulse."
    )
    time_range: TimeRange = Field(
        default_factory=lambda: TimeRange(start=0.0, stop=1.0, sampling_time=0.1),
        description="Time range over which the impulse signal is defined."
    )
    impulse_time: float = Field(
        default=0.1,
        description="Time at which the unit impulse occurs (must fall within the time range)."
    )
    magnitude: float = Field(
        default=1.0,
        description="Amplitude of the impulse (default 1.0 for unit impulse)."
    )

    @model_validator(mode="after")
    def _check_impulse_time(self):
        tr = self.time_range
        if not (tr.start <= self.impulse_time <= tr.stop):
            raise ValueError("impulse_time must be within [start, stop]")
        return self

class Point(BaseModel):
    """
    Characteristic point.
    """
    timestamp: float = Field(..., description="Timestamp of the characteristic point.")
    value: float = Field(..., description="Value of the characteristic point.")

class CharacteristicPoint(BaseModel):
    """
    Characteristic point.
    """
    name: str = Field(..., description="Name of the characteristic point.")
    description: str = Field(..., description="Description of the characteristic point.")
    point: Point = Field(..., description="Points of the characteristic point.")

class CharacteristicPoints(BaseModel):
    """
    Characteristic points of a step response.
    """
    signal_name: str = Field(..., description="Name of the signal.")
    characteristic_points: List[CharacteristicPoint] = Field(..., description="Points of the characteristic point.")

class FindPeaksProps(BaseModel):
    height: Optional[float] = Field(
        default=None,
        description=(
            "Required height of peaks. Either a number, None, an array matching x or a 2-element sequence of the former."
            "The first element is always interpreted as the minimal and the second, if supplied, as the maximal required height."
        )
    )
    threshold: Optional[float] = Field(
        default=None,
        description=(
            "Required threshold of peaks, the vertical distance to its neighboring samples."
            "Either a number, None, an array matching x or a 2-element sequence of the former."
            "The first element is always interpreted as the minimal and the second, if supplied, as the maximal required threshold."
        )
    )
    distance: Optional[float] = Field(
        default=None,
        description=(
            "Required distance between peaks. The minimum distance between returned peaks. "
            "Smaller peaks are removed first until the condition is fulfilled for all remaining peaks."
        )
    )
    prominence: Optional[float] = Field(
        default=None,
        description=(
            "Required prominence of peaks. Either a number, None, an array matching x or a 2-element sequence of the former."
            "The first element is always interpreted as the minimal and the second, if supplied, as the maximal required prominence."
        )
    )
    width: Optional[float] = Field(
        default=None,
        description=(
            "Required width of peaks in samples. Either a number, None, an array matching x or a 2-element sequence of the former."
            "The first element is always interpreted as the minimal and the second, if supplied, as the maximal required width"
        )
    )
    wlen: Optional[int] = Field(
        default=None,
        description=(
            "Used for calculation of the peaks prominences, thus it is only used if one of the arguments prominence or width is given."
            "See argument wlen in peak_prominences for a full description of its effects."
        )
    )
    rel_height: Optional[float] = Field(
        default=0.5,
        description=(
            "Used for calculation of the peaks width, thus it is only used if width is given."
            "See argument rel_height in peak_widths for a full description of its effects."
        )
    )
    plateau_size: Optional[int] = Field(
        default=None,
        description=(
            "Required size of the flat top of peaks in samples. Either a number, None, an array matching x or a 2-element sequence of the former."
            "The first element is always interpreted as the minimal and the second, if supplied, as the maximal required plateau size."
        )
    )

class FindPeaksResult(BaseModel):
    signal_name: str = Field(..., description="Name of the signal.")
    peaks: List[Point] = Field(
        ...,
        description="List of peaks (timestamps and values) in signal that satisfy all given conditions."
    )
    average_peak_period: float = Field(
        ...,
        description="Average period of the peaks"
    )
    properties: Dict[str, float] = Field(
        ...,
        description="Properties of the peaks"
    )


########################################################
# HELPER FUNCTIONS
########################################################
# Helper: get value at time (with interpolation)
def _get_value(timestamps: List[float], values: List[float], t_val: float) -> float:
    """
    Returns the interpolated value at time `t_val` using linear interpolation.

    - Uses numpy's `interp`, which handles interpolation and edge clipping.
    - Returns NaN for invalid inputs (e.g. mismatched or empty lists).

    Args:
        timestamps: Sorted list of time points.
        values: List of sample values corresponding to timestamps.
        t_val: Query time.

    Returns:
        Interpolated value, or NaN if input is invalid.
    """
    return float(np.interp(
        x=t_val,
        xp=timestamps,
        fp=values,
        left=values[0],      # Clip to first value when t_val < timestamps[0]
        right=values[-1]     # Clip to last value when t_val > timestamps[-1]
    ))

# Helper: first crossing of threshold
def _first_cross(
    timestamps: List[float],
    values: List[float],
    threshold: float,
    is_upward: bool = True,
    start_index: int = 0,
) -> Tuple[float, float]:
    """
    Returns the first sample (t, y) after `start_index` where `values` crosses the given `threshold`.
    No interpolation — directly returns the sample time and value.

    Args:
        timestamps: List of sample time points (same length as values).
        values: List of corresponding signal values.
        threshold: Threshold to detect.
        is_upward: True for upward crossing (>=), False for downward crossing (<=).
        start_index: Index to start the search from.

    Returns:
        (time, value) tuple at the first threshold crossing, or (nan, nan) if none.
    """
    t = np.asarray(timestamps)
    y = np.asarray(values)
    yinf = values[-1]

    if is_upward:
        idx = np.where(y[start_index:] >= threshold)[0]
    else:
        idx = np.where(y[start_index:] <= threshold)[0]

    if idx.size > 0:
        i = start_index + idx[0] - 1
        return float(t[i]), float(y[i])
    else:
        return float("nan"), float("nan")

########################################################
# TOOLS
########################################################

def generate_step(step: StepProps) -> ResponseModel:
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

    data = DataModel(
        timestamps=timestamps,
        signals=[Signal(name=step.signal_name, values=values.tolist())]
        )
    return ResponseModel(
        source=Source(tool_name="generate_step_tool"),
        data=data
    )

def generate_impulse(impulse: ImpulseProps) -> ResponseModel:
    """
    Generates a unit impulse signal.
    
    Args:
        impulse: ImpulseProps containing the impulse signal properties
        
    Returns:
        DataModel: Impulse signal

    Example: Generate a unit impulse at t=1 seconds on the time interval [0, 10.0] seconds.
    """
    start = impulse.time_range.start
    stop = impulse.time_range.stop
    dt = impulse.time_range.sampling_time

    # number of samples in interval
    dt = impulse.time_range.sampling_time
    timestamps = np.arange(start, stop + dt, dt)
    values = np.zeros_like(timestamps)
    # index of impulse
    idx = np.argmin(np.abs(timestamps - impulse.impulse_time))
    values[idx] = impulse.magnitude

    data = DataModel(
        timestamps=timestamps,
        signals=[Signal(name=impulse.signal_name, values=values.tolist())]
        )
    return ResponseModel(
        source=Source(tool_name="generate_step_tool"),
        data=data
    )

def find_characteristic_points(data: DataModel) -> ResponseModel:
    """
    Finds the characteristic points of step responses.
    
    Args:
        data: DataModel containing the signal
        
    Returns:
        ResponseModel: Contains **critical points* analyzing step rsponses and finetuning controllers.
            - p0 = (t0,y0) point when output starts to change from initial value.
            - p10 = (t10,y10) point when output first reachest 10% of total change.
            - p63 = (t63,y63) point when output first reachest 63% of total change. Can be used to determine the time constant T of a FOPDT system.
            - p90 = (t90,y90) point when output first reachest 90% of total change.
            - p98 = (t98,y98) point when output first reachest 98% of total change.
    """
    # find the points where the signal changes
    timestamps = data.timestamps

    characteristic_points = []
    for signal in data.signals:
        values = signal.values

        y_final = values[-1]
        t_final = timestamps[-1]
        
        # find the points where the signal changes
        t0, y0 = _first_cross(timestamps, values, 0.0)
        cp0 = CharacteristicPoint(
            name="p0",
            description="Point when output first starts to change from initial value.",
            point=Point(timestamp=t0, value=y0)
        )
        t10, y10 = _first_cross(timestamps, values, 0.1 * y_final)
        cp10 = CharacteristicPoint(
            name="p10",
            description="Point when output first reachest 10% of total change. Used as lower reference point when determining the rise time of a system.",
            point=Point(timestamp=t10, value=y10)
        )
        t63, y63 = _first_cross(timestamps, values, 0.63 * y_final)
        cp63 = CharacteristicPoint(
            name="p63",
            description="Point when output first reachest 63% of total change. Can be used to determine the time constant T of a FOPDT system.",
            point=Point(timestamp=t63, value=y63)
        )
        t90, y90 = _first_cross(timestamps, values, 0.90 * y_final)
        cp90 = CharacteristicPoint(
            name="p90",
            description="Point when output first reachest 90% of total change. Used as upper reference point when determining the rise time of a system.",
            point=Point(timestamp=t90, value=y90)
        )
        cp_final = CharacteristicPoint(
            name="pinf",
            description=f"Steady-state point of the step response as t to infty.",
            point=Point(timestamp=t_final, value=y_final)
        )

        cps = CharacteristicPoints(
            signal_name=signal.name,
            characteristic_points=[cp0, cp10, cp63, cp90, cp_final]
        )
        characteristic_points.append(cps)

    return ResponseModel(
        source=Source(
            tool_name="find_characteristic_points_tool"
            ),
        payload=characteristic_points
    )

def find_peaks(data: DataModel, props: FindPeaksProps) -> FindPeaksResult:
    """
    Find peaks inside a signal based on peak properties.

    This function takes DataModel and finds all local maxima by simple comparison of neighboring values.
    Optionally, a subset of these peaks can be selected by specifying conditions for a peak's properties.
    """
    t = np.asarray(data.timestamps, dtype=float)
    peaks_results = []
    for signal in data.signals:
        x = np.asarray(signal.values, dtype=float)
        peaks, properties = scipy_find_peaks(x, height=props.height, threshold=props.threshold, distance=props.distance, prominence=props.prominence, width=props.width, wlen=props.wlen, rel_height=props.rel_height, plateau_size=props.plateau_size)
    
        peak_timestamps = [t[p] for p in peaks]
        if len(peak_timestamps) >= 2:
            average_peak_period = float(np.mean(np.diff(peak_timestamps)))
        else:
            # If less than 2 peaks, set period to NaN or 0
            average_peak_period = float("nan")
        peaks_results.append(
            FindPeaksResult(
                signal_name=signal.name,
                peaks=[Point(timestamp=t[p], value=x[p]) for p in peaks],
                average_peak_period=average_peak_period,
                properties=properties)
        )

    return ResponseModel(
        source=Source(tool_name="find_peaks_tool"),
        payload=peaks_results
    )