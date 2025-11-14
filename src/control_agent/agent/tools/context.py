from control_agent.agent.core.types import *
from control_agent.agent.context.models import *
from control_agent.agent.validation.guardrails import apply_guardrails, SimulationGuardrails
from control_agent.agent.utils.docstrings import make_docstring
logger = getLogger(__name__)

console = Console()

from typing import Literal
from control_agent.evals.schemas.responses import StepResponse, Signal
def control_help(ctx: RunContext[StateDeps[SimContext]], topic:Literal["fopdt_pi_description", "keywords", "lambda_tuning", "zn_pid_tuning", "seaborg"]) -> str:
    """
    Provides detailed documentation on control tuning methods.
    
    **General Guidelines:**
    - Read tool docstrings carefully to understand prerequisites and usage
    - **Documentation**: If you need theoretical background or detailed procedures, use `control_help` tool with topics: `zn_pid_tuning`, `keywords`, `lambda_tuning`
    - Do NOT repeatedly call the same tool if it keeps failing - read error messages and fix the underlying issue
    
    **IMPORTANT**: 
    - For `ultimate_gain` experiment: Tool docstrings have workflow guidance, but if you need clarification on what "sustained oscillations" means or how to interpret peak data, use `control_help` with topic `zn_pid_tuning` or `keywords`
    - For `z_n` experiment: Tool docstrings have prerequisites, but use `control_help` if you need detailed theory
    - Only call if you genuinely need theoretical background or clarification, not for routine execution
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
    Get a plot image of a signal from the most recent simulation.
    
    **PRIMARY USE**: Ziegler-Nichols method - visually inspect oscillations to determine if sustained oscillations are present before calling `find_peaks`.
    
    **IMPORTANT**:
    - Call this tool ONCE per simulation if you need visual confirmation
    - Do NOT call this tool repeatedly for the same simulation - the plot doesn't change
    - For most experiments, you don't need this tool - use `find_peaks` or `find_characteristic_points` instead
    - Only use when you need to visually verify oscillations (Ziegler-Nichols) or debug signal behavior
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


def get_step_response_data(ctx: RunContext[StateDeps[SimContext]]) -> StepResponse|ToolExecutionError:
    """
    Extract the latest simulation data as StepResponse format.
    Use this tool to get the simulation results in the format required for the output.
    Returns timestamps, inputs, and outputs signals from the most recent simulation.
    
    IMPORTANT: This tool MUST be called after simulate_step_response to get the actual simulation data.
    The returned StepResponse contains the full simulation results with all signals.
    """
    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet. Call simulate_step_response first.")
        
        simulation = ctx.deps.state.fmu.simulations[-1]
        data = simulation.data
        
        # Extract timestamps
        timestamps = data.timestamps if hasattr(data, 'timestamps') and data.timestamps else []
        
        # Extract signals - DataModel has 'signals' attribute
        signals = []
        if hasattr(data, 'signals'):
            signals = data.signals if data.signals else []
        elif hasattr(data, 'get_signals'):
            # Try alternative method if available
            signals = data.get_signals() if callable(data.get_signals) else []
        
        # Debug: Log what we found
        if not signals:
            available_attrs = [attr for attr in dir(data) if not attr.startswith('_')]
            console.print(f"[DEBUG] No signals found. Available attributes: {available_attrs}")
            console.print(f"[DEBUG] Data type: {type(data)}")
            if hasattr(data, 'timestamps'):
                console.print(f"[DEBUG] Timestamps length: {len(timestamps)}")
        
        # Separate inputs and outputs
        inputs = []
        outputs = []
        
        for signal in signals:
            # Extract signal name and values
            signal_name = signal.name if hasattr(signal, 'name') else str(signal)
            signal_values = signal.values if hasattr(signal, 'values') and signal.values else []
            
            if not signal_values:
                console.print(f"[WARNING] Signal '{signal_name}' has no values")
                continue
            
            signal_obj = Signal(name=signal_name, values=signal_values)
            
            # Typically 'u' or 'input' is input, 'y' or 'output' is output
            signal_name_lower = signal_name.lower()
            if signal_name_lower in ['u', 'input', 'control']:
                inputs.append(signal_obj)
            elif signal_name_lower in ['y', 'output', 'plant']:
                outputs.append(signal_obj)
            else:
                # Default to output if unclear
                outputs.append(signal_obj)
        
        # Validate we have data
        if not timestamps:
            return ToolExecutionError(message="Simulation data has no timestamps. The simulation may have failed.")
        
        if not outputs and not inputs:
            return ToolExecutionError(
                message=f"Simulation data has no signals. Found {len(signals)} signals in data. "
                f"Available data attributes: {[attr for attr in dir(data) if not attr.startswith('_')]}"
            )
        
        return StepResponse(
            timestamps=timestamps,
            inputs=inputs,
            outputs=outputs
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        console.print(f"Error extracting step response data: {e}")
        console.print(f"Traceback: {error_details}")
        return ToolExecutionError(message=f"Failed to extract step response data: {str(e)}")

def get_fmu_names(ctx: RunContext[StateDeps[SimContext]]) -> List[str]:
    """
    Gets the names of the available FMUs.
    
    **IMPORTANT**: 
    - Call this tool ONCE - the result is stored in context and doesn't change
    - After calling, use the returned list to choose an FMU with `choose_fmu`
    - Do NOT call this tool multiple times - reuse the result from the first call
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
    
    **WHEN TO USE**:
    - Only call this tool if you need to select a specific FMU
    - If the task doesn't specify which FMU to use, you may not need this tool
    - Check if an FMU is already selected in context before calling
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
        console.print(f"Error in choose fmu: {e}")
        return ToolExecutionError(message=str(e))

