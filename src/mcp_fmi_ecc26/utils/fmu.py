import os
import json
from fmpy import read_model_description
from fmpy import simulate_fmu
from pydantic import BaseModel
from typing import Tuple, List, Dict, Any
from uuid import uuid4

_folder = "models/fmus"

def get_folder():
    return _folder

def set_folder(folder: str):
    global _folder
    _folder = folder

def list_fmus():
    return list(filter(lambda x: x.endswith(".fmu"), os.listdir(get_folder())))

def get_fmu_path(fmu_id: str):
    return os.path.join(get_folder(), fmu_id)

def get_fmu_description(fmu_id: str):
    return read_model_description(get_fmu_path(fmu_id))


def get_fmu_simulation_result(fmu_id: str):
    return simulate_fmu(get_fmu_path(fmu_id))

def create_result_path(result_id: str):
    return os.path.join("data", "simulations", result_id, ".json")


def load_result(result_id: str):
    with open(get_result_path(result_id), "r") as f:
        return json.load(f)
    
class Parameters(BaseModel):
    time: float
    signals: dict

class FMUTool:

    results: List[Tuple[Parameters, str]]
    current_parameters: Parameters

    def __init__(self, fmu_id: str):        
        self.fmu_id = fmu_id
        self.fmu_path = get_fmu_path(fmu_id)
        self.fmu_description = get_fmu_description(fmu_id)
        self.fmu_simulation_result = get_fmu_simulation_result(fmu_id)
        self.results = []
    
    def update_parameters(self, changes: Dict[str, Any]):
        self.current_parameters = Parameters(**{**self.current_parameters.model_dump(), **changes})

    def describe(self):
        return self.fmu_description.to_json()

    def simulate(self):
        result = self.fmu_simulation_result.result()
        id = str(uuid4())
        path = create_result_path(id)
        with open(path, "w") as f:
            json.dump(result, f)