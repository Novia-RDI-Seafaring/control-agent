import pytest
from control_agent.evals.schemas.responses import *
from control_agent.agent.core.agent import create_agent


@pytest.fixture
def agent():
    return create_agent()

