from pydantic_evals import Case, Dataset
from .types import ExperimentInputType, ExperimentOutputType, ExperimentMetadataType
from .agent import agent_name
from .custom_evaluators import ListModels_Evaluator
from pydantic_evals.evaluators import LLMJudge
from control_agent.evals.evaluators import Yaysayer
from pydantic_ai_examples.evals.custom_evaluators import AgentCalledTool

dataset = Dataset[ExperimentInputType, ExperimentOutputType, ExperimentMetadataType](
    cases=[
        Case(
            name='get_fmu_names',
            inputs="Please list all the FMU models in the system",
            expected_output=ExperimentOutputType(
                model_names=["PI_FOPDT_2"]
            ),
            metadata=ExperimentMetadataType(
                focus='tool use',
                description='Tests if the agent is able to list all the FMU models in the system'
            ),
            evaluators=(
                Yaysayer(foo="hello", bar=1, baz=2.0, zip=True),
                ListModels_Evaluator(model_names=["PI_FOPDT_2"]),
                AgentCalledTool(
                    agent_name=agent_name,
                    tool_name='get_fmu_names'
                ),
                LLMJudge(
                    rubric='The agent should return a structured output, that should contain a list with ["PI_FOPDT_2"]',
                    include_input=True,
                    model='openai:gpt-4o',
                ),
            ),
        ),
    ],
)
