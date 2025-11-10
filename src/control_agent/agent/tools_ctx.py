from control_toolbox.tools.information import get_fmu_names, get_model_description
from control_toolbox.tools.simulation import simulate_step_response as _simulate_step_response, simulate as _simulate
from control_toolbox.tools.identification import identify_fopdt_from_step as _identify_fopdt_from_step
from control_toolbox.tools.analysis import find_inflection_point as _find_inflection_point, find_characteristic_points as _find_characteristic_points, find_peaks as _find_peaks, find_settling_time as _find_settling_time 
from control_toolbox.config import get_fmu_dir
from control_agent.agent.make_tool import make_tool
from pydantic_ai._run_context import RunContext
from control_agent.agent.stored_model import TypedStore, StoredModel

from control_toolbox.core import ResponseModel
from control_toolbox.tools.simulation import SimulationProps, StepProps
from control_toolbox.tools.analysis import FindPeaksProps, InflectionPointProps, SettlingTimeProps
from control_toolbox.core import DataModel
from control_toolbox.tools.identification import IdentificationProps
from pathlib import Path
from typing import Any
from pydantic_ai.tools import Tool



def resolve_response(ctx: RunContext[TypedStore], stored_model: StoredModel) -> ResponseModel:
    """
    **Purpose:**  
    Resolve a stored model.
    But  beware, it may fill your context window.
    so you want to send teh stored model to tools instead of the resolved data

    **Inputs:**  
    - `StoredModel`: A JSON object matching the `StoredModel` schema with the following fields:  
        - `kind` (string) — Kind of the model.
        - `id` (string) — ID of the model.

    **Outputs:**  

    - `ResponseModel`: A JSON object matching the `ResponseModel` schema with the following fields:  
        - `source` (Optional[Source]) — Source of the tool and its arguments that generated the response.
        - `summary` (Optional[str]) — Summary of the response.
        - `data` (Optional[Union[DataModel, List[DataModel]]]) — Data associated with the response.
        - `attributes` (Optional[List[AttributesGroup]]) — Attributes associated with the response.
        - `payload` (Optional[Any]) — Any other object the tool needs toreturn.
        - `figures` (Optional[List[FigureModel]]) — Figures associated with the response.
        - `error` (Optional[ErrorModel]) — Error message if the response is not successful.

        in teh data there are signals, 
    """
    try:
        return stored_model.resolve(ctx.deps) # type: ignore
    except Exception as e:
        print(f"Error resolving response: {e}")
        raise e

def simulate_step_response(ctx: RunContext[TypedStore],
        sim_props: SimulationProps,
        step_props: StepProps,
        FMU_DIR: Path|None = None,
        generate_plot: bool = False,
    ) -> StoredModel[ResponseModel]:
    """
    
    **Purpose:**  
    Simulate a step response of a Functional Mock-up Unit (FMU) model using the specified parameters and input signals.

    **Inputs:**  
    - `SimulationProps`: Accepts a JSON object matching the `SimulationProps` schema with the following fields:  
        - `fmu_name` (string) — Name of the FMU to simulate.
        - `start_time` (float) — Simulation start time (in seconds). Typically 0.0 seconds.
        - `stop_time` (float) — Simulation stop time (in seconds).  
        - `input` (DataModel) — Input signal(s) defined over the time interval.

    **Outputs:**  
    - `StoredModel[ResponseModel]`, that has a handle to the data, that can be passed ot other tools can use to get teh actual result from the simulation.

    the ResponseModel which can be resolved from the StoredModel, has the following fields:
    
    """
    try:
        result = _simulate_step_response(sim_props, step_props, FMU_DIR, generate_plot)
        assert ctx.deps is not None, ctx
 
        stored_model = StoredModel.store(ctx.deps, result, kind="ResponseModel")
        return stored_model
    except Exception as e:
        print(f"Error simulating step response: {e}")
        raise e


def identify_fopdt_from_step(ctx: RunContext[TypedStore],
        stored_model: StoredModel[ResponseModel],
        identification_props: IdentificationProps,
    ) -> StoredModel[ResponseModel]:
    """
    **Purpose:**  
    Identify a FOPDT model from a step response.

    **Inputs:**  
    - `StoredModel[ResponseModel]`: A JSON object matching the `StoredModel` schema with the following fields:  
        - `kind` (string) — Kind of the model.
        - `id` (string) — ID of the model.

    - `IdentificationProps`: Accepts a JSON object matching the `IdentificationProps` schema with the following fields:  
        - `input_name` (string) — Name of the input signal.
        - `output_name` (string) — Name of the output signal.
        - `method` (string) — Method to identify the model.

    Note the signal name for input is "u" and the signal name for output is "y"
    """
    try:
        response = stored_model.resolve(ctx.deps)
        data:DataModel = response.data
        result = _identify_fopdt_from_step(data, identification_props)
        return StoredModel.store(ctx.deps, result, kind="ResponseModel")
    except Exception as e:
        print(f"Error identifying FOPDT from step: {e}")
        raise e


