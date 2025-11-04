from pydantic import BaseModel, Field, model_validator
from typing import Any, Optional, Dict, Union, List
from datetime import datetime

########################################################
# DATA SCHEMA
########################################################
class Signal(BaseModel):
    name: str = Field(..., description="Name of the signal")
    values: List[float] = Field(..., description="List of values corresponding to the timestamps")
    unit: Optional[str] = Field(default=None, description="Unit of the signal")

class DataModel(BaseModel):
    timestamps: List[float] = Field(
        default_factory=list,
        description="List of timestamps"
    )
    signals: List[Signal] = Field(
        default_factory=list,
        description="List of signals, defined using the Signal schema"
    )

    @model_validator(mode="after")
    def check_length(self):
        """Ensure each signal has same number of values as timestamps."""
        tlen = len(self.timestamps)
        for s in self.signals:
            if len(s.values) != tlen:
                raise ValueError(
                    f"Length of timestamps and values in signal '{s.name}' "
                    f"does not match: timestamps={tlen}, values={len(s.values)}"
                )
        return self

class Attribute(BaseModel):
    name: str = Field(..., description="Name of the attribute")
    value: Union[float, int, str] = Field(..., description="Value of the attribute")
    unit: Optional[str] = Field(default=None, description="Unit of the attribute")
    description: Optional[str] = Field(default=None, description="Description of the attribute")

class AttributeGroup(BaseModel):
    name: str = Field(..., description="Name of the attribute group")
    attributes: List[Attribute] = Field(default_factory=list, description="List of attributes")

########################################################
# FIGURE SCHEMA
########################################################
class FigureModel(BaseModel):
    spec: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON-friendly figure spec (e.g., Plotly dict)."
    )
    caption: Optional[str] = Field(None, description="Short human-readable caption for the figure.")

########################################################
# RESPONSE SCHEMA
########################################################

class Source(BaseModel):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the creation of the response"
    )
    tool_name: str = Field(
        ...,
        description="Name of the tool that generated the response"
    )
    run_id: Optional[str] = Field(
        default=None,
        description="ID of the run that generated the response"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters/arguments used for this run (if any)."
    )

class ErrorModel(BaseModel):
    message: str = Field(..., description="Error message")
    traceback: Optional[str] = Field(default=None, description="Traceback of the error")
    
class ToolResponse(BaseModel):
    source: Source = Field(..., description="Source of the tool and its arguments that generated the response")
    summary: Optional[str] = Field(default=None, description="Summary of the response")
    data: Optional[List[DataModel]] = Field(default=None, description="Data associated with the response")
    attributes: Optional[List[AttributeGroup]] = Field(default=None, description="Attributes associated with the response")
    figure: Optional[FigureModel] = Field(default=None, description="Figures associated with the response")
    error: Optional[ErrorModel] = Field(default=None, description="Error message if the response is not successful")