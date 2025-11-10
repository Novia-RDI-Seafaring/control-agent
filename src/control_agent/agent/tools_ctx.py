from control_toolbox.tools.information import get_fmu_names, get_model_description
from control_toolbox.tools.simulation import simulate_step_response
from control_toolbox.tools.identification import identify_fopdt_from_step
from control_toolbox.tools.analysis import find_inflection_point, find_characteristic_points, find_peaks, find_settling_time

from control_agent.agent.make_tool import make_tool

from typing import Any
from pydantic_ai.tools import Tool


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



        make_tool(
            simulate_step_response,
            name="simulate_step_response",
            description=simulate_step_response.__doc__,
        ),
        make_tool(
            identify_fopdt_from_step,
            name="identify_fopdt_from_step",
            description=identify_fopdt_from_step.__doc__,
        ),

        # analysis
        make_tool(
            find_inflection_point,
            name="find_inflection_point",
            description=find_inflection_point.__doc__,
        ),
        make_tool(
            find_characteristic_points,
            name="find_characteristic_points",
            description=find_characteristic_points.__doc__,
        ),
        make_tool(
            find_peaks,
            name="find_peaks",
            description=find_peaks.__doc__,
        ),
        make_tool(
            find_settling_time,
            name="find_settling_time",
        )
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