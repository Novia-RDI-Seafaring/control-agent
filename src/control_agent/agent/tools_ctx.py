from control_agent.agent.common import *
from control_agent.agent.ctx import *
logger = getLogger(__name__)

from typing import Literal
def control_help(ctx: RunContext[StateDeps[SimContext]], topic:Literal["fopdt_pi_description", "keywords", "lambda_tuning", "zn_pid_tuning", "seaborg"]) -> str:
    """
    Provides help on control tuning methods.
    """
    match topic:
        case "fopdt_pi_description": path = "docs/fopdt_pi_description.md"
        case "lambda_tuning": path = "docs/lam_method.md"
        case "zn_pid_tuning": path = "docs/zn_method.md"
        case "seaborg": path = "docs/seaborg.md"
        case "keywords": path = "docs/keywords.md"
        case _: return f"Unknown topic: {topic}"
    try:
        print(f"Reading documentation file {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Could not read documentation file {path}: {e}"

def look_at_plot(ctx: RunContext[StateDeps[SimContext]],
        plot_type: Literal["step_response", "bode", "nyquist", "root_locus"],
    ) -> StateSnapshotEvent|ToolExecutionError:
    """
    Looks at a plot of the data.
    """
    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    

def get_fmu_names(ctx: RunContext[StateDeps[SimContext]]) -> List[str]:
    """
    Gets the names of the available FMUs.
    """
    folder = ctx.deps.state.fmu_folder
    fmu_names = _get_fmu_names(folder)
    ctx.deps.state.fmu_names = fmu_names.fmu_names
    return fmu_names.fmu_names

def choose_fmu(ctx: RunContext[StateDeps[SimContext]],
        fmu_name: str,
    ) -> StateSnapshotEvent|ToolExecutionError:
    """
    Chooses a FMU from the list of available FMUs.
    """
    if fmu_name not in ctx.deps.state.fmu_names: return ToolExecutionError(message="FMU not found")
    try:
        ctx.deps.state.current_fmu = fmu_name
        if fmu_name not in ctx.deps.state.fmus:
            ctx.deps.state.fmus[fmu_name] = FmuContext(
                fmu_name=fmu_name,
                fmu_path=str(Path(ctx.deps.state.fmu_folder) / f"{fmu_name}.fmu"),
                model_description=None,
                simulations=[],
                lambda_tuning_checks=[],
                zn_pid_tuning_checks=[]
            )
        return StateSnapshotEvent(
        type=EventType.STATE_SNAPSHOT,
        snapshot=ctx.deps.state,
    )

    except Exception as e:
        print(f"Error in choose fmu: {e}")
        return ToolExecutionError(message=str(e))

def get_model_description(ctx: RunContext[StateDeps[SimContext]]) -> ToolExecutionError|StateSnapshotEvent:
    """
    Gets the model info for a FMU.
    """
    try:
        fmu_path = ctx.deps.state.fmu.fmu_path
    except Exception as e:
        return ToolExecutionError(message=str(e))

    try:
        model_info = _get_model_description(fmu_path)
        ctx.deps.state.fmu.model_description = model_info
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=ctx.deps.state,
        )

    except Exception as e:
        print(f"Error in get model description: {e}")
        return ToolExecutionError(message=str(e))