def find_inflection_point(ctx: RunContext[TypedStore],
        stored_model: StoredModel,
        props: InflectionPointProps,
    ) -> StoredModel:
    """
    **Purpose:**  
    Find the inflection point of a step response.
    """
    try:    
        response = stored_model.resolve(ctx.deps)
        data:DataModel = response.data
        result = _find_inflection_point(data, props)
        return StoredModel.store(ctx.deps, result, kind="ResponseModel")
    except Exception as e:
        print(f"Error finding inflection point: {e}")
        raise e


def find_characteristic_points(ctx: RunContext[TypedStore],
        stored_model: StoredModel
    ) -> StoredModel[ResponseModel]:
    """
    Finds the characteristic points of step responses.
    
    Args:
        data: DataModel containing the signal
        
    Returns:

    - `StoredModel[ResponseModel]`, that has a handle to the data, that can be passed ot other tools can use to get teh actual result from the simulation.

    the ResponseModel which can be resolved from the StoredModel, has the following fields:
        ResponseModel: Contains **critical points* analyzing step rsponses and finetuning controllers.
            - p0 = (t0,y0) point when output starts to change from initial value.
            - p10 = (t10,y10) point when output first reachest 10% of total change.
            - p63 = (t63,y63) point when output first reachest 63% of total change. Can be used to determine the time constant T of a FOPDT system.
            - p90 = (t90,y90) point when output first reachest 90% of total change.
            - p98 = (t98,y98) point when output first reachest 98% of total change.
    """
    try:
        response = stored_model.resolve(ctx.deps)
        data:DataModel = response.data
        assert data is not None, "there is no data in the stored model"
        result = _find_characteristic_points(data)
        return StoredModel.store(ctx.deps, result, kind="ResponseModel")
    except Exception as e:
        print(f"Error finding characteristic points: {e}")
        raise e


def find_peaks(ctx: RunContext[TypedStore],
        stored_model: StoredModel,
        props: FindPeaksProps,
    ) -> StoredModel[ResponseModel]:
    """
    **Purpose:**  
    Find the peaks of a step response.

    - `StoredModel[ResponseModel]`, that has a handle to the data, that can be passed ot other tools can use to get teh actual result from the simulation.

    the ResponseModel which can be resolved from the StoredModel, has the following fields:
        ResponseModel: Contains **peak analysis** analyzing step rsponses and finetuning controllers.
            - peaks: List[Peak] = List of peaks found in the signal.
            - peak_indices: List[int] = List of indices of the peaks.
            - peak_values: List[float] = List of values of the peaks.
    """
    try:
        response = stored_model.resolve(ctx.deps)
        data:DataModel = response.data
        result = _find_peaks(data, props)
        return StoredModel.store(ctx.deps, result, kind="ResponseModel")
    except Exception as e:
        print(f"Error finding peaks: {e}")
        raise e

def find_settling_time(ctx: RunContext[TypedStore],
        stored_model: StoredModel[ResponseModel],
        props: SettlingTimeProps,
    ) -> StoredModel[ResponseModel]:
    """
    **Purpose:**  
    Finds the settling time of a step response.

    Args:
        data: DataModel containing the signal
        
    Returns:

    - `StoredModel[ResponseModel]`, that has a handle to the data, that can be passed ot other tools can use to get teh actual result from the simulation.

    the ResponseModel which can be resolved from the StoredModel, has the following fields:
        ResponseModel: Contains **settling time** analyzing step rsponses and finetuning controllers.
            - settling_time: float = Settling time of the signal.
    """
    try:
        response = stored_model.resolve(ctx.deps)
        data:DataModel = response.data
        result = _find_settling_time(data, props)
        return StoredModel.store(ctx.deps, result, kind="ResponseModel")
    except Exception as e:
        print(f"Error finding settling time: {e}")
        raise e

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

        Tool(find_settling_time,
            name="find_settling_time",
            description=find_settling_time.__doc__,
            takes_ctx=True),
    ]


if __name__ == "__main__":

    tools = get_tools()
    print(tools)
    from control_agent.agent.make_tool import TypedStore

    from control_agent.agent.agent import create_agent
    agent = create_agent(model="openai:gpt-4o", tools=tools, deps=TypedStore)
    import asyncio
    result = asyncio.run(agent.run("What is the name of the FMU?", deps=TypedStore()))
    print(result)