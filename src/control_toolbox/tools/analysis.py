import numpy as np
from scipy.signal import find_peaks as scipy_find_peaks
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel, Field
from control_toolbox.schema import ResponseModel, DataModel, Source, AttributesGroup

########################################################
# SCHEMAS
########################################################
class Point(BaseModel):
    """
    A data point.
    """
    timestamp: float = Field(..., description="Timestamp of the data point.")
    value: float = Field(..., description="Value of the data point.")
    description: Optional[str] = Field(default=None, description="Description of the data point.")

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

class PeakAttributes(BaseModel):
    signal_name: str = Field(..., description="Name of the signal.")
    timestamps: List[float] = Field(..., description="List of timestamps in the signal.")
    peak_values: List[float] = Field(..., description="List of values in the signal.")
    average_peak_period: float = Field(..., description="Average period of the peaks")
    properties: Dict[str, float] = Field(..., description="Properties of the peaks")

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
# TOOLS FUNCTIONS
########################################################
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

def find_peaks(data: DataModel, props: FindPeaksProps) -> ResponseModel:
    """
    Find peaks inside a signal based on peak properties.

    This function takes DataModel and finds all local maxima by simple comparison of neighboring values.
    Optionally, a subset of these peaks can be selected by specifying conditions for a peak's properties.
    """
    t = np.asarray(data.timestamps, dtype=float)

    peak_attributes = []
    for signal in data.signals:
        x = np.asarray(signal.values, dtype=float)
        peaks, properties = scipy_find_peaks(x, height=props.height, threshold=props.threshold, distance=props.distance, prominence=props.prominence, width=props.width, wlen=props.wlen, rel_height=props.rel_height, plateau_size=props.plateau_size)
    
        peak_timestamps = [t[p] for p in peaks]
        peak_values = [x[p] for p in peaks]

        if len(peak_timestamps) >= 2:
            average_peak_period = float(np.mean(np.diff(peak_timestamps)))
        else:
            # If less than 2 peaks, set period to NaN or 0
            average_peak_period = float("nan")
        
        peak_attributes.append(PeakAttributes(
            signal_name=signal.name,
            timestamps=peak_timestamps,
            peak_values=peak_values,
            average_peak_period=average_peak_period,
            properties=properties
        ))

    # collect results in attribute groups
    peaks_attribute_group = AttributesGroup(
        title="Peak-detection results",
        attributes=peak_attributes,
        description=f"Detected peaks in all signals"
    )
                
    return ResponseModel(
        source=Source(tool_name="find_peaks_tool"),
        attributes=[peaks_attribute_group]
    )

class SettlingTimeProps(BaseModel):
    """
    Properties for finding steady state time point of a signal.
    """
    tolerance: float = Field(default=0.02, description="Tolerance for the steady state time point stays within a threshold (percentage) of steady-state value.")

class SettlingTime(BaseModel):
    signal_name: str = Field(..., description="Name of the signal.")
    settling_time: float = Field(..., description="Settling time of the signal.")

def find_settling_time(data: DataModel, props: SettlingTimeProps) -> ResponseModel:
    """
    Finds the settling time of each signal in the data. The settling time is defined as the
    first time point where the signal remains within a specified tolerance (percentage) of
    its final value (i.e., steady-state level) for the remainder of the signal.
    """
    t = np.asarray(data.timestamps, dtype=float)
    if t.size == 0:
        raise ValueError("No timestamps in data")

    tol = props.tolerance
    settling_attributes = []

    for idx, s in enumerate(data.signals):
        x = np.asarray(s.values, dtype=float)
        steady_state = x[-1]

        # bounds for settling region
        ub = steady_state * (1 + tol)
        lb = steady_state * (1 - tol)

        # find point where signal stays within bounds
        within_band = (x >= lb) & (x <= ub)

        settling_time = float("nan")
        settling_value = float("nan")

        for i in range(len(within_band)):
            if within_band[i:].all():
                settling_time = float(t[i])
                settling_value = float(x[i])
                break

        # Add result as an Attribute entry
        settling_attributes.append(
            SettlingTime(
                signal_name=s.name,
                settling_time=settling_time
            )
        )

    # All done — now return a full response
    return ResponseModel(
        source=Source(tool_name="find_settling_time_tool", arguments=props.model_dump()),
        attributes=[
            AttributesGroup(
                title="Settling time results",
                attributes=settling_attributes,
                description="Settling times for each signal based on tolerance band."
            )
        ]
    )
        