def get_model_description(ctx: RunContext[StateDeps[SimContext]]) -> ToolExecutionError|StateSnapshotEvent:
    """
    Gets the model description/metadata for the currently chosen FMU.
    
    **PREREQUISITES**:
    - You MUST call `choose_fmu` FIRST to select an FMU
    - Without a chosen FMU, this tool will fail
    
    **IMPORTANT**:
    - Call this tool ONCE after choosing an FMU - the result is stored in context
    - Do NOT call this tool before choosing an FMU
    - Do NOT call this tool multiple times for the same FMU - reuse the stored result
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
        console.print(f"Error in get model description: {e}")
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
    - For P controller (Ziegler-Nichols/Ultimate Gain): Set `Ti=float('inf')` (use Python float('inf'), NOT the string 'inf' or 'float("inf")')
    - If simulation fails with "Failed to instantiate model" or "Server unexpectedly died":
      * Check that all required parameters in start_values are set correctly
      * Verify Ti is float('inf') not string 'inf' for P controller
      * Try a different Kp value if current one causes instability
      * Do NOT retry the same failed simulation repeatedly - adjust parameters instead
    
    **For Ultimate Gain experiments:**
    - Use P controller: `mode=True`, `Ti=float('inf')`, gradually increase `Kp` until sustained oscillations appear
    - When you see sustained oscillations (output signal oscillates with constant amplitude), STOP simulating
    - The Kp value causing sustained oscillations is Ku (ultimate gain)
    - Then call `find_peaks` on that simulation result to get Pu (ultimate period) from `average_peak_period`
    
    **CRITICAL**: 
    - Do NOT call this tool multiple times with the same parameters - the result is stored in context
    - After a successful simulation, use analysis tools (`find_characteristic_points`, `find_peaks`, etc.) on the stored result when needed
    - Do NOT re-simulate just to get the same data - reuse the stored simulation result

    """
    try:
        fmu_path = ctx.deps.state.fmu.fmu_path
    except Exception as e:
        return ToolExecutionError(message=str(e))
    # Normalize start_values: convert string 'inf' to float('inf')
    if sim_props.start_values:
        normalized_start_values = {}
        for key, value in sim_props.start_values.items():
            if isinstance(value, str):
                # Handle various string representations of infinity
                value_lower = value.lower().strip()
                if value_lower in ('inf', 'infinity', "float('inf')", 'float("inf")', "float('inf')", 'float("inf")'):
                    normalized_start_values[key] = float('inf')
                else:
                    normalized_start_values[key] = value
            else:
                normalized_start_values[key] = value
        # Create a new sim_props with normalized values
        sim_props = sim_props.model_copy(update={'start_values': normalized_start_values})
    
    try:
        console.print(f"simulate step response:")
        console.print(sim_props)
        console.print(step_props)
        data = _simulate_step_response(fmu_path, sim_props, step_props)
        
        # Limit stored simulations to prevent context window bloat
        # Keep only the most recent simulations (tools use simulations[-1])
        # Default: 3 simulations (sufficient for most workflows, prevents context bloat)
        MAX_STORED_SIMULATIONS = int(os.getenv('MAX_STORED_SIMULATIONS', '3'))
        ctx.deps.state.fmu.simulations.append(SimulationRun(
            sim_props=sim_props,
            step_props=step_props,
            data=data,
            fopdt_checks=[],
            attributes=[]
        ))
        # Remove oldest simulations if we exceed the limit
        if len(ctx.deps.state.fmu.simulations) > MAX_STORED_SIMULATIONS:
            ctx.deps.state.fmu.simulations = ctx.deps.state.fmu.simulations[-MAX_STORED_SIMULATIONS:]
        
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=ctx.deps.state,
        )

    except Exception as e:
        error_msg = str(e)
        print(f"Error in simulate step response: {error_msg}")
        # Provide more helpful error message for common issues
        if "Failed to instantiate" in error_msg or "Server" in error_msg or "mi2SetReal" in error_msg:
            enhanced_msg = (
                f"Simulation failed: {error_msg}. "
                "Common causes: invalid start_values format (e.g., Ti='inf' as string instead of float('inf')), "
                "missing required parameters, or unstable controller parameters. "
                "Check start_values and try adjusting parameters. Do NOT retry the same failed simulation."
            )
            return ToolExecutionError(message=enhanced_msg)
        return ToolExecutionError(message=error_msg)


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
        
