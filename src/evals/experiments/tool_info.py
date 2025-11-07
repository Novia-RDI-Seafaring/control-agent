
from __future__ import annotations
from typing import Any
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Contains, IsInstance
from pydantic_ai_examples.evals.custom_evaluators import AgentCalledTool
from pydantic_evals.evaluators import LLMJudge

input_type = str
from typing import List


# Evaluation dataset for testing agent capabilities
dataset = Dataset["str", "str", Any](
    cases=[
        Case(
            name='get_model_info',
            inputs="Can you get model info for PI_FOPDT_2.fmu",
            metadata={
                'focus': 'tool use ',
                'description': 'Tests if the agent is able to get moedl indo'
            },
            evaluators=(
                AgentCalledTool(agent_name='FMIAgent', tool_name='get_model_description'),
                LLMJudge(
                    rubric='The agent should return an answer that shows we saw the model description.',
                    include_input=True,
                    model='openai:gpt-4o',
                ),
            ),
        ),
    ],

)
