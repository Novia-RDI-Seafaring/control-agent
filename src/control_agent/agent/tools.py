from pydantic_ai import Tool

from typing import Any
from control_toolbox.tools.information import get_fmu_names, get_model_description
from control_toolbox.tools.simulation import simulate_step_response
from control_toolbox.tools.identification import identify_fopdt_from_step
from control_toolbox.tools.analysis import find_inflection_point, find_characteristic_points, find_peaks, find_settling_time


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

        #simulate
        Tool(simulate_step_response,
            name="simulate_step_response",
            description=simulate_step_response.__doc__,
            takes_ctx=False),
        Tool(identify_fopdt_from_step,
            name="identify_fopdt_from_step",
            description=identify_fopdt_from_step.__doc__,
            takes_ctx=False),

        # analysis
        Tool(find_inflection_point,
            name="find_inflection_point",
            description=find_inflection_point.__doc__,
            takes_ctx=False),
        Tool(find_characteristic_points,
            name="find_characteristic_points",
            description=find_characteristic_points.__doc__,
            takes_ctx=False),
        Tool(find_peaks,
            name="find_peaks",
            description=find_peaks.__doc__,
            takes_ctx=False),
        Tool(find_settling_time,
            name="find_settling_time",
            description=find_settling_time.__doc__,
            takes_ctx=False),
]
