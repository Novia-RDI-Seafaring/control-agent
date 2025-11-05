from plotly.graph_objs.pie import title
from pydantic import BaseModel, Field, model_validator
from control_toolbox.schema import ResponseModel, DataModel, Signal, Source, AttributesGroup
from typing import List, Tuple, Optional, Dict
import numpy as np
from datetime import datetime, timezone
from scipy.signal import find_peaks as scipy_find_peaks

########################################################
# SCHEMAS
########################################################
class TimeRange(BaseModel):
    start: float = Field(..., description="Start time of the time range")
    stop: float = Field(..., description="Stop time of the time range")
    sampling_time: float = Field(..., gt=0, description="Sampling time of the time range")

    @model_validator(mode="after")
    def _check_bounds(self):
        if self.stop <= self.start:
            raise ValueError("stop must be greater than start")
        return self
    
    @model_validator(mode="after")
    def _check_sampling_time(self):
        if self.sampling_time <= 0:
            raise ValueError("sampling_time must be greater than 0")
        return self

class StepProps(BaseModel):
    signal_name: str = Field(default="input", description="Name of the signal")
    time_range: TimeRange = Field(
        default_factory=lambda: TimeRange(start=0.0, stop=1.0, sampling_time=0.1),
        description="Time range over which the step signal is generated",
    )
    step_time: float = Field(default=0.1, description="Time at which the step occurs")
    initial_value: float = Field(default=0.0, description="Initial value of the step signal")
    final_value: float = Field(default=1.0, description="Final value of the step signal")

    @model_validator(mode="after")
    def _check_step_time(self):
        tr = self.time_range
        if not (tr.start <= self.step_time <= tr.stop):
            raise ValueError("step_time must be within [start, stop]")
        return self

class ImpulseProps(BaseModel):
    """
    Properties for generating a discrete-time impulse (Dirac delta) signal.
    """
    signal_name: str = Field(
        default="input",
        description="Name of the signal carrying the impulse."
    )
    time_range: TimeRange = Field(
        default_factory=lambda: TimeRange(start=0.0, stop=1.0, sampling_time=0.1),
        description="Time range over which the impulse signal is defined."
    )
    impulse_time: float = Field(
        default=0.1,
        description="Time at which the unit impulse occurs (must fall within the time range)."
    )
    magnitude: float = Field(
        default=1.0,
        description="Amplitude of the impulse (default 1.0 for unit impulse)."
    )

    @model_validator(mode="after")
    def _check_impulse_time(self):
        tr = self.time_range
        if not (tr.start <= self.impulse_time <= tr.stop):
            raise ValueError("impulse_time must be within [start, stop]")
        return self

########################################################
# HELPER FUNCTIONS
########################################################


########################################################
# TOOLS
########################################################

def generate_step(step: StepProps) -> ResponseModel:
    """
    Generates a step signal.
    
    Args:
        step: StepProps containing the step signal properties
        
    Returns:
        DataModel: Step signal

    Usage: 
    - Make sure thaht the step signal is generated with the correct signal name when passed to other tools as input.
    - Make sure the lists of timestamps and values are the same length
    - Make sure the timestamps are in ascending order
    - Keep the timestamp and value lists as short as possible. It is enough to define the singal only at timestamps where change happens.

    Example: Generate a step at t=1 seconds on the time interval [0, 10.0] seconds.
    ```json
    {
        "signal_name": "input",
        "time_range": {
            "start": 0.0,
            "stop": 10.0,
            "sampling_time": 0.1
        },
        "step_time": 1.0,
        "initial_value": 0.0,
        "final_value": 1.0
    }
    ```

    """
    start = step.time_range.start
    stop = step.time_range.stop
    dt = step.time_range.sampling_time

    # number of samples in interval
    dt = step.time_range.sampling_time
    timestamps = np.array([start, step.step_time - dt, step.step_time, step.step_time + dt, stop])
    values = np.array([step.initial_value, step.initial_value, step.final_value, step.final_value, step.final_value])

    data = DataModel(
        timestamps=timestamps,
        signals=[Signal(name=step.signal_name, values=values.tolist())]
        )
    return ResponseModel(
        source=Source(tool_name="generate_step_tool"),
        data=data
    )

def generate_impulse(impulse: ImpulseProps) -> ResponseModel:
    """
    Generates a unit impulse signal.
    
    Args:
        impulse: ImpulseProps containing the impulse signal properties
        
    Returns:
        DataModel: Impulse signal

    Example: Generate a unit impulse at t=1 seconds on the time interval [0, 10.0] seconds.
    """
    start = impulse.time_range.start
    stop = impulse.time_range.stop
    dt = impulse.time_range.sampling_time

    # number of samples in interval
    dt = impulse.time_range.sampling_time
    timestamps = np.arange(start, stop + dt, dt)
    values = np.zeros_like(timestamps)
    # index of impulse
    idx = np.argmin(np.abs(timestamps - impulse.impulse_time))
    values[idx] = impulse.magnitude

    data = DataModel(
        timestamps=timestamps,
        signals=[Signal(name=impulse.signal_name, values=values.tolist())]
        )
    return ResponseModel(
        source=Source(tool_name="generate_step_tool"),
        data=data
    )

