from typing import Any, Type

from pydantic_ai import Agent, Tool
from pydantic_ai.models import Model, KnownModelName

# System prompt with tuning method documentation
from control_agent.agent.tools import get_tools
from control_agent.agent.model import get_default_model
from pydantic_ai._run_context import AgentDepsT
from pydantic_ai.output import OutputDataT

from control_agent.prompts import SYS_PROMPT as SYSTEM_PROMPT

def create_agent(
    model: Model | KnownModelName | str = get_default_model(),
    max_retries: int = 1,
    name: str = "FMIAgent",
    deps: Type[AgentDepsT] = str,
    output_type: Type[OutputDataT] = str,
    tools: list[Tool[Any]] = get_tools(),
) -> Agent[AgentDepsT, OutputDataT]:
    """Create FMI agent with tools.
    
    Args:
        model_name: Azure OpenAI deployment name
        temperature: LLM temperature
        verbose: Enable verbose logging
        max_iterations: Maximum iterations (not used by pydantic_ai directly)
        max_retries: Maximum retries for tool calls
    Returns:
        Configured pydantic_ai Agent
    """

    # Create agent with tools
    return Agent[AgentDepsT, OutputDataT]( # type: ignore
        model=model,
        instructions=SYSTEM_PROMPT,
        name=name,
        retries=max_retries,
        deps_type=deps or AgentDepsT,
        output_type=output_type,
        tools=tools
    )

