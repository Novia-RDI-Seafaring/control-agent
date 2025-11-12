from control_agent.agent.common import *

DepsType = StateDeps['FmuContext']


class SimulationResponse(BaseModel):
    repr_id: str
    data: DataModel


class FOPDTCheck(BaseModel):
    props: IdentificationProps
    data: FOPDTModel

class InflectionCheck(BaseModel):
    signal_name: str
    data: AttributesGroup

class RiseTimeCheck(BaseModel):
    data: AttributesGroup

class PIDCheck(BaseModel):
    data: PIDParameters

class LambdaTuningCheck(BaseModel):
    model: FOPDTModel
    props: LambdaTuningProps
    params: PIDParameters
    messages: List[str]

class ZNPIDTuningCheck(BaseModel):
    props: UltimateTuningProps
    params: PIDParameters
    messages: List[str]

class SettlingTimeCheck(BaseModel):
    props: SettlingTimeProps
    data: AttributesGroup

class SimulationRun(BaseModel):
    sim_props: SimulationStepResponseProps
    step_props: StepProps
    data: DataModel
    fopdt_checks: List[FOPDTCheck] = Field(default_factory=list)
    pid_checks: List[PIDCheck] = Field(default_factory=list)
    attributes: List[AttributesGroup] = Field(default_factory=list)
    settling_time_checks: List[SettlingTimeCheck] = Field(default_factory=list)

class CharacteristicPointsCheck(BaseModel):
    data: AttributesGroup

class Analysis(BaseModel):
    props: IdentificationProps
    data: AttributesGroup


class FmuContext(BaseModel):
    fmu_name: str = "PI_FOPDT_2"
    fmu_path: str = "models/fmus/PI_FOPDT_2.fmu"
    model_description: Optional[ModelDescription] = Field(default=None)
    simulations: List[SimulationRun] = Field(default_factory=list)
    lambda_tuning_checks: List[LambdaTuningCheck] = Field(default_factory=list)
    zn_pid_tuning_checks: List[ZNPIDTuningCheck] = Field(default_factory=list)

        

class SimContext(BaseModel):
    query: str = Field(default="")
    fmu_folder: str = Field(default="models/fmus")
    current_fmu: Optional[str] = Field(default=None)
    fmu_names: List[str] = Field(default_factory=list)
    fmus: Dict[str, FmuContext] = Field(default_factory=dict)
    notes: List[str]

    @property
    def fmu(self) -> FmuContext:
        if self.current_fmu is None: raise ValueError("No FMU chosen")
        if self.current_fmu not in self.fmus: raise ValueError(f"FMU {self.current_fmu} not found")
        return self.fmus[self.current_fmu]
    
class ToolExecutionError(BaseModel):
    message: str
