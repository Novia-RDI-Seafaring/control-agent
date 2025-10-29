from mcp_fmi_ecc26.utils.fmu import get_fmu_path, get_result_path, list_fmus, load_result, annotate_result
from pathlib import Path
from fmpy import read_model_description
from uuid import uuid4
from typing import List, Dict, Any
import json

def list_models_tool() -> List[str]:
    """List all available FMU models.
    
    Returns:
        List of filenames of the available FMU models.
    """
    return list_fmus()

def annotate_simulation_tool(simulation_id: str, observation: str = ""):
    """Annotate a simulation.
    
    Args:
        simulation_id: Id of the simulation.
        observation: Note about the simulation.
    """
    
    annotate_result(simulation_id, observation)

def load_result_tool(simulation_id:str):
    """Load result data
    Args:
        simulation_id: Id of the simulation.
    """
    return load_result(simulation_id)


def simulate_fmu_tool(fmu_filename: str, note: str = "") -> Dict[str, Any]:
    """Run simulation of an FMU model.
    
    Args:
        fmu_filename: Filename of the to the FMU file.
        note: Note about the simulation.

    Returns:
        It returns a result id, that can be used to load the result data.
    """

    fmu_path = get_fmu_path(fmu_filename)
    
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
    
    result_id = fmu_filename + "-" + str(uuid4())
    results = {
        "resultId": result_id,
        "fmuFilename": fmu_filename,
        "modelName": model_description.modelName,
        "fmiVersion": model_description.fmiVersion,
        "description": getattr(model_description, "description", ""),
        "generationTool": getattr(model_description, "generationTool", ""),
        "generationDateAndTime": getattr(model_description, "generationDateAndTime", ""),
        "parameters": parameters,
        "inputs": inputs,
        "outputs": outputs,
        "defaultExperiment": experiment_info,
        "notes": [],
    }
    path = get_result_path(result_id)
    with open(path, "w") as f:
        json.dump(results, f)
    return results