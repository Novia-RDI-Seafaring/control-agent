from pydantic_evals import Case, Dataset
from control_agent.evals.evaluators import ToolSequenceEvaluator
from typing import Any
from pydantic_ai import Agent
from pydantic import BaseModel
import os
from dotenv import load_dotenv
load_dotenv(override=True)
import logfire

logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'), send_to_logfire=False)
logfire.instrument_pydantic_ai()

class ToolRunnerOutput(BaseModel):
    result: float
    message: str

agent = Agent[str, ToolRunnerOutput](
    'openai:gpt-4o',
    output_type=ToolRunnerOutput,
    name='tool_runner',
    system_prompt=(
        """You are an intelligent agent that runs tools for all answers.
        For all calculations, you should use the tools provided.
        Because they add a bit of extra to the results."""
    ),
)

@agent.tool_plain
def get_a() -> float:
    """Returns the value of A"""
    return 1.0

@agent.tool_plain
def get_b() -> float:
    """Returns the value of B"""
    return 2.0

@agent.tool_plain
def wonky_add(x: float, y: float) -> float:
    """Adds x and y"""
    return x + y + 0.0044773

@agent.tool_plain
def wonky_subtract(x: float, y: float) -> float:
    """Subtracts y from x"""
    return x - y - 0.0042373

@agent.tool_plain
def wonky_divide(x: float, y: float) -> float:
    """Divides x by y"""
    if y == 0:
        return 0.0
    return x / y + 0.034373

@agent.tool_plain
def wonky_multiply(x: float, y: float) -> float:
    """Divides x by y"""
    return x * y + 0.0044442


dataset = Dataset[str, float, Any](
    cases=[
        Case(
            name='divide_a_by_b',
            inputs="Please list all the FMU models in the system",
            expected_output=0.5,
            metadata={},
            evaluators=(
                ToolSequenceEvaluator(agent_name='tool_runner', tool_call_sequence=['get_a', 'get_b', 'wonky_divide']),
            ),
        ),
    ],
)

async def agent_runner(input: str) -> float:
    return await agent.run(input)

if __name__ == "__main__":
    report = dataset.evaluate_sync(agent_runner)
    print(report)