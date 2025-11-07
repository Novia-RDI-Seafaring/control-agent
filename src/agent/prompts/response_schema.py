from pydantic import BaseModel
from typing import List
import json

def get_json_schema(model):
    return json.dumps(model.model_json_schema(), indent=2)

class ListModelNamesResponse(BaseModel):
    model_names: List[str]

class ListIOPResponse(BaseModel):
    inputs: List[str]
    outputs: List[str]
    parameters: List[str]

class GetMetadataResponse(BaseModel):
    fmi_version: str
    author: str
    version: str
    license: str
    generation_tool: str
    generation_date_and_time: str

class Signal(BaseModel):
    name: str
    values: List[float]

class StepResponse(BaseModel):
    timestamps: List[float]
    inputs: List[Signal]
    outputs: List[Signal]

class SystemParameters(BaseModel):
    K: float
    T: float
    L: float

class PIDParameters(BaseModel):
    Kp: float
    Ti: float
    Td: float

class SystemIdentificationResponse(BaseModel):
    method: str
    parameters: SystemParameters

class LambdaTuningResponse(BaseModel):
    system_parameters: SystemParameters
    lambda_parameter: float
    controller_parameters: PIDParameters

class UltimateGainResponse(BaseModel):
    Ku: float
    Pu: float

class ZNResponse(BaseModel):
    Ku: float
    Pu: float
    controller_parameters: PIDParameters

class TuningOvershootResponse(BaseModel):
    controller_parameters: PIDParameters
    overshoot: float
    rise_time: float