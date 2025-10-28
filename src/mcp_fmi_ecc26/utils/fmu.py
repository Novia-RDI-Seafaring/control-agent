import os
import json
from fmpy import read_model_description
from fmpy import simulate_fmu
from pydantic import BaseModel
from typing import Tuple, List, Dict, Any
from uuid import uuid4
from pathlib import Path

_folder = "models/fmus"
_data_folder = "data"

def get_folder():
    return _folder

def set_folder(folder: str):
    global _folder
    _folder = folder

def get_data_folder():
    return _data_folder


def list_fmus() -> List[str]:
    return list(filter(lambda x: x.endswith(".fmu"), os.listdir(get_folder())))

def get_fmu_path(fmu_id: str):
    return os.path.join(get_folder(), fmu_id)

def get_fmu_description(fmu_id: str):
    return read_model_description(get_fmu_path(fmu_id))

def get_result_path(result_id: str):
    path = Path(get_data_folder(), "data", "simulations", f"{result_id}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.as_posix()


def load_result(result_id: str):
    with open(get_result_path(result_id), "r") as f:
        return json.load(f)
    
def annotate_result(result_id:str, note:str):
    data:Dict[str,Any] = load_result(result_id)
    data.setdefault("notes",[]).append(note)
    with open(get_result_path(result_id), "w") as f:
        json.dump(data, f)    
