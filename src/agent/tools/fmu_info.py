"""Tool to retrieve FMU model information."""

import os
from pathlib import Path
from typing import Any, Dict
from langchain_core.tools import tool
from fmpy import read_model_description


@tool
def get_fmu_info_tool(fmu_path: str = None) -> Dict[str, Any]:
    """Get information about an FMU model including parameters, inputs, and outputs.
    
    Args:
        fmu_path: Path to the FMU file. If None, uses FMU_PATH from environment.
        
    Returns:
        Dictionary containing model description, parameters, inputs, outputs, and metadata.
    """
    if fmu_path is None:
        fmu_path = os.getenv("FMU_PATH", "models/fmus/fopdt_pi.fmu")
    
    fmu_path = Path(fmu_path).as_posix()
    
    model_description = read_model_description(fmu_path)
    
    # Extract model variables
    parameters = []
    inputs = []
    outputs = []
    
    for var in model_description.modelVariables:
        var_info = {
            "name": var.name,
            "description": getattr(var, "description", ""),
            "causality": getattr(var, "causality", ""),
            "variability": getattr(var, "variability", ""),
            "start": getattr(var, "start", None),
        }
        
        causality = getattr(var, "causality", None)
        if causality == "parameter":
            parameters.append(var_info)
        elif causality == "input":
            inputs.append(var_info)
        elif causality == "output":
            outputs.append(var_info)
    
    # Get default experiment settings
    default_experiment = getattr(model_description, "defaultExperiment", None)
    experiment_info = {}
    if default_experiment:
        experiment_info = {
            "startTime": getattr(default_experiment, "startTime", 0.0),
            "stopTime": getattr(default_experiment, "stopTime", 60.0),
            "stepSize": getattr(default_experiment, "stepSize", 0.1),
        }
    
    return {
        "modelName": model_description.modelName,
        "fmiVersion": model_description.fmiVersion,
        "description": getattr(model_description, "description", ""),
        "generationTool": getattr(model_description, "generationTool", ""),
        "generationDateAndTime": getattr(model_description, "generationDateAndTime", ""),
        "parameters": parameters,
        "inputs": inputs,
        "outputs": outputs,
        "defaultExperiment": experiment_info,
    }

