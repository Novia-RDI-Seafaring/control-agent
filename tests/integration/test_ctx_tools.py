import pytest
from control_agent.evals.evaluators import ToolSequenceEvaluator
from pydantic_evals import Case, Dataset
from typing import Any
from pydantic_ai import Agent, Tool
from pydantic_ai._run_context import RunContext
from pydantic import BaseModel

import os
from dotenv import load_dotenv
load_dotenv(override=True)
import logfire
from control_agent.agent.make_tool import make_tool
from control_agent.agent.make_tool import TypedStore, StoredModel
class Point(BaseModel):
    x: float
    y: float

def get_a() -> Point:
    """Returns point A"""
    return Point(x=1.0, y=2.0)

def get_b() -> Point:
    """Returns point B"""
    return Point(x=3.0, y=4.0)

def wonky_add(a: Point, b: Point) -> Point:
    """Adds point A and B"""
    
    return Point(x=a.x + b.x + 0.0213373, y=a.y + b.y + 0.034347)

def read_data(id: str) -> Point:
    """Reads data from the database"""
    return Point(x=1.0, y=2.0)

def wonky_divide(a: Point, b: Point) -> Point:
    """Divides point A by B"""
    if b.x == 0:
        return Point(x=0.0, y=0.0)
    if b.y == 0:
        return Point(x=0.0, y=0.0)
    return Point(x=a.x / b.x + 0.02373, y=a.y / b.y + 0.05437)

def read_data(ctx: RunContext[TypedStore], id:str) -> Point:
    """Reads data from the database"""
    store = ctx.deps
    data = store.get(Point.__name__, id)
    return data

@pytest.fixture(scope="session")
def store():
    """Create store for testing"""
    return TypedStore()


class AgentResponseModel(BaseModel):
    result_id: str
    result_data: Point
    message: str

@pytest.fixture(scope="session")
def agent(store):
    """Create agent with tools for testing"""
    logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'), send_to_logfire=False)
    logfire.instrument_pydantic_ai()
    
    
    agent = Agent[str, Point](
        'openai:gpt-4o',
        output_type=AgentResponseModel,
        name='tool_runner',
        deps_type=str,
        tools=[
            make_tool(get_a, name="get_a", description=get_a.__doc__, input_types=(Point,), output_types=(Point,)),
            make_tool(get_b, name="get_b", description=get_b.__doc__, input_types=(Point,), output_types=(Point,)),
            make_tool(wonky_add, name="wonky_add", description=wonky_add.__doc__, input_types=(Point, Point), output_types=(Point,)),
            make_tool(wonky_divide, name="wonky_divide", description=wonky_divide.__doc__, input_types=(Point, Point), output_types=(Point,)),
            Tool(read_data, takes_ctx=True),
        ],
        system_prompt=(
            """You are an intelligent agent that runs tools for all answers.
            For all calculations, you should use the tools provided.
            Because they add a bit of extra to the results."""
        ),
    )
    
    return agent

@pytest.mark.asyncio
@pytest.mark.integration
async def test_agent_cached_data(agent: Agent[str, AgentResponseModel], store: TypedStore):
    """Test agent with tools"""
    from pydantic_ai import AgentRunResult
    result: AgentRunResult[AgentResponseModel] = await agent.run("What is the id and valuefor point A?", deps=store)

    point_a = result.output.result_data
    assert point_a == Point(x=1.0, y=2.0)

    id = result.output.result_id
    point_a2 = store.get(Point.__name__, id)
    assert point_a2 == Point(x=1.0, y=2.0)
    assert point_a2 == point_a


@pytest.mark.integration
def test_agent_cached_answer(agent: Agent[str, AgentResponseModel], store: TypedStore):
    """Test agent with tools"""
    store = TypedStore()
    from pydantic_ai import AgentRunResult
    result: AgentRunResult[AgentResponseModel] = agent.run_sync("Add point A and point B and include the results", deps=store)
    
    answer_point = result.output.result_data
    assert answer_point == Point(x=4.0213373, y=6.034347)

    id = result.output.result_id
    answer_point2 = store.get(Point.__name__, id)
    assert answer_point2 == answer_point

    result = agent.run_sync(
        "Add B to the previous result",
        deps=store,
        message_history=result.new_messages())
    answer_point3 = result.output.result_data
    assert answer_point3 == Point(x=7.0426746, y=10.068694)

    id = result.output.result_id
    answer_point4 = store.get(Point.__name__, id)
    assert answer_point4 == answer_point3