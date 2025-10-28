"""Tool to set FMU parameters."""

from typing import Dict, Any, Literal, Optional
from langchain_core.tools import tool


@tool
def set_fmu_parameters_tool(
    mode: Optional[Literal["manual", "automatic"]] = None,
    Kp: Optional[float] = None,
    Ti: Optional[float] = None,
    K: Optional[float] = None,
    T: Optional[float] = None,
    L: Optional[float] = None,
) -> Dict[str, Any]:
    """Set FMU model parameters for PI controller and FOPDT system.
    
    Controller Parameters:
    - mode: Controller operating mode
        * "manual": Operator directly determines control signal u(t) (open-loop)
        * "automatic": PI control law is active (closed-loop)
    - Kp: PI controller proportional gain
    - Ti: PI controller integral time constant [seconds]
    
    Plant Parameters (FOPDT system):
    - K: Static gain of the plant
    - T: Time constant of the plant [seconds]
    - L: Dead time of the plant [seconds]
    
    Args:
        mode: Controller mode ('manual' or 'automatic')
        Kp: Proportional gain (K_p or K_c)
        Ti: Integral time constant (T_i) [seconds]
        K: Plant static gain
        T: Plant time constant [seconds]
        L: Plant dead time [seconds]
        
    Returns:
        Dictionary of parameters to be passed to the FMU simulation.
    """
    parameters = {}
    
    # Controller parameters
    if mode is not None:
        # Convert to boolean for FMU: True = automatic, False = manual
        parameters["mode"] = (mode == "automatic")
    
    if Kp is not None:
        parameters["Kp"] = float(Kp)
    
    if Ti is not None:
        # For disabling integral action (Ziegler-Nichols step), use very large Ti
        if Ti == float('inf'):
            parameters["Ti"] = 1e10  # Practical infinity
        else:
            parameters["Ti"] = float(Ti)
    
    # Plant parameters
    if K is not None:
        parameters["K"] = float(K)
    
    if T is not None:
        parameters["T"] = float(T)
    
    if L is not None:
        parameters["L"] = float(L)
    
    return {
        "parameters": parameters,
        "description": f"FMU parameters configured: {', '.join(f'{k}={v}' for k, v in parameters.items())}",
    }

