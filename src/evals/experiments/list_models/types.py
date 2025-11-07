from pydantic import BaseModel
from typing import List

class ListModels_Metadata(BaseModel):
    focus: str
    description: str


class ListModels_OutputData(BaseModel):
    model_names: List[str]

ExperimentInputType = str
ExperimentOutputType = ListModels_OutputData
ExperimentMetadataType = ListModels_Metadata