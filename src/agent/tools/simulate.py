"""Tool to simulate FMU models."""

import os
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from fmpy import simulate_fmu, read_model_description


@tool
def simulate_fmu_tool(
    fmu_path: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    input_signals: Optional[List[Dict[str, Any]]] = None,
    start_time: Optional[float] = None,
    stop_time: Optional[float] = None,
    step_size: Optional[float] = None,
) -> Dict[str, Any]:
    """Simulate an FMU model with specified parameters and input signals.
    
    Args:
        fmu_path: Path to the FMU file. If None, uses FMU_PATH from environment.
        parameters: Dictionary of parameter names and values to set (e.g., {'mode': True, 'Kp': 1.0, 'Ti': 2.0})
        input_signals: List of signal dictionaries from create_step_signal_tool or create_constant_signal_tool
        start_time: Simulation start time [seconds]. If None, uses default from FMU.
        stop_time: Simulation stop time [seconds]. If None, uses default from FMU.
        step_size: Time step size [seconds]. If None, uses default from FMU.
        
    Returns:
        Dictionary containing simulation results with time and output variables.
    """
    if fmu_path is None:
        fmu_path = os.getenv("FMU_PATH", "models/fmus/fopdt_pi.fmu")
    
    fmu_path = Path(fmu_path).as_posix()
    
    # Read model description to get defaults
    model_description = read_model_description(fmu_path)
    default_experiment = getattr(model_description, "defaultExperiment", None)
    
    # Get FMU input variables
    fmu_inputs = [v.name for v in model_description.modelVariables if v.causality == 'input']
    
    # Prepare input signals in FMPy format
    input_data = None
    if input_signals:
        # Validate input signals format
        reference_time = None
        reference_length = None
        
        for i, signal in enumerate(input_signals):
            if not isinstance(signal, dict):
                return {
                    "success": False,
                    "error": f"Signal {i} must be a dictionary, got {type(signal).__name__}",
                }
            required_keys = ["signal_name", "time", "values"]
            missing_keys = [k for k in required_keys if k not in signal]
            if missing_keys:
                return {
                    "success": False,
                    "error": f"Signal {i} missing required keys: {missing_keys}. Use create_step_signal_tool to generate proper signal format.",
                }
            
            # Validate lengths match within signal
            time_len = len(signal.get("time", []))
            values_len = len(signal.get("values", []))
            if time_len != values_len:
                return {
                    "success": False,
                    "error": f"Signal '{signal.get('signal_name', i)}' has mismatched lengths: time={time_len}, values={values_len}. Regenerate with create_step_signal_tool.",
                }
            
            # Validate all signals share the same time vector
            if reference_time is None:
                reference_time = signal["time"]
                reference_length = time_len
            else:
                if time_len != reference_length:
                    return {
                        "success": False,
                        "error": f"Signal '{signal.get('signal_name', i)}' has length {time_len} but expected {reference_length}. All signals must use the same start_time/stop_time/step_size. Create all signals with identical time parameters.",
                    }
        
        # Check for time grid alignment across all signals
        time_vector = np.array(input_signals[0]["time"], dtype=float)
        for s in input_signals[1:]:
            if not np.allclose(np.array(s["time"], dtype=float), time_vector):
                return {
                    "success": False,
                    "error": f"Time grid mismatch for signal '{s['signal_name']}'. All signals must use identical time vectors.",
                }
        
        # Validate all required FMU inputs are provided
        provided = {s["signal_name"] for s in input_signals}
        missing = [n for n in fmu_inputs if n not in provided]
        if missing:
            return {
                "success": False,
                "error": f"Missing input(s): {missing}. Add/create signals with exactly these names (case-sensitive).",
            }
        
        # Build structured array with all signals
        dtype_list = [("time", np.float64)]
        for signal in input_signals:
            dtype_list.append((signal["signal_name"], np.float64))
        
        input_data = np.zeros(len(time_vector), dtype=dtype_list)
        input_data["time"] = time_vector
        
        for signal in input_signals:
            input_data[signal["signal_name"]] = np.array(signal["values"])
        
        # When input signals are provided, use their time vector
        # Only override if explicitly specified
        if start_time is None:
            start_time = time_vector[0]
        if stop_time is None:
            stop_time = time_vector[-1]
        if step_size is None:
            # Calculate from signal time vector
            if len(time_vector) > 1:
                step_size = time_vector[1] - time_vector[0]
            else:
                step_size = 0.1
    else:
        # No input signals - use FMU defaults or provided values
        if start_time is None:
            start_time = getattr(default_experiment, "startTime", 0.0) if default_experiment else 0.0
        if stop_time is None:
            stop_time = getattr(default_experiment, "stopTime", 60.0) if default_experiment else 60.0
        if step_size is None:
            step_size = getattr(default_experiment, "stepSize", 0.1) if default_experiment else 0.1
    
    # Prepare start values (parameters)
    start_values = parameters if parameters else {}
    
    # Convert mode parameter if provided as string
    if "mode" in start_values and isinstance(start_values["mode"], str):
        start_values = start_values.copy()  # Don't modify original
        start_values["mode"] = (start_values["mode"] == "automatic")
    
    # Run simulation
    try:
        # When input signals are provided, explicitly pass time parameters to align grids
        if input_data is not None:
            result = simulate_fmu(
                filename=fmu_path,
                start_time=float(time_vector[0]),
                stop_time=float(time_vector[-1]),
                output_interval=float(time_vector[1] - time_vector[0]) if len(time_vector) > 1 else None,
                input=input_data,
                start_values=start_values,
                record_events=True,
            )
        else:
            # No input signals - use explicit time parameters
            result = simulate_fmu(
                filename=fmu_path,
                start_time=start_time,
                stop_time=stop_time,
                output_interval=step_size,
                start_values=start_values,
                record_events=True,
            )
        
        # Convert result to dictionary
        output = {
            "time": result["time"].tolist(),
            "success": True,
        }
        
        # Extract all output variables
        for name in result.dtype.names:
            if name != "time":
                output[name] = result[name].tolist()
        
        # Add metadata
        output["metadata"] = {
            "start_time": start_time,
            "stop_time": stop_time,
            "step_size": step_size,
            "parameters": start_values,
        }
        
        return output
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "parameters": start_values,
        }

