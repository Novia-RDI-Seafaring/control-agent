import numpy as np
from typing import Optional
from control_toolbox.schema import DataModel, Signal

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