def oscillation_analysis(ctx: RunContext[StateDeps[SimContext]]) -> StateSnapshotEvent|ToolExecutionError:
    try:
        if len(ctx.deps.state.fmu.simulations) == 0:
            return ToolExecutionError(message="No simulations have been run yet")
    except Exception as e:
        return ToolExecutionError(message=str(e))
    try:
        console.print(f"simulate step response:")
        data = ctx.deps.state.fmu.simulations[-1].data
        #console.print(data)
        oscillation_result = _oscillation_analysis(data)
        ctx.deps.state.fmu.simulations[-1].attributes.append(oscillation_result)
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=ctx.deps.state,
        )
    
    except Exception as e:
        print(f"Error in oscillation analysis: {e}")
        return ToolExecutionError(message=str(e))

def find_characteristic_points(ctx: RunContext[StateDeps[SimContext]]) -> StateSnapshotEvent|ToolExecutionError:
    """
    Finds the characteristic points of step responses from the most recent simulation.
    
    **WHEN TO USE**:
    - Use this tool when you need to analyze step response characteristics (e.g., for system identification, tuning)
    - Do NOT call this tool automatically after every simulation - only when analysis is needed for the task
    - For simple "simulate and return data" tasks, this tool is typically NOT needed
    
    **IMPORTANT**:
    - Call this tool ONCE per simulation - the result is stored in context
    - Do NOT call this tool multiple times for the same simulation - reuse the stored result
    - This tool analyzes the most recent simulation automatically
    
    Args:
        Uses the most recent simulation from context (no parameters needed)
        
    Returns:
        ResponseModel: Contains **critical points** for analyzing step responses and fine-tuning controllers.
            - p0 = (t0,y0) point when output starts to change from initial value.
            - p10 = (t10,y10) point when output first reaches 10% of total change.
            - p63 = (t63,y63) point when output first reaches 63% of total change. Can be used to determine the time constant T of a FOPDT system.
            - p90 = (t90,y90) point when output first reaches 90% of total change.
            - p98 = (t98,y98) point when output first reaches 98% of total change.
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
    
    **For Ultimate Gain / Ziegler-Nichols method**: 
    - REQUIRED: Call this tool after EACH simulation to check for oscillations
    - The tool analyzes the most recent simulation automatically
    - The result is stored in the simulation's attributes
    - Access `average_peak_period` from `result.attributes[0].average_peak_period` to get Pu (ultimate period)
    - If `find_peaks` detects multiple peaks with consistent period, you have sustained oscillations
    - When sustained oscillations are detected: STOP simulating, use that Kp as Ku, use `average_peak_period` as Pu
    
    **WHEN TO USE:**
    - For ultimate gain experiments: Call this after EACH simulation to check for oscillations
    - Keep simulating with increasing Kp until `find_peaks` detects sustained oscillations (multiple peaks)
    - Once sustained oscillations are found, use that simulation's Kp (Ku) and `average_peak_period` (Pu)
    
    Args:
        props: FindPeaksProps containing peak detection properties (typically use default values: `FindPeaksProps()`)
        
    Returns:
        StateSnapshotEvent with peaks data stored in simulation attributes. 
        Access Pu via: `result.snapshot.fmu.simulations[-1].attributes[-1].average_peak_period`
        Or check the tool return message for the `average_peak_period` value.
    """
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
    """
    Compute PID controller parameters using the Ziegler-Nichols closed-loop
    (also called ultimate gain or continuous-cycling) tuning method.
    
    **CRITICAL PREREQUISITES**: You MUST determine Ku and Pu BEFORE calling this tool:
    
    1. Run closed-loop simulations with a P controller (NOT PI):
       - Set `mode=True` (closed-loop mode)
       - Set `Ti=float('inf')` (use Python float('inf'), NOT the string 'inf')
       - Set `Kp` to different values, gradually increasing until you see sustained oscillations
       - The Kp value that causes sustained oscillations is Ku (ultimate gain)
       - If simulation fails, check error message and adjust parameters - do NOT retry same failed simulation
    
    2. Use `find_peaks` on the oscillating simulation result:
       - The `average_peak_period` from find_peaks gives you Pu (ultimate period)
    
    3. Only THEN call this tool with Ku and Pu values.
    
    **DO NOT call this tool without Ku and Pu values** - it will fail and waste tokens.
    
    Args:
        props: UltimateTuningProps containing:
            - Ku: Ultimate gain (the Kp value that causes sustained oscillations)
            - Pu: Ultimate period (from find_peaks average_peak_period)
            - controller: Type of controller to tune ("pi" or "pid")
            - method: Tuning method (typically "classic")
            
    Returns:
        PIDParameters containing the PID controller parameters (Kp, Ti, Td).
    """
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

