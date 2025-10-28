"""Tool to analyze simulation results and calculate performance metrics."""

import numpy as np
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool


@tool
def calculate_metrics_tool(
    time: List[float],
    output: List[float],
    setpoint: Optional[List[float]] = None,
    step_time: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate performance metrics for closed-loop step response.
    
    Calculates standard control system performance metrics:
    - Rise time (10% to 90% of final value)
    - Settling time (within 2% of final value)
    - Overshoot (percentage)
    - Peak time
    - Steady-state error
    
    Args:
        time: Time vector from simulation [seconds]
        output: Output signal values (y) from simulation
        setpoint: Setpoint signal values (optional, for steady-state error)
        step_time: Time when step occurred (optional, for better metric calculation)
        
    Returns:
        Dictionary containing performance metrics.
    """
    time_arr = np.array(time)
    output_arr = np.array(output)
    
    # Determine initial and final values
    if step_time is not None:
        pre_step_mask = time_arr < step_time
        if np.any(pre_step_mask):
            y_initial = np.mean(output_arr[pre_step_mask])
        else:
            y_initial = output_arr[0]
        
        # Analyze response after step
        post_step_mask = time_arr >= step_time
        time_post = time_arr[post_step_mask]
        output_post = output_arr[post_step_mask]
    else:
        y_initial = output_arr[0]
        time_post = time_arr
        output_post = output_arr
    
    # Final value (average of last 20% of data)
    y_final = np.mean(output_post[-int(len(output_post) * 0.2):])
    
    # Total change
    y_change = y_final - y_initial
    
    # Rise time (10% to 90%)
    y_10 = y_initial + 0.10 * y_change
    y_90 = y_initial + 0.90 * y_change
    
    rise_time = None
    if abs(y_change) > 1e-10:
        if y_change > 0:
            t_10_idx = np.where(output_post >= y_10)[0]
            t_90_idx = np.where(output_post >= y_90)[0]
        else:
            t_10_idx = np.where(output_post <= y_10)[0]
            t_90_idx = np.where(output_post <= y_90)[0]
        
        if len(t_10_idx) > 0 and len(t_90_idx) > 0:
            rise_time = float(time_post[t_90_idx[0]] - time_post[t_10_idx[0]])
    
    # Overshoot
    overshoot_percent = 0.0
    peak_time = None
    peak_value = None
    
    if abs(y_change) > 1e-10:
        if y_change > 0:
            peak_idx = np.argmax(output_post)
            peak_value = output_post[peak_idx]
            if peak_value > y_final:
                overshoot_percent = ((peak_value - y_final) / abs(y_change)) * 100
                peak_time = float(time_post[peak_idx])
        else:
            peak_idx = np.argmin(output_post)
            peak_value = output_post[peak_idx]
            if peak_value < y_final:
                overshoot_percent = ((y_final - peak_value) / abs(y_change)) * 100
                peak_time = float(time_post[peak_idx])
    
    # Settling time (within 2% of final value)
    settling_time = None
    tolerance = 0.02 * abs(y_change)
    
    # Find last time signal exceeds tolerance band
    outside_band = np.abs(output_post - y_final) > tolerance
    if np.any(outside_band):
        last_outside_idx = np.where(outside_band)[0][-1]
        if last_outside_idx < len(time_post) - 1:
            settling_time = float(time_post[last_outside_idx + 1])
            if step_time is not None:
                settling_time = settling_time - step_time
    
    # Steady-state error
    steady_state_error = None
    if setpoint is not None:
        setpoint_arr = np.array(setpoint)
        if len(setpoint_arr) == len(time_arr):
            # Use final setpoint value
            final_setpoint = setpoint_arr[-1]
            steady_state_error = float(final_setpoint - y_final)
    
    return {
        "rise_time": rise_time,
        "settling_time": settling_time,
        "overshoot_percent": float(overshoot_percent),
        "peak_time": peak_time,
        "peak_value": float(peak_value) if peak_value is not None else None,
        "steady_state_error": steady_state_error,
        "initial_value": float(y_initial),
        "final_value": float(y_final),
        "total_change": float(y_change),
    }

