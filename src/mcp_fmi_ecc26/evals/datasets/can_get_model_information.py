
from __future__ import annotations
from typing import Any
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Contains, IsInstance, LLMJudge
from pydantic_ai_examples.evals.custom_evaluators import AgentCalledTool

input_type = str
from typing import List




# Evaluation dataset for testing agent capabilities
dataset = Dataset["str", "str", Any](
    cases=[
        Case(
            name='get_model_info',
            inputs="Cah you run the simulation tool? on the FMU named PI_FOPDT.fmu",
            metadata={
                'focus': 'tool use ',
                'description': 'Tests if the agent is able to use the simulation tool'
            },
            evaluators=(
                IsInstance(type_name='str'),
                Contains(value="id", case_sensitive=False),
                AgentCalledTool(agent_name='simulation_agent', tool_name='run_simulation_tool'),
            ),
        ),
    ],

)

###
""""
                LLMJudge(
                    rubric=f'It shall become apparent that the agent hasn been aboe to run the tools to provide information about the model.',
                    include_input=True,
                    model='openai:gpt-4o',
                ),

    evaluators=[
        LLMJudge(
            rubric='The agent should demonstrate correct tool usage and provide accurate answers.',
            include_input=True,
            model='openai:gpt-4o',
        ),
    ],


"""