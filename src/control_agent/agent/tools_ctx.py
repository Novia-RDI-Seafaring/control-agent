from pydantic_ai._run_context import RunContext

from control_toolbox.tools.information import get_fmu_names, get_model_description
from control_toolbox.tools.simulation import simulate_step_response as _simulate_step_response, simulate as _simulate
from control_toolbox.tools.identification import identify_fopdt_from_step as _identify_fopdt_from_step
from control_toolbox.tools.analysis import find_inflection_point as _find_inflection_point, find_characteristic_points as _find_characteristic_points, find_peaks as _find_peaks, find_settling_time as _find_settling_time 
from control_toolbox.tools.identification import IdentificationProps, FOPDTModel
from control_toolbox.tools.simulation import SimulationStepResponseProps, StepProps
from control_toolbox.tools.analysis import AttributesGroup, FindPeaksProps, InflectionPointProps, SettlingTimeProps
from typing import Any, Union, Tuple
from pydantic_ai.tools import Tool
from control_agent.agent.stored_model import StoredModel, ModelStore
from logging import getLogger
logger = getLogger(__name__)
from control_toolbox.core import DataModel, DataModelTeaser
from pydantic import BaseModel
class SimulationResponse(BaseModel):
    repr_id: str
    data: DataModel

def simulate_step_response(ctx: RunContext[ModelStore],
        sim_props: SimulationStepResponseProps,
        step_props: StepProps,
    ) -> SimulationResponse:
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
    print(f"simulate step response with props: {sim_props} and step props: {step_props}")
    assert sim_props.fmu_name is not None, "FMU name is required"
    with ctx.tracer.start_as_current_span(f"Simulating step response ({sim_props.fmu_name}, {sim_props.start_time}, {sim_props.stop_time}, {sim_props.output_interval})") as span:
        span.set_attribute("fmu_name", sim_props.fmu_name)
        span.set_attribute("start_time", str(sim_props.start_time))
        span.set_attribute("stop_time", str(sim_props.stop_time))
        span.set_attribute("output_interval", str(sim_props.output_interval))

        
        # {sim_props} and step props: {step_props}"):
        logger.debug(f"Simulating step response with props: {sim_props} and step props: {step_props}")
        try:
            span.add_event(f"will store it")
            print("will store it")
            from devtools import debug
            debug(sim_props)
            debug(step_props)
            data = _simulate_step_response(sim_props, step_props)
            debug(data)
            dm = ctx.deps.convert(data)
            span.add_event(f"stored it")
            print("stored it")
            debug(dm)
            return SimulationResponse(repr_id=dm.repr_id, data=data)
        except Exception as e:
            logger.error(f"Error simulating step response: {e}")
            raise e


def identify_fopdt_from_step(ctx: RunContext[ModelStore],
        repr_id: str,
        props: IdentificationProps,
    ) -> FOPDTModel:
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
    print(f"identify FOPDT model with repr_id: {repr_id} and props: {props}")
    logger.debug(f"Identifying FOPDT model with props: {props}")
    try:
        return _identify_fopdt_from_step(
            ctx.deps.recreate(repr_id),
            props
        )
    except Exception as e:
        logger.error(f"Error identifying FOPDT model: {e}")
        raise e

def find_inflection_point(ctx: RunContext[ModelStore],
        repr_id: str,
        props: InflectionPointProps,
    ) -> AttributesGroup:
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
    print(f"find inflection point with repr_id: {repr_id} and props: {props}")
    logger.debug(f"Finding inflection point with props: {props}")
    try:
        data = ctx.deps.recreate(repr_id)
    except Exception as e: raise e
    try:    
        response = _find_inflection_point(data, props)
    except Exception as e:
        logger.error(f"Error finding inflection point: {e}")
        raise e
    return response

from control_toolbox.tools.analysis import find_rise_time as _find_rise_time
def find_rise_time(ctx: RunContext[ModelStore],
        repr_id: str,
    ) -> AttributesGroup:
    """
    Finds the rise time of a signal.
    Args:
        repr_id: the id representing data from a simulation run, that is used to get the full DataModel containing the step response data (the full data is not used as to not clutter the context window with lots of numbers)
    Returns:
        AttributesGroup containing the rise time.
        the AttributesGroup contains the timestamp, value and rise time of the signal.
        the AttributesGroup also contains a description of the rise time.
    """
    print(f"find rise time with repr_id: {repr_id}")
    return _find_rise_time(ctx.deps.recreate(repr_id))

