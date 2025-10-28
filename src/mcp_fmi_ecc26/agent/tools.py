from pydantic_ai import Tool
from uuid import uuid4
from pydantic import BaseModel

class SimlationToolResponse(BaseModel):
    fmu_id: str
    result_id: str

def simulate_fmu(fmu_id: str) -> SimlationToolResponse:
    """Simulate an FMU and it returns a result id you can examine later..."""
    id = str(uuid4())
    return SimlationToolResponse(fmu_id=fmu_id, result_id=id)

