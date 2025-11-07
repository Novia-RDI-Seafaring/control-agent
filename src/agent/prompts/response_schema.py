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
    
    