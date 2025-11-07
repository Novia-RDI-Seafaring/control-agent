
from __future__ import annotations
from typing import Any
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Contains, IsInstance, Equals
from pydantic_ai_examples.evals.custom_evaluators import AgentCalledTool
from pydantic_evals.evaluators import LLMJudge
from pydantic import BaseModel
from pydantic_ai import Agent
from agent.agent import create_agent
from evals.evaluators import Yaysayer, ListModelsEvaluator
from pydantic_evals.evaluators import Evaluator
from typing import List

class ExperimentModelListOutput(BaseModel):
    model_names: List[str]

class ExperimentModelListMetadata(BaseModel):
    focus: str
    description: str

    


ExperimentInputType = str
ExperimentOutputType = ExperimentModelListOutput
ExperimentMetadataType = ExperimentModelListMetadata

agent = create_agent(
    name="FMIAgentModelList",
    input_type=ExperimentInputType,
    output_type=ExperimentOutputType,
)

# Evaluation dataset for testing agent capabilities
dataset = Dataset[str, ExperimentModelListOutput, ExperimentModelListMetadata](
    cases=[
        Case(
            name='get_fmu_names',
            inputs="Please list all the FMU models in the system",
            expected_output=ExperimentModelListOutput(
                model_names=["PI_FOPDT_2"]
            ),
            metadata=ExperimentModelListMetadata(
                focus='tool use',
                description='Tests if the agent is able to list all the FMU models in the system'
            ),
            evaluators=(
                Yaysayer(foo="hello", bar=1, baz=2.0, zip=True),
                ListModelsEvaluator(model_names=["PI_FOPDT_2"]),
                AgentCalledTool(
                    agent_name="FMIAgentModelList",
                    tool_name='get_fmu_names'),
                LLMJudge(
                    rubric='The agent should return a structured output, that should contain a list with ["PI_FOPDT_2"]',
                    include_input=True,
                    model='openai:gpt-4o',
                ),
            ),
        ),
    ],

)