def simulate_step_response(ctx: RunContext[StateDeps[SimContext]],
        sim_props: SimulationStepResponseProps,
        step_props: StepProps,
    ) -> StateSnapshotEvent|ToolExecutionError:
    """
    Simulates a step response with input defined in the StepProps.

    Args:
        ctx: the context of the run
        sim_props: SimulationStepResponseProps containing the simulation parameters.
        step_props: StepProps containing the step signal properties.
        
    Returns:
        SimulationResponse containtin the data and an id  (repr_id) that to be used with other tools
        If you pass the repr_id to other tools, they will get access to the full datamodel from the run.
        that is the DataModel: step response of the FMU model.
        the return value contains Teaser, of that specifying what signals there are etc.
    **Purpose:**  
    Simulate a step response of a Functional Mock-up Unit (FMU) model using the specified parameters and input signals.

    **Important:**
    - Ensure that the output `output_interval` and the signal `sampling_time` are integer multiples of the FMU model step size (default 0.1).
    - Ensure that you have set all parameters correctly in the `start_values` dictionary before simulating.

    """
    try:
        fmu_path = ctx.deps.state.fmu.fmu_path
    except Exception as e:
        return ToolExecutionError(message=str(e))
    try:
        print(f"simulate step response with props: {sim_props} and step props: {step_props}")

        data = _simulate_step_response(fmu_path, sim_props, step_props)
        ctx.deps.state.fmu.simulations.append(SimulationRun(
            sim_props=sim_props,
            step_props=step_props,
            data=data,
            fopdt_checks=[],
            attributes=[]
        ))
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=ctx.deps.state,
        )

    except Exception as e:
        print(f"Error in simulate step response: {e}")
        return ToolExecutionError(message=str(e))


def identify_fopdt_from_step(ctx: RunContext[StateDeps[SimContext]],
        props: IdentificationProps,
    ) -> StateSnapshotEvent|ToolExecutionError:
    """
    Identify a First Order Plus Dead Time (FOPDT) model from step response data without input signal.

    Args:
        repr_id: the id representing data from a simulation run, that is used to get the full DataModel containing the step response data (the full data is not used as to not clutter the context window with lots of numbers)
        props: IdentificationProps containing the identification parameters
            - output_name: Name of the output signal
            - input_step_size: The size of the input step that was applied in the experiment.
            - input_step_time: The time at which the input step was applied.
            - method: Method to identify the model.
            - step_threshold: Threshold for step detection. Changes in input signal smaller than this value will be ignored. If None, uses 1% of the input signal range as default.
    Returns:


    **Usage:**
        This tool analyzes a previously simulated or measured step response and fits a FOPDT model to it.
    """

    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    try:
        data = ctx.deps.state.fmu.simulations[-1].data
        fopdt_check = FOPDTCheck(
            props=props,
            data=_identify_fopdt_from_step(data, props)
        )
        ctx.deps.state.fmu.simulations[-1].fopdt_checks.append(fopdt_check)
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=ctx.deps.state,
        )

    except Exception as e:
        print(f"Error in identify fopdt from step: {e}")
        return ToolExecutionError(message=str(e))

def find_inflection_point(ctx: RunContext[StateDeps[SimContext]],
        props: InflectionPointProps,
    ) -> StateSnapshotEvent|ToolExecutionError:
    """
    Finds the inflection point of a signal.

    Args:
        repr_id: the id representing data from a simulation run, that is used to get the full DataModel containing the step response data (the full data is not used as to not clutter the context window with lots of numbers)
        props: InflectionPointProps containing the inflection point properties
            - signal_name: Name of the signal to find the inflection point of.
    Returns:
        AttributesGroup containing the inflection point.
        the AttributesGroup contains the timestamp, value and slope of the inflection point.
        the AttributesGroup also contains a description of the inflection point.
    """

    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    try:
        data = ctx.deps.state.fmu.simulations[-1].data
        inflection_check = InflectionCheck(
            signal_name=props.signal_name,
            data=_find_inflection_point(data, props)
        )
        ctx.deps.state.fmu.simulations[-1].attributes.append(inflection_check.data)
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=ctx.deps.state,
        )
    except Exception as e:
        print(f"Error in find inflection point: {e}")
        return ToolExecutionError(message=str(e))
    
def find_rise_time(ctx: RunContext[StateDeps[SimContext]]) -> StateSnapshotEvent|ToolExecutionError:
    """
    Finds the rise time of a signal.
    Args:
        repr_id: the id representing data from a simulation run, that is used to get the full DataModel containing the step response data (the full data is not used as to not clutter the context window with lots of numbers)
    Returns:
        AttributesGroup containing the rise time.
        the AttributesGroup contains the timestamp, value and rise time of the signal.
        the AttributesGroup also contains a description of the rise time.
    """
    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    try:
            
        data = ctx.deps.state.fmu.simulations[-1].data
        rise_time_check = RiseTimeCheck(
            data=_find_rise_time(data)
        )
        ctx.deps.state.fmu.simulations[-1].attributes.append(rise_time_check.data)
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=ctx.deps.state,
        )

    except Exception as e:
        print(f"Error in find rise time: {e}")
        return ToolExecutionError(message=str(e))