def find_characteristic_points(ctx: RunContext[ModelStore],
        repr_id: str
    ) -> AttributesGroup:
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
    print(f"find characteristic points with repr_id: {repr_id}")
    return _find_characteristic_points(ctx.deps.recreate(repr_id))

from control_toolbox.tools.pid_tuning import PIDParameters, lambda_tuning as _lambda_tuning, LambdaTuningProps
from control_toolbox.tools.identification import FOPDTModel
def lambda_tuning(model: FOPDTModel,
        props: LambdaTuningProps,
    ) -> PIDParameters:
    """
    Compute PID controller parameters using the Lambda tuning method.
    """
    print(f"lambda tuning with model: {model} and props: {props}")
    try:
        response = _lambda_tuning(data, props)
        return response
    except Exception as e:
        logger.error(f"Error lambda tuning: {e}")
        raise e
    return response
    
def find_peaks(ctx: RunContext[ModelStore],
        repr_id: str,
        props: FindPeaksProps,
    ) -> AttributesGroup:
    """
    Find peaks inside a signal based on peak properties.

    This function takes DataModel and finds all local maxima by simple comparison of neighboring values.
    Optionally, a subset of these peaks can be selected by specifying conditions for a peak's properties.
    
    Args:
        repr_id: the id representing data from a simulation run, that is used to get the full DataModel containing the step response data (the full data is not used as to not clutter the context window with lots of numbers)
    """
    print(f"find peaks with props: {props}")
    return _find_peaks(ctx.deps.recreate(repr_id), props)

def find_settling_time(ctx: RunContext[ModelStore],
        repr_id: str,
        props: SettlingTimeProps,
    ) -> AttributesGroup:
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
    print(f"find settling time with props: {props}")
    return _find_settling_time(ctx.deps.recreate(repr_id), props)

from control_toolbox.tools.pid_tuning import UltimateTuningProps, PIDParameters, zn_pid_tuning as _zn_pid_tuning
def zn_pid_tuning(ctx: RunContext[ModelStore],
        repr_id: str,
        props: UltimateTuningProps,
    ) -> PIDParameters:
    """
    Compute PID controller parameters using the Ziegler-Nichols closed-loop
    (also called ultimate gain or continuous-cycling) tuning method.
    
    Args:
        repr_id: the id representing data from a simulation run, that is used to get the full DataModel containing the step response data (the full data is not used as to not clutter the context window with lots of numbers)
        props: UltimateTuningProps containing the ultimate tuning properties
            - controller: Type of controller to tune.
            - method: Method to tune the controller.
    Returns:
        PIDParameters containing the PID controller parameters.
    """
    print(f"zn pid tuning with props: {props}")
    return _zn_pid_tuning(ctx.deps.recreate(repr_id), props)

 
## add rise time,  and lam

# Build the tool list with stored I/O
def get_tools() -> list[Tool[Any]]:
    return [

        # information tools
        Tool(get_fmu_names,
            name="get_fmu_names",
            description=get_fmu_names.__doc__,
            takes_ctx=False),
        Tool(get_model_description,
            name="get_model_description",
            description=get_model_description.__doc__,
            takes_ctx=False),

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
            takes_ctx=False),
        ]


if __name__ == "__main__":

    tools = get_tools()
    print(tools)
    from pathlib import Path
    fmu_dir = Path("models/fmus")
    from control_toolbox.config import set_fmu_dir
    set_fmu_dir(fmu_dir)
    from control_agent.agent.stored_model import get_repr_store
    from control_agent.agent.agent import create_agent
    agent = create_agent(model="openai:gpt-4o", tools=tools, deps=ModelStore)
    import asyncio
    result = asyncio.run(agent.run("What is the name of the FMU?", deps=get_repr_store()))
    print(result)
    storage = get_repr_store()
    ctx = RunContext[ModelStore](
        model="openai:gpt-4o",    
        usage = result.usage,                        

        deps=storage
    )
    try:
        from control_toolbox.tools.signals import TimeRange
        result = simulate_step_response(ctx, 
            SimulationStepResponseProps(
                fmu_name="PI_FOPDT_2",
                start_time=0.0,
                stop_time=1.0,
                output_interval=0.1,
            ), StepProps(
                signal_name="input",
                time_range=TimeRange(start=0.0, stop=1.0, sampling_time=0.1),
                initial_value=0.0,
                final_value=1.0,
            )
        )
        id = result.repr_id
        from devtools import debug
        debug(result)
        full = storage.recreate(id)
        debug(full)
    except Exception as e:
        print(f"Error simulating step response: {e}")
        raise e
    print(result)