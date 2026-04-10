from control_agent.agent.common import *
from control_agent.agent.model import get_default_model
from control_agent.agent.sys_prompt import SYS_PROMPT as SYSTEM_PROMPT

def create_agent(
    model: Model | KnownModelName | str = get_default_model(),
    max_retries: int = 1,
    name: str = "FMIAgent",
    deps: Type[AgentDepsT] = str,
    tools: list[Tool[Any]] = [],
    output_type: Type[OutputDataT] = str,
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