def find_characteristic_points(ctx: RunContext[StateDeps[SimContext]]) -> StateSnapshotEvent|ToolExecutionError:
    """
    Finds the characteristic points of step responses.
    
    Args:
        repr_id: the id representing data from a simulation run, that is used to get the full DataModel containing the step response data (the full data is not used as to not clutter the context window with lots of numbers)
        
    Returns:
        ResponseModel: Contains **critical points* analyzing step rsponses and finetuning controllers.
            - p0 = (t0,y0) point when output starts to change from initial value.
            - p10 = (t10,y10) point when output first reachest 10% of total change.
            - p63 = (t63,y63) point when output first reachest 63% of total change. Can be used to determine the time constant T of a FOPDT system.
            - p90 = (t90,y90) point when output first reachest 90% of total change.
            - p98 = (t98,y98) point when output first reachest 98% of total change.
    """
    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    try:
        data = ctx.deps.state.fmu.simulations[-1].data
        characteristic_points_check = CharacteristicPointsCheck(
            data=_find_characteristic_points(data)
        )
        ctx.deps.state.fmu.simulations[-1].attributes.append(characteristic_points_check.data)
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=ctx.deps.state,
        )
    
    except Exception as e:
        print(f"Error in find characteristic points: {e}")
        return ToolExecutionError(message=str(e))

def lambda_tuning(ctx: RunContext[StateDeps[SimContext]],
        model: FOPDTModel,
        props: LambdaTuningProps,
    ) -> StateSnapshotEvent|ToolExecutionError:
    """
    Compute PID controller parameters using the Lambda tuning method.
    """
    messages:List[str] = []
    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            messages.append("No simulations have been run yet, this might be unreliable.")
        if len(ctx.deps.state.fmu.simulations[-1].fopdt_checks) == 0:
            messages.append("No FOPDT checks have been run yet, this might be unreliable.")

    except Exception as e:
        print(f"Error in lambda tuning A: {e}")
        return ToolExecutionError(message=str(e))
    try:
        messages = []
        params = _lambda_tuning(model, props)
        ctx.deps.state.fmu.lambda_tuning_checks.append(LambdaTuningCheck(
            model=model,
            props=props,
            params=params,
            messages=messages
        ))
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=ctx.deps.state,
        )
    except Exception as e:
        print(f"Error in lambda tuning: {e}")
        return ToolExecutionError(message=str(e))


    
def find_peaks(ctx: RunContext[StateDeps[SimContext]],
        props: FindPeaksProps,
    ) -> StateSnapshotEvent|ToolExecutionError:
    """
    Find peaks inside a signal based on peak properties.

    This function takes DataModel and finds all local maxima by simple comparison of neighboring values.
    Optionally, a subset of these peaks can be selected by specifying conditions for a peak's properties.
    
    Args:
        repr_id: the id representing data from a simulation run, that is used to get the full DataModel containing the step response data (the full data is not used as to not clutter the context window with lots of numbers)
    """
    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    print("\nFinding peaks")
    for key, value in props.model_dump().items():
        print(f"\tAttribute: {key}: {value}")
    data = ctx.deps.state.fmu.simulations[-1].data
    result = _find_peaks(data, props)
    ctx.deps.state.fmu.simulations[-1].attributes.append(result)
    return StateSnapshotEvent(
        type=EventType.STATE_SNAPSHOT,
        snapshot=ctx.deps.state,
    )

