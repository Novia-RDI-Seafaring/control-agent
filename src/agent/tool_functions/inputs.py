# inputs.py

from fmpy import simulate_fmu, read_model_description
from pathlib import Path
from typing import List, Dict, Optional
from .schema import DataModel, Signal
import numpy as np

def ndarray_to_data_model(data: np.ndarray) -> DataModel:
    """
    Convert a structured numpy array from FMPy into a DataModel.

    Args:
        results: Structured numpy array with a 'time' field and one field per variable.

    Returns:
        DataModel: Contains 'timestamps' and 'signals' for each variable.
    """
    if data.dtype.names is None or 'time' not in data.dtype.names:
        raise ValueError("Structured array must have a 'time' field.")

    timestamps = data['time'].tolist()

    signals = []
    for name in data.dtype.names:
        if name != 'time':
            signals.append(
                    Signal(name=name, values=data[name].tolist())
                )
    return DataModel(timestamps=timestamps, signals=signals)

def data_model_to_ndarray(input_model: Optional[DataModel]) -> Optional[np.ndarray]:
    """
    Convert a DataModel of inputs into a structured numpy array for FMPy.

    Args:
        input_model: DataModel containing 'timestamps' and 'signals', or None.

    Returns:
        Structured numpy array with dtype [('time', 'f8'), ...] and one row per timestamp, or None.
    """
    if input_model is None:
        return None
        
    # Extract timestamps and variable names
    timestamps = input_model.timestamps
    n = len(timestamps)
    if n == 0:
        raise ValueError("DataModel.timestamps is empty")

    # list singal names
    signal_names = [s.name for s in input_model.signals]

    # Define structured dtype
    dtype = [("time", "f8")] + [(name, "f8") for name in signal_names]

    # Prepare structured array
    arr = np.zeros(n, dtype=dtype)
    arr["time"] = np.asarray(timestamps, dtype=float)

    # Fill in each signal's values
    for s in input_model.signals:
        values = np.asarray(s.values, dtype=float)
        if len(values) != n:
            raise ValueError(
                f"Signal '{s.name}' length ({len(values)}) does not match timestamps ({n})"
            )
        arr[s.name] = values

    return arr

def create_signal(
        input_name: str,
        timestamps: List[float],
        values: List[float]
) -> DataModel:
    """
    Create a DataModel with a single input signal populated with values.
    Returns:
        Structured numpy array with dtype [('time', 'f8'), ...] and one row per timestamp.
    """
    if len(timestamps) != len(values):
        raise ValueError("Length of timestamps and values must be the same.")
    if not all(timestamps[i] < timestamps[i+1] for i in range(len(timestamps) - 1)):
        raise ValueError("Timestamps must be in ascending order.")

    return DataModel(
        timestamps=timestamps,
        signals=[Signal(name=input_name, values=values)]
    )

def merge_signals(signals: List[DataModel]) -> DataModel:
    """
    Merge multiple DataModel instances into a unified model with shared timestamps.
    Assumes piecewise-constant behavior: values hold until the next change.
    """
    #Build global sorted timestamp list
    new_timestamps = sorted(set(t for model in signals for t in model.timestamps))

    # Prepare output signals
    merged_signals = {}

    for s in signals:
        name = list(s.signals.keys())[0]  # only one signal per model
        ts = s.timestamps
        vs = s.signals[name]

        # Map the known values to timestamps
        signal_map = dict(zip(ts, vs))

        # Fill in values across the global timestamp list using last known value
        filled_values = []
        last_value = 0.0  # or None, or a configurable default

        for t in new_timestamps:
            if t in signal_map:
                last_value = signal_map[t]
            filled_values.append(last_value)

        merged_signals[name] = filled_values

    return DataModel(
        timestamps=new_timestamps,
        signals=merged_signals
    )