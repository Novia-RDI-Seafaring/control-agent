from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance, Contains, LLMJudge
from pydantic_ai_examples.evals.custom_evaluators import AgentCalledTool
from .agent import agent_name
from .world import SECRET_NUMBER, MESSAGE_ON_THE_FRIDGE

SECRET_NUMBER = 1234
MESSAGE_ON_THE_FRIDGE = "milk"

dataset = Dataset["str", "str", Any](
    cases=[
        Case(
            name='discover_secret_code',
            inputs="What is the code to unlock the door?",
            metadata={
                'focus': 'tool_discovery_and_correct_answer',
                'description': 'Tests if agent can discover and use the look_under_the_doormat tool'
            },
            evaluators=(
                IsInstance(type_name='str'),
                Contains(value=str(SECRET_NUMBER), case_sensitive=False),
                LLMJudge(
                    rubric=f'The agent should discover that the correct code is {SECRET_NUMBER}.',
                    include_input=True,
                    model='openai:gpt-4o',
                ),
                AgentCalledTool(agent_name='world_explorer', tool_name='look_under_the_doormat'),
            ),
        ),
        
        Case(
            name='complete_kitchen_mission',
            inputs="What is the message on the fridge?",
            metadata={
                'focus': 'sequential_tool_usage',
                'description': 'Tests if agent can sequence multiple tools correctly to achieve complex goal'
            },
            evaluators=(
                IsInstance(type_name='str'),
                Contains(value="milk", case_sensitive=False),
                LLMJudge(
                    rubric=f'The agent should find the message: "{MESSAGE_ON_THE_FRIDGE}".',
                    include_input=True,
                    model='openai:gpt-4o',
                ),
                # Required tool sequence for success
                AgentCalledTool(agent_name='world_explorer', tool_name='look_under_the_doormat'),
                AgentCalledTool(agent_name='world_explorer', tool_name='unlock_door'),
                AgentCalledTool(agent_name='world_explorer', tool_name='open_door'),
                AgentCalledTool(agent_name='world_explorer', tool_name='go_inside'),
                AgentCalledTool(agent_name='world_explorer', tool_name='turn_on_light'),
                AgentCalledTool(agent_name='world_explorer', tool_name='go_to_kitchen'),
                AgentCalledTool(agent_name='world_explorer', tool_name='read_message_on_the_fridge'),
            ),
        ),
        
        Case(
            name='planning_and_sequencing',
            inputs="List the steps needed to read the message on the fridge.",
            expected_output="look_under_the_doormat, unlock_door, open_door, go_inside, turn_on_light, go_to_kitchen, read_message_on_the_fridge",
            metadata={
                'focus': 'planning_ability',
                'description': 'Tests if agent can plan the correct sequence of actions'
            },
        ),
    ],
    evaluators=[
        LLMJudge(
            rubric='The agent should demonstrate correct tool usage and provide accurate answers.',
            include_input=True,
            model='openai:gpt-4o',
        ),
    ],
)
