import pytest
from control_agent.evals.response_schema import *
from control_agent.agent.agent import create_agent


@pytest.fixture
def agent():
    return create_agent()

