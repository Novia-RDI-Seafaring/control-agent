"""Tool to generate input signals for FMU simulations."""

import numpy as np
from typing import Dict, Any, Literal
from langchain_core.tools import tool


@tool
def create_step_signal_tool(
    signal_name: str,
    step_time: float,
    step_level: float,
    initial_level: float = 0.0,
    start_time: float = 0.0,
    stop_time: float = 60.0,
    step_size: float = 0.1,
) -> Dict[str, Any]:
    """Create a step input signal for FMU simulation.
    
    Args:
        signal_name: Name of the input signal (e.g., 'setpoint', 'u_manual')
        step_time: Time when the step change occurs [seconds]
        step_level: Final value after the step change
        initial_level: Initial value before the step change (default: 0.0)
        start_time: Simulation start time [seconds] (default: 0.0)
        stop_time: Simulation stop time [seconds] (default: 60.0)
        step_size: Time step size [seconds] (default: 0.1)
        
    Returns:
        Dictionary containing time vector and signal values that can be used in simulation.
    """
    # Create time vector
    n = int(round((stop_time - start_time) / step_size)) + 1
    time_vector = np.linspace(start_time, stop_time, n, dtype=float)
    
    # Create step signal
    signal_values = np.where(time_vector >= step_time, step_level, initial_level)
    
    return {
        "signal_name": signal_name,
        "time": time_vector.tolist(),
        "values": signal_values.tolist(),
        "step_time": step_time,
        "step_level": step_level,
        "initial_level": initial_level,
    }


@tool
def create_constant_signal_tool(
    signal_name: str,
    constant_value: float,
    start_time: float = 0.0,
    stop_time: float = 60.0,
    step_size: float = 0.1,
) -> Dict[str, Any]:
    """Create a constant input signal for FMU simulation.
    
    Args:
        signal_name: Name of the input signal
        constant_value: Constant value for the entire duration
        start_time: Simulation start time [seconds] (default: 0.0)
        stop_time: Simulation stop time [seconds] (default: 60.0)
        step_size: Time step size [seconds] (default: 0.1)
        
    Returns:
        Dictionary containing time vector and signal values.
    """
    n = int(round((stop_time - start_time) / step_size)) + 1
    time_vector = np.linspace(start_time, stop_time, n, dtype=float)
    signal_values = np.full_like(time_vector, constant_value)
    
    return {
        "signal_name": signal_name,
        "time": time_vector.tolist(),
        "values": signal_values.tolist(),
        "constant_value": constant_value,
    }

