from pathlib import Path
from typing import Dict, List, Optional
from fmpy import read_model_description
from pydantic import BaseModel
from control_toolbox.schema import ResponseModel, Source
from control_toolbox.config import get_fmu_dir

########################################################
# SCHEMAS
########################################################

class FMUVariables(BaseModel):
    inputs: Dict[str, str]
    outputs: Dict[str, str]
    parameters: Dict[str, str]

class FMUMetadata(BaseModel):
    fmi_version: str
    author: str
    version: str
    license: str
    generation_tool: str
    generation_date_and_time: str

class FMUSimulationOptions(BaseModel):
    start_time: float
    stop_time: float
    tolerance: float

class FMUInfo(BaseModel):
    name: str
    relative_path: str
    description: str
    variables: FMUVariables
    metadata: FMUMetadata
    simulation: FMUSimulationOptions

class FMUCollection(BaseModel):
    """Returns a collection of all available FMU models and their information."""
    fmus: Dict[str, FMUInfo]


########################################################
# HELPERS FUNCTIONS
########################################################


def _get_fmu_paths(fmu_dir: List[str]) -> List[str]:
    paths = [f.as_posix() for f in fmu_dir.glob("*.fmu") if f.is_file()]
    return paths

def _get_default_simulation_options(md):
    default_exp = md.defaultExperiment
    return FMUSimulationOptions(
        start_time=default_exp.startTime if default_exp.startTime is not None else 0.0,
        stop_time=default_exp.stopTime if default_exp.stopTime is not None else 0.0,
        tolerance=default_exp.tolerance if default_exp.tolerance is not None else 1E-4
    )

def _get_fmu_information(fmu_path: str) -> FMUInfo:
    """
    Reads the FMU at fmu_path and returns an FMUInfo object
    containing variables, metadata, and simulation settings.
    """
    path = Path(fmu_path)
    md = read_model_description(str(path))

    # Gather variables by causality
    inputs = {v.name: v.type for v in md.modelVariables if v.causality == 'input'}
    outputs = {v.name: v.type for v in md.modelVariables if v.causality == 'output'}
    parameters = {v.name: v.type for v in md.modelVariables if v.causality == 'parameter'}

    variables = FMUVariables(
        inputs=inputs,
        outputs=outputs,
        parameters=parameters
    )

    # Metadata with safe fallbacks
    metadata = FMUMetadata(
        fmi_version=md.fmiVersion or '',
        author=md.author or '',
        version=md.version or '',
        license=md.license or '',
        generation_tool=md.generationTool or '',
        generation_date_and_time=md.generationDateAndTime or ''
    )

    # Simulation defaults with safe fallback for None
    simulation_description = _get_default_simulation_options(md)
    base_description = md.description or '' # get base description from FMU model

    return FMUInfo(
        name=md.modelName or '',
        relative_path=str(path),
        description=base_description,
        variables=variables,
        metadata=metadata,
        simulation=simulation_description
    )

########################################################
# TOOLS
########################################################
def get_fmu_names(fmu_dir: Optional[Path] = None) -> List[str]:
    """Lists all FMU models in the directory.
    Returns:
    List[str]: List of model names (without .fmu extension)
    """
    if fmu_dir is None:
        fmu_dir = get_fmu_dir()
    names = [f.stem for f in fmu_dir.glob("*.fmu") if f.is_file()]
    return ResponseModel(
        source=Source(
            tool_name="get_fmu_names",
            arguments={"fmu_dir": fmu_dir}
        ),
        payload=names
    )

def get_model_description(fmu_name: str, FMU_DIR: Optional[Path] = None) -> ResponseModel:
    """Gets the model description of an FMU model.
    Returns:
    FMUInfo: Full FMU information object
    """
    if FMU_DIR is None:
        FMU_DIR = get_fmu_dir()
    dir = str(FMU_DIR / f"{fmu_name}.fmu")
    information = _get_fmu_information(dir)
    return ResponseModel(
        source=Source(
            tool_name="get_model_description",
            arguments={"fmu_name": fmu_name}
        ),
        payload=information
    )

def get_all_model_descriptions(FMU_DIR: Optional[Path] = None) -> ResponseModel:
    """Lists all FMU models with full metadata, variables, and simulation defaults."""
    if FMU_DIR is None:
        FMU_DIR = get_fmu_dir()
    fmu_names = get_fmu_names(FMU_DIR)
    descriptions = []
    for name in fmu_names.payload:
        dir = str(FMU_DIR / f"{name}.fmu")
        information = _get_fmu_information(dir)
        descriptions.append(information)
    return ResponseModel(
        source=Source(
            tool_name="get_all_model_descriptions",
            arguments={"FMU_DIR": FMU_DIR}
        ),
        payload=descriptions
    )