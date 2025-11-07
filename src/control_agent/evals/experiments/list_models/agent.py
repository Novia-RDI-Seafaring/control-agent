from control_agent.agent.agent import create_agent
from .types import ExperimentInputType, ExperimentOutputType

agent_name = "FMIAgentModelList"
agent = create_agent(
    name=agent_name,
    input_type=ExperimentInputType,
    output_type=ExperimentOutputType,
)