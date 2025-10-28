"""Tool to identify FOPDT model parameters from step response."""

import numpy as np
from typing import Dict, Any, List
from langchain_core.tools import tool


@tool
def identify_fopdt_tool(
    time: List[float],
    output: List[float],
    input_step_time: float,
    input_step_magnitude: float,
) -> Dict[str, Any]:
    """Identify FOPDT model parameters (K, T, L) from open-loop step response.
    
    Uses the 63% method as described in Lambda tuning documentation:
    - Dead time L: Time when output first starts to change after step input
    - Static gain K: Final steady-state change / input step magnitude  
    - Time constant T: Time to reach 63% of total change (excluding dead time)
    
    Args:
        time: Time vector from simulation [seconds]
        output: Output signal values (y) from simulation
        input_step_time: Time when step input was applied [seconds]
        input_step_magnitude: Magnitude of the step change in input
        
    Returns:
        Dictionary containing identified FOPDT parameters K, T, L and additional metrics.
    """
    time_arr = np.array(time)
    output_arr = np.array(output)
    
    # Find initial value (average before step)
    pre_step_mask = time_arr < input_step_time
    if np.any(pre_step_mask):
        y_initial = np.mean(output_arr[pre_step_mask])
    else:
        y_initial = output_arr[0]
    
    # Find final value (average of last 20% of data)
    final_mask = time_arr > (time_arr[-1] - (time_arr[-1] - input_step_time) * 0.2)
    y_final = np.mean(output_arr[final_mask])
    
    # Total change in output
    y_change = y_final - y_initial
    
    # Calculate static gain K
    if abs(input_step_magnitude) > 1e-10:
        K = y_change / input_step_magnitude
    else:
        K = 0.0
    
    # Find dead time L (when output exceeds 2% of total change)
    threshold = y_initial + 0.02 * y_change
    post_step_mask = time_arr >= input_step_time
    
    if y_change > 0:
        response_start_idx = np.where((time_arr >= input_step_time) & (output_arr > threshold))[0]
    else:
        response_start_idx = np.where((time_arr >= input_step_time) & (output_arr < threshold))[0]
    
    if len(response_start_idx) > 0:
        t0 = time_arr[response_start_idx[0]]
        L = t0 - input_step_time
    else:
        L = 0.0
    
    # Find time constant T (time to reach 63% of change from start of response)
    y_63 = y_initial + 0.63 * y_change
    
    if y_change > 0:
        t63_idx = np.where((time_arr >= t0) & (output_arr >= y_63))[0]
    else:
        t63_idx = np.where((time_arr >= t0) & (output_arr <= y_63))[0]
    
    if len(t63_idx) > 0:
        t_63 = time_arr[t63_idx[0]]
        T = t_63 - t0
    else:
        T = 1.0  # Default fallback
    
    # Ensure physical validity
    if T <= 0:
        T = 1.0
    if L < 0:
        L = 0.0
    
    return {
        "K": float(K),
        "T": float(T),
        "L": float(L),
        "y_initial": float(y_initial),
        "y_final": float(y_final),
        "y_change": float(y_change),
        "response_start_time": float(t0) if 't0' in locals() else float(input_step_time),
        "model_string": f"G(s) = {K:.4f} * exp(-{L:.4f}*s) / ({T:.4f}*s + 1)",
    }

