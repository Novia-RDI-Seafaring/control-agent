from control_agent.agent.common import *
from control_agent.agent.ctx import *
logger = getLogger(__name__)
from control_agent.agent.docstrings import make_docstring
console = Console()

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
        console.print(f"Reading documentation file {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Could not read documentation file {path}: {e}"

def look_at_plot(ctx: RunContext[StateDeps[SimContext]],
        signal_name: str,
    ) -> BinaryContent|ToolExecutionError:
    """
    If you need to check a signal as an image, you can use this tool to get the raw image data of the signal you are interested in.
    """
    import matplotlib
    matplotlib.use('Agg') # type: ignore
    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            console.print(f"No simulations have been run yet")
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    try:
        console.print(f"will try to look at plot of signal: {signal_name}")
        data = ctx.deps.state.fmu.simulations[-1].data
        figures = plot_data(data)
        try:
            figure:Figure = figures[signal_name]
        except Exception as e:
            return ToolExecutionError(message=f"Signal {signal_name} not found in data")
        try:
            # Use an in-memory bytes buffer to capture PNG image data
            import io
            buf = io.BytesIO()
            figure.savefig(buf, format='png', bbox_inches='tight', dpi=300)
            buf.seek(0)
            png_image: bytes = buf.read()
            buf.close()
            console.print(f"Looking at image of signal: {signal_name}")
            return BinaryContent(data=png_image, media_type='image/png')
        except Exception as e:
            return ToolExecutionError(message=str(e))
    except Exception as e:
        return ToolExecutionError(message=str(e))


def get_fmu_names(ctx: RunContext[StateDeps[SimContext]]) -> List[str]:
    folder = ctx.deps.state.fmu_folder
    fmu_names = _get_fmu_names(folder)
    ctx.deps.state.fmu_names = fmu_names.fmu_names
    return fmu_names.fmu_names

def choose_fmu(ctx: RunContext[StateDeps[SimContext]],
        fmu_name: str,
    ) -> StateSnapshotEvent|ToolExecutionError:
    if fmu_name not in ctx.deps.state.fmu_names: return ToolExecutionError(message="FMU not found")
    try:
        ctx.deps.state.current_fmu = fmu_name
        if fmu_name not in ctx.deps.state.fmus:
            fmu_path = str(Path(ctx.deps.state.fmu_folder) / f"{fmu_name}.fmu")
            ctx.deps.state.fmus[fmu_name] = FmuContext(
                fmu_name=fmu_name,
                fmu_path=fmu_path,
                model_description=_get_model_description(fmu_path),
                simulations=[],
                lambda_tuning_checks=[],
                zn_pid_tuning_checks=[]
            )
        return StateSnapshotEvent(
        type=EventType.STATE_SNAPSHOT,
        snapshot=ctx.deps.state,
    )

    except Exception as e:
        console.print(f"Error in choose fmu: {e}")
        return ToolExecutionError(message=str(e))

def get_model_description(ctx: RunContext[StateDeps[SimContext]]) -> ToolExecutionError|StateSnapshotEvent:
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
        console.print(f"Error in get model description: {e}")
        return ToolExecutionError(message=str(e))


def simulate_step_response(ctx: RunContext[StateDeps[SimContext]],
        sim_props: SimulationStepResponseProps,
        step_props: StepProps,
    ) -> StateSnapshotEvent|ToolExecutionError:
    try:
        fmu_path = ctx.deps.state.fmu.fmu_path
    except Exception as e:
        return ToolExecutionError(message=str(e))
    try:
        console.print(f"simulate step response:")
        console.print(sim_props)
        console.print(step_props)
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

def find_overshoot(ctx: RunContext[StateDeps[SimContext]]) -> StateSnapshotEvent|ToolExecutionError:

    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    try:
            
        data = ctx.deps.state.fmu.simulations[-1].data
        overshoot_check = OvershootCheck(
            data=_find_overshoot(data)
        )
        ctx.deps.state.fmu.simulations[-1].attributes.append(overshoot_check.data)
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=ctx.deps.state,
        )

    except Exception as e:
        print(f"Error in find overshoot: {e}")
        return ToolExecutionError(message=str(e))

def find_characteristic_points(ctx: RunContext[StateDeps[SimContext]]) -> StateSnapshotEvent|ToolExecutionError:
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

    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    console.print("\nFinding peaks")
    console.print(props)
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


    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    
    data = ctx.deps.state.fmu.simulations[-1].data
    debug(props)

    result = _find_settling_time(data, props)
    debug(result)
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

    console.print(f"zn pid tuning with props")
    messages:List[str] = []
    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            messages.append("No simulations have been run yet, this might be unreliable.")
        if len(ctx.deps.state.fmu.simulations[-1].fopdt_checks) == 0:
            messages.append("No FOPDT checks have been run yet, this might be unreliable.")

    except Exception as e:
        return ToolExecutionError(message=str(e))

    debug(props)
    params = _zn_pid_tuning(props)
    debug(params)
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
from control_agent.agent.docstrings import make_docstring
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
            description=make_docstring(_get_fmu_names, get_fmu_names),
            takes_ctx=True),

        Tool(look_at_plot,
            name="look_at_signal_plot",
            description=look_at_plot.__doc__,
            takes_ctx=True),

        Tool(choose_fmu,    
            name="choose_fmu",
            description=choose_fmu.__doc__,
            takes_ctx=True),
        Tool(get_model_description,
            name="get_model_description",
            description=make_docstring(_get_model_description, get_model_description),
            takes_ctx=True),

        Tool(simulate_step_response,
            name="simulate_step_response",
            description=make_docstring(_simulate_step_response, simulate_step_response),
            takes_ctx=True),

        Tool(identify_fopdt_from_step,
            name="identify_fopdt_from_step",
            description=make_docstring(_identify_fopdt_from_step, identify_fopdt_from_step),#identify_fopdt_from_step.__doc__,
            takes_ctx=True),

        Tool(find_inflection_point,
            name="find_inflection_point",
            description=make_docstring(_find_inflection_point, find_inflection_point),
            takes_ctx=True),

        Tool(find_characteristic_points,
            name="find_characteristic_points",
            description=make_docstring(_find_characteristic_points, find_characteristic_points),
            takes_ctx=True),

        Tool(find_peaks,
            name="find_peaks",
            description=make_docstring(_find_peaks, find_peaks),
            takes_ctx=True),

        Tool(find_rise_time,
            name="find_rise_time",
            description=make_docstring(_find_rise_time, find_rise_time),
            takes_ctx=True),

        Tool(find_overshoot,
            name="find_overshoot",
            description=make_docstring(_find_overshoot, find_overshoot),
            takes_ctx=True),

        Tool(find_settling_time,
            name="find_settling_time",
            description=make_docstring(_find_settling_time, find_settling_time),
            takes_ctx=True),

        Tool(zn_pid_tuning,
            name="zn_pid_tuning",
            description=make_docstring(_zn_pid_tuning, zn_pid_tuning),
            takes_ctx=True),

        Tool(lambda_tuning,
            name="lambda_tuning",
            description=make_docstring(_lambda_tuning, lambda_tuning),
            takes_ctx=True),
        ]

if __name__ == "__main__":

    tools = get_tools()
    for t in tools:
        print(f"--------------------------------")
        print(t.name)
        print(t.description)
        print("--------------------------------")