# Build the tool list with stored I/O
def get_tools() -> list[Tool[Any]]:
    """Get list of tools, optionally with guardrails applied."""
    guardrails_enabled = os.getenv("GUARDRAILS_ENABLED", "true").lower() == "true"
    validator = SimulationGuardrails() if guardrails_enabled else None
    
    def maybe_guard(tool_func, tool_name: str):
        """Apply guardrails to a tool function if enabled."""
        if validator and tool_name in [
            "simulate_step_response",
            "choose_fmu",
            "identify_fopdt_from_step",
            "lambda_tuning",
            "zn_pid_tuning",
        ]:
            return apply_guardrails(tool_func, validator, tool_name, enabled=True)
        return tool_func
    
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

        Tool(look_at_plot,
            name="look_at_signal_plot",
            description=look_at_plot.__doc__,
            takes_ctx=True),

        Tool(get_step_response_data,
            name="get_step_response_data",
            description=get_step_response_data.__doc__,
            takes_ctx=True),

        Tool(maybe_guard(choose_fmu, "choose_fmu"),    
            name="choose_fmu",
            description=choose_fmu.__doc__,
            takes_ctx=True),
        Tool(get_model_description,
            name="get_model_description",
            description=get_model_description.__doc__,
            takes_ctx=True),

        Tool(maybe_guard(simulate_step_response, "simulate_step_response"),
            name="simulate_step_response",
            description=simulate_step_response.__doc__,
            takes_ctx=True),

        Tool(maybe_guard(identify_fopdt_from_step, "identify_fopdt_from_step"),
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

        Tool(find_overshoot,
            name="find_overshoot",
            description=make_docstring(_find_overshoot, find_overshoot),
            takes_ctx=True),

        Tool(oscillation_analysis,
            name="oscillation_analysis",
            description=make_docstring(_oscillation_analysis, oscillation_analysis),
            takes_ctx=True),

        Tool(find_settling_time,
            name="find_settling_time",
            description=find_settling_time.__doc__,
            takes_ctx=True),

        Tool(maybe_guard(zn_pid_tuning, "zn_pid_tuning"),
            name="zn_pid_tuning",
            description=zn_pid_tuning.__doc__,
            takes_ctx=True),

        Tool(maybe_guard(lambda_tuning, "lambda_tuning"),
            name="lambda_tuning",
            description=lambda_tuning.__doc__,
            takes_ctx=True),
        ]

