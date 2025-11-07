import os
from typing import Literal, Union, Any
from dotenv import load_dotenv

from pydantic_ai import Agent, Tool
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel
from pydantic_ai.models import Model, KnownModelName
from pydantic_ai.providers import Provider
from openai import AsyncOpenAI
from logging import getLogger
from prompts import SYS_PROMPT
from control_toolbox.tools.information import (
    get_fmu_names,
    get_model_description
)
from control_toolbox.tools.simulation import (
    simulate,
    simulate_step_response,
)

from control_toolbox.tools.identification import (
    identify_fopdt_from_step
)

from control_toolbox.tools.analysis import (
    find_inflection_point,
    find_characteristic_points,
    find_peaks,
    find_settling_time,
)

from control_toolbox.config import *

# set patch fo FMU models
set_fmu_dir(Path(__file__).parents[2] / "models" / "fmus")

logger = getLogger(__name__)
# Load environment variables
load_dotenv(override=True)

#default_provider = os.getenv("DEFAULT_PROVIDER", "openai")
#default_model = os.getenv("DEFAULT_MODEL", "openai:gpt-4o")

default_model = None
default_provider = "azure"

if os.getenv("AZURE_OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", None)) is not None:

    default_provider = "azure" if os.getenv("AZURE_OPENAI_API_KEY") is not None else "openai"
    match default_provider:
        case "azure":
            assert os.getenv("AZURE_OPENAI_ENDPOINT") is not None, "AZURE_OPENAI_ENDPOINT is not set"
            assert os.getenv("AZURE_OPENAI_API_KEY") is not None, "AZURE_OPENAI_API_KEY is not set"
            assert os.getenv("OPENAI_API_VERSION") is not None, "OPENAI_API_VERSION is not set" # see the docstring in class AzureProvider
            logger.info("Using Azure OpenAI as the default provider")
            default_provider = "azure"
            default_model = default_model or os.getenv("AZURE_OPENAI_DEPLOYMENT", default_model)
        case "openai":
            assert os.getenv("OPENAI_API_KEY") is not None, "OPENAI_API_KEY is not set"
            default_model = default_model
            default_provider = "openai"

else:
    logger.warning("""
        No default provider found, using default provider: %s.
        - To use OpenAI, set the OPENAI_API_KEY environment variable.
        - To use Azure OpenAI, set the following env variables:
            - AZURE_OPENAI_ENDPOINT (the endpoint of the Azure OpenAI service)
            - AZURE_OPENAI_API_KEY (the API key of the Azure OpenAI service)
            - OPENAI_API_VERSION (this is used by the AzureProvider class to set the API version)
    """)
assert default_provider is not None, "No default provider configured"
assert default_provider in ['azure', 'deepseek', 'cerebras', 'fireworks', 'github', 'grok', 'heroku', 'moonshotai', 'ollama', 'openai', 'openai-chat', 'openrouter', 'together', 'vercel', 'litellm', 'nebius', 'ovhcloud', 'gateway'], f"Default provider must be a Provider or a string: {type(default_provider)}, {default_provider}"
assert default_model is not None, "No default model configured"

def get_default_model(model_name: str = default_model, provider: Provider[AsyncOpenAI] | Literal['azure', 'deepseek', 'cerebras', 'fireworks', 'github', 'grok', 'heroku', 'moonshotai', 'ollama', 'openai', 'openai-chat', 'openrouter', 'together', 'vercel', 'litellm', 'nebius', 'ovhcloud', 'gateway'] = default_provider) -> OpenAIChatModel:
    global default_provider, default_model
    assert model_name is not None, "No default provider configured"
    assert default_model is not None, "No default model configured"
    assert model_name or default_model is not None
    return OpenAIChatModel(
        model_name=model_name.split(':')[1] if ':' in model_name else model_name,
        provider=provider
    )

# System prompt with tuning method documentation
SYSTEM_PROMPT = SYS_PROMPT

def get_tools() -> list[Tool[Any]]:
    return [
        # information tools
        Tool(get_fmu_names,
            name="get_fmu_names",
            description=get_fmu_names.__doc__,
            takes_ctx=False),
            Tool(get_model_description,
                name="get_model_description",
                description=get_model_description.__doc__,
                takes_ctx=False),

            # simulation tools
            # Tool(simulate,
            #    name="simulate",
            #    description=simulate.__doc__,
            #    takes_ctx=False),
            Tool(simulate_step_response,
                name="simulate_step_response",
                description=simulate_step_response.__doc__,
                takes_ctx=False),
            Tool(identify_fopdt_from_step,
                name="identify_fopdt_from_step",
                description=identify_fopdt_from_step.__doc__,
                takes_ctx=False),

            # analysis
            Tool(find_inflection_point,
                name="find_inflection_point",
                description=find_inflection_point.__doc__,
                takes_ctx=False),
            Tool(find_characteristic_points,
                name="find_characteristic_points",
                description=find_characteristic_points.__doc__,
                takes_ctx=False),
            Tool(find_peaks,
                name="find_peaks",
                description=find_peaks.__doc__,
                takes_ctx=False),
            Tool(find_settling_time,
                name="find_settling_time",
                description=find_settling_time.__doc__,
                takes_ctx=False),
]

def add_tools(agent: Agent, tools: list[Tool[Any]]) -> Agent:
    for tool in tools:
        agent.tool(tool) #type: ignore
    return agent

def supply_agent(agent: Agent):
    tools = get_tools()
    add_tools(agent, tools)
    return agent

def create_agent(
    model: Model | KnownModelName | str = get_default_model(),
    max_retries: int = 1,
):
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
    fmi_agent = Agent(
        model=model,
        instructions=SYS_PROMPT,
        name="FMIAgent",
        tools=get_tools(),
        retries=max_retries,
    )
    
    return fmi_agent
