import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

from openai import AsyncClient
from pydantic_ai import Agent, RunContext, AgentRunResultEvent, AgentStreamEvent, agent, Tool
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider
from httpx import AsyncClient

from agent.prompts import SYS_PROMPT
from agent.tools.fmi_tools import (
    get_model_description,
    get_fmu_names,
    simulate_tool,
    generate_step_tool,
    analyse_step_response
)
from agent.tools.functions.schema import DataModel, SimulationModel

# Load environment variables
load_dotenv()

# System prompt with tuning method documentation
SYSTEM_PROMPT = SYS_PROMPT

def create_agent(
    model_name: Optional[str] = None,
    temperature: float = 0.0,
    verbose: bool = False,
    max_iterations: int = 20,
):
    """Create FMI agent with tools.
    
    Args:
        model_name: Azure OpenAI deployment name
        temperature: LLM temperature
        verbose: Enable verbose logging
        max_iterations: Maximum iterations (not used by pydantic_ai directly)
        
    Returns:
        Configured pydantic_ai Agent
    """
    # Get Azure OpenAI configuration
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = model_name or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    
    CLIENT = AsyncClient()
    MODEL = OpenAIChatModel(
        deployment,
        provider=AzureProvider(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            http_client=CLIENT,
        )
    )
    
    TOOLS = [
        #Tool(get_all_model_descriptions,
        #    name="get_all_model_descriptions",
        #    description=get_all_model_descriptions.__doc__,
        #    takes_ctx=False),
        Tool(get_model_description,
            name="get_model_description",
            description=get_model_description.__doc__,
            takes_ctx=False),
        Tool(get_fmu_names,
            name="get_fmu_names",
            description=get_fmu_names.__doc__,
            takes_ctx=False),
        Tool(simulate_tool,
            name="simulate_fmu",  # expose the desired tool name
            description=simulate_tool.__doc__,
            takes_ctx=False),
        Tool(generate_step_tool,
            name="generate_step",
            description=generate_step_tool.__doc__,
            takes_ctx=False),
        Tool(analyse_step_response,
            name="analyse_step_response",
            description=analyse_step_response.__doc__,
            takes_ctx=False),
        #Tool(create_signal_tool,
        #    name="create_signal",
        #    description=create_signal_tool.__doc__,
        #    takes_ctx=False),
        #Tool(merge_signals_tool,
        #    name="merge_signals",
        #    description=merge_signals_tool.__doc__,
        #    takes_ctx=False),
    ]
    
    # Create agent with tools
    fmi_agent = Agent(
        model=MODEL,
        instructions=SYS_PROMPT,
        name="FMIAgent",
        tools=TOOLS,
    )
    
    return fmi_agent