def find_settling_time(ctx: RunContext[StateDeps[SimContext]],
        repr_id: str,
        props: SettlingTimeProps,
    ) -> StateSnapshotEvent|ToolExecutionError:
    """
    Finds the settling time of each signal in the data. The settling time is defined as the
    first time point where the signal remains within a specified tolerance (percentage) of
    its final value (i.e., steady-state level) for the remainder of the signal.

    Args:
        repr_id: the id representing data from a simulation run, that is used to get the full DataModel containing the step response data (the full data is not used as to not clutter the context window with lots of numbers)
        props: SettlingTimeProps containing the settling time properties
            - tolerance: Tolerance (percentage) of the final value.
    Returns:
        AttributesGroup containing the settling time.
    """

    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    
    data = ctx.deps.state.fmu.simulations[-1].data
    result = _find_settling_time(data, props)
    ctx.deps.state.fmu.simulations[-1].settling_time_checks.append(SettlingTimeCheck(
        props=props,
        data=result
    ))
    return StateSnapshotEvent(
        type=EventType.STATE_SNAPSHOT,
        snapshot=ctx.deps.state,
    )

def zn_pid_tuning(ctx: RunContext[StateDeps[SimContext]],
        props: UltimateTuningProps,
    ) -> StateSnapshotEvent|ToolExecutionError:
    """
    Compute PID controller parameters using the Ziegler-Nichols closed-loop
    (also called ultimate gain or continuous-cycling) tuning method.
    
    You need to do simulations first, in order to determing Ku and Pu
    from closed loop experiments with a PI controller first
    This tool assume you have the right values.
    
    
    Args:
        props: UltimateTuningProps containing the ultimate tuning properties
            - controller: Type of controller to tune.
            - method: Method to tune the controller.
    Returns:
        PIDParameters containing the PID controller parameters.
    """
    print(f"zn pid tuning with props: {props}")
    messages:List[str] = []
    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            messages.append("No simulations have been run yet, this might be unreliable.")
        if len(ctx.deps.state.fmu.simulations[-1].fopdt_checks) == 0:
            messages.append("No FOPDT checks have been run yet, this might be unreliable.")

    except Exception as e:
        return ToolExecutionError(message=str(e))

    params = _zn_pid_tuning(props)
    ctx.deps.state.fmu.zn_pid_tuning_checks.append(ZNPIDTuningCheck(
        props=props,
        params=params,
        messages=messages
    ))
    return StateSnapshotEvent(
        type=EventType.STATE_SNAPSHOT,
        snapshot=ctx.deps.state,
    )

 
## add rise time,  and lam

# Build the tool list with stored I/O
def get_tools() -> list[Tool[Any]]:
    return [
        Tool(control_help,
            name="control_help",
            description=control_help.__doc__,
            takes_ctx=True),
        # information tools
        Tool(get_fmu_names,
            name="get_fmu_names",
            description=get_fmu_names.__doc__,
            takes_ctx=True),
        Tool(choose_fmu,    
            name="choose_fmu",
            description=choose_fmu.__doc__,
            takes_ctx=True),
        Tool(get_model_description,
            name="get_model_description",
            description=get_model_description.__doc__,
            takes_ctx=True),

        Tool(simulate_step_response,
            name="simulate_step_response",
            description=simulate_step_response.__doc__,
            takes_ctx=True),

        Tool(identify_fopdt_from_step,
            name="identify_fopdt_from_step",
            description=identify_fopdt_from_step.__doc__,
            takes_ctx=True),

        Tool(find_inflection_point,
            name="find_inflection_point",
            description=find_inflection_point.__doc__,
            takes_ctx=True),

        Tool(find_characteristic_points,
            name="find_characteristic_points",
            description=find_characteristic_points.__doc__,
            takes_ctx=True),

        Tool(find_peaks,
            name="find_peaks",
            description=find_peaks.__doc__,
            takes_ctx=True),

        Tool(find_rise_time,
            name="find_rise_time",
            description=find_rise_time.__doc__,
            takes_ctx=True),

        Tool(find_settling_time,
            name="find_settling_time",
            description=find_settling_time.__doc__,
            takes_ctx=True),

        Tool(zn_pid_tuning,
            name="zn_pid_tuning",
            description=zn_pid_tuning.__doc__,
            takes_ctx=True),

        Tool(lambda_tuning,
            name="lambda_tuning",
            description=lambda_tuning.__doc__,
            takes_ctx=True),
        ]

