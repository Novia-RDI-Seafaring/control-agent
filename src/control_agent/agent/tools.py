from control_agent.agent.common import *

def get_tools() -> list[Tool[Any]]:
    return [
        # information tools
        Tool(_get_fmu_names,
            name="get_fmu_names",
            description=_get_fmu_names.__doc__,
            takes_ctx=False),
        Tool(_get_model_description,
            name="get_model_description",
            description=_get_model_description.__doc__,
            takes_ctx=False),

        #simulate
        Tool(_simulate_step_response,
            name="simulate_step_response",
            description=_simulate_step_response.__doc__,
            takes_ctx=False),
        Tool(_identify_fopdt_from_step,
            name="identify_fopdt_from_step",
            description=_identify_fopdt_from_step.__doc__,
            takes_ctx=False),

        # analysis
        # Tool(find_inflection_point,
        #    name="find_inflection_point",
        #    description=find_inflection_point.__doc__,
        #    takes_ctx=False),
        Tool(_find_characteristic_points,
            name="find_characteristic_points",
            description=_find_characteristic_points.__doc__,
            takes_ctx=False),
        Tool(_find_peaks,
            name="find_peaks",
            description=_find_peaks.__doc__,
            takes_ctx=False),
        Tool(_find_settling_time,
            name="find_settling_time",
            description=_find_settling_time.__doc__,
            takes_ctx=False),
]
