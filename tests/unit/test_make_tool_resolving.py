from control_agent.agent.make_tool import make_tool, TypedStore, StoredModel
from control_toolbox.core import ResponseModel, DataModel
from pydantic_ai._run_context import RunContext
from pydantic import BaseModel
import pytest
from pydantic_ai.tools import Tool

class Point(BaseModel):
    x: float
    y: float


def get_a() -> Point:
    """Returns point A"""
    return Point(x=1.0, y=2.0)

def get_b() -> Point:
    """Returns point B"""
    return Point(x=3.0, y=4.0)

def add(a: Point, b: Point) -> Point:
    """Returns point A + B """
    return Point(x=a.x + b.x, y=a.y + b.y)


@pytest.fixture
def tools():
    return [
        Tool(get_a, name="get_a", description=get_a.__doc__, takes_ctx=False),
        Tool(get_b, name="get_b", description=get_b.__doc__, takes_ctx=False),
        Tool(add, name="add", description=add.__doc__, takes_ctx=False),
    ]

@pytest.fixture
def storing_tools():
    return [
        make_tool(get_a, name="get_a", description=get_a.__doc__, input_types=(Point,), output_types=(Point,)),
        make_tool(get_b, name="get_b", description=get_b.__doc__, input_types=(Point,), output_types=(Point,)),
        make_tool(add, name="add", description=add.__doc__, input_types=(Point, Point), output_types=(Point,)),
    ]

@pytest.fixture
def ctx() -> RunContext[TypedStore]:
    store = TypedStore()
    return RunContext(model="openai:gpt-4o", usage="test_run_tools", deps=store)

def test_tools(ctx, tools):
    assert len(tools) == 3
    assert tools[0].name == "get_a"
    assert tools[0].description == "Returns point A"

    result = tools[0].function()
    assert isinstance(result, Point)

def test_storing_tools(ctx, storing_tools):
    assert len(storing_tools) == 3
    assert storing_tools[0].name == "get_a"
    assert storing_tools[0].description == "Returns point A"
    a = get_a()
    assert a.model_dump() == { "x": 1.0, "y": 2.0 }

    result = storing_tools[0].function(ctx)
    assert not isinstance(result, Point)
    assert hasattr(result, "id")

    assert result.resolve(ctx.deps).model_dump() == { "x": 1.0, "y": 2.0 }
    assert isinstance(result, StoredModel)
    assert result.is_of(Point)

    resolved = result.resolve(ctx.deps)
    assert isinstance(resolved, Point)
    assert resolved.model_dump() == { "x": 1.0, "y": 2.0 }