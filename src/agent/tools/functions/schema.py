from typing import List, Dict, Optional, Union, Any, Tuple
from pydantic import BaseModel, HttpUrl, Field, model_validator
from pydantic_core.core_schema import DateSchema

class Signal(BaseModel):
    name: str = Field(..., description="Name of the signal")
    values: List[float] = Field(..., description="List of values corresponding to the timestamps")

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

#class DataModel(BaseModel):
#    timestamps: List[float] = Field(default_factory=list)
#    signals:    Dict[str, List[float]] = Field(default_factory=dict)

class FMUPaths(BaseModel):
    fmu_paths: List[str]

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

class PlotHttpURL(BaseModel):
    description: str
    url: HttpUrl

class SimulationModel(BaseModel):
    fmu_name: str = Field(
        description="Name of the FMU model to simulate"
    )
    start_time: Optional[Union[float, str]] = Field(
        default=0.0,
        description="Simulation start time"
    )
    stop_time: Optional[Union[float, str]] = Field(
        default=1.0,
        description="Simulation stop time"
    )
    step_size: Optional[Union[float, str]] = Field(
        default=None,
        description="Simulation step size"
    )
    input: Optional[DataModel] = Field(
        default=None,
        description="DataModel containing input signals"
    )
    output: Optional[List[str]] = Field(
        default=None,
        description="Sequence of output variable names to record"
    )
    output_interval: Union[float, str] = Field(
        default=None,
        description="Interval for sampling the output"
    )
    start_values: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Dictionary of initial parameter and input values. "
            "Use this function to change the values of parameters and "
            "inputs from their default values."
        )
    )

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

class AnalysisProps(BaseModel):
    settling_time_treshhold: float = Field(
        default=0.02,
        description=(
            "Specifies the threshold ST used in defining settling/transient times."
        ),
    )
    rise_time_limits: List[float] = Field(
        default=(0.1, 0.9),
        description=(
            "Specifies lower/upper RT(0) and RT(1) thresholds used for rise time. "
            "Rise time is the time the response takes to rise from RT(0) to RT(1) of the way "
            "from initial value to steady-state. The upper threshold RT(1) is also used for "
            "settling_min and settling_max (minimum and maximum after the RT(1) point)."
        ),
    )

class CharacteristicPoints(BaseModel):
    # (time, value) pairs at key fractions of the total change
    p0: List[float] = Field(
        ...,
        description="(t0, y0): first time when output starts to change from initial value."
    )
    p10: List[float] = Field(
        ...,
        description="(t10, y10): (time, value) pair when output first reachest 10% of total change."
    )
    p63: List[float] = Field(
        ...,
        description="(t63, y63): (time, value) pair when output first reaches 63% (≈1−e⁻¹) of total change."
    )
    p90: List[float] = Field(
        ...,
        description="(t90, y90): (time, value) pair when output first reaches 90% of total change."
    )
    p98: List[float] = Field(
        ...,
        description="(t98, y98): (time, value) pair when output first reaches 98% of total change."
    )
    pRT0: List[float] = Field(
        ...,
        description="(tRT0, yRT0): (time, value) pair when output first reaches RT(0) of total change."
    )
    pRT1: List[float] = Field(
        ...,
        description="(tRT1, yRT1): (time, value) pair when output first reaches RT(1) of total change."
    )
    pST: List[float] = Field(
        ...,
        description="(tST, yST): (time, value) pair when output first reaches ST of total change."
    )
    pPeak: List[float] = Field(
        ...,
        description="(tPeak, yPeak): Peak value and corresponding time point."
    )
    pUndershoot: List[float] = Field(
        ...,
        description="(tUndershoot, yUndershoot): Undershoot value (smallest value after RT1) and corresponding time point."
    )

class StepResponseAnalysis(BaseModel):
    characteristic_points: CharacteristicPoints = Field(
        ...,
        description="Key percentage-response points: (t10,y10), (t63,y63), (t90,y90), (t98,y98)."
    )

    # Core metrics
    rise_time: float = Field(
        ...,
        description="Rise time defined as t90 − t10 (from characteristic_points)."
    )

    settling_time: float = Field(
        ...,
        description="Time it takes until the response is within 2% of the final value."
    )

    settling_min: float = Field(
        ...,
        description="Minimum response value observed while evaluating settling behavior."
    )

    settling_max: float = Field(
        ...,
        description="Maximum response value observed while evaluating settling behavior."
    )

    # Percent metrics (relative to total change)
    overshoot: Optional[float] = Field(
        default=None,
        description="Percent overshoot: (peak - final)/|final - initial| * 100."
    )
    undershoot: Optional[float] = Field(
        default=None,
        description="Percent undershoot: (min - initial)/|final - initial| * 100 (reported as ≥ 0)."
    )