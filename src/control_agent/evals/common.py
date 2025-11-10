from pydantic_ai import Agent
from pydantic import BaseModel
from pydantic_evals import Dataset, Case
from typing import List, Type, Callable, Any, Generic, TypeVar, Coroutine
from control_agent.agent.agent import create_agent, AgentDepsT, OutputDataT
from control_agent.agent.model import get_default_model
from control_agent.agent.agent import get_tools
from pydantic_evals.evaluators import Evaluator, EqualsExpected, EvaluatorContext, EvaluationReason, EqualsExpected
from dataclasses import dataclass

from control_agent.evals.evaluators.equals_expecter_with_reason import EqualsExpectedWithReason

def get_agent_runner(output_model: Type[OutputDataT]) -> Callable[[str], Coroutine[Any, Any, OutputDataT]]:
    agent = create_agent(
        model=get_default_model(),
        tools=get_tools(),
        output_type=output_model,
    )
    def runner(input: str) -> OutputDataT:
        result = agent.run_sync(input, output_type=output_model)
        return result.output
    return runner