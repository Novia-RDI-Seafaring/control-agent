from mcp_fmi_ecc26.utils.fmu import get_fmu_path, get_fmu_simulation_result, create_result_path
from pathlib import Path
from fmpy import read_model_description
from uuid import uuid4

def simulate_fmu_tool(fmu_id: str, note:str = "") -> str:
    """Get information about an FMU model including parameters, inputs, and outputs.
    
    Args:
        fmu_id: ID of the to the FMU file.
        
    Returns:
        Dictionary containing model description, parameters, inputs, outputs, and metadata.
    """
        
    fmu_path = get_fmu_path(fmu_id)
    
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
    
    results = {
        "modelName": model_description.modelName,
        "fmiVersion": model_description.fmiVersion,
        "description": getattr(model_description, "description", ""),
        "generationTool": getattr(model_description, "generationTool", ""),
        "generationDateAndTime": getattr(model_description, "generationDateAndTime", ""),
        "parameters": parameters,
        "inputs": inputs,
        "outputs": outputs,
        "defaultExperiment": experiment_info,
        "note": note,
    }

    path = create_result_path(fmu_id)
    with open(path, "w") as f:
        json.dump(results, f)
    return path