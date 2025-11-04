import os
from typing import List, Optional, Union
from dotenv import load_dotenv

from openai import AsyncClient
from pydantic_ai.models.openai import OpenAIChatModel, Model
from pydantic_ai import Agent, Tool
from pydantic_ai.providers.azure import AzureProvider
from httpx import AsyncClient

from agent.prompts import SYS_PROMPT
from agent.tools.fmi_tools import (
    get_all_model_descriptions,
    get_model_description,
    get_fmu_names,
    simulate_tool,
    generate_step_tool,
    analyse_step_response,
    zn_pid_tuning
)
# Load environment variables
load_dotenv()

# System prompt with tuning method documentation
SYSTEM_PROMPT = SYS_PROMPT

def get_tools() -> List[Tool]:
    return [
        Tool(get_all_model_descriptions,
            name="get_all_model_descriptions",
            description=get_all_model_descriptions.__doc__,
            takes_ctx=False),
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
            max_retries=3, 
            takes_ctx=False),
        Tool(zn_pid_tuning,
            name="zn_pid_tuning",
            description=zn_pid_tuning.__doc__,
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

def get_azure_model(name: str) -> OpenAIChatModel:
    CLIENT = AsyncClient()
    # Get Azure OpenAI configuration
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = name or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    return OpenAIChatModel(
        deployment,
        provider=AzureProvider(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            http_client=CLIENT,
        )
    )


def create_agent(
    model_name: Optional[str] = None,
    temperature: float = 0.0,
    verbose: bool = False,
    max_iterations: int = 20,
    model: Optional[Union[Model,str]]=None,
    tools: Optional[List[Tool]] = None,
    agent_name:str = "FMIAgent"
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
    if model is None: model = get_azure_model(model_name or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"))
    if tools is None: tools = get_tools()
    
    # Create agent with tools
    return Agent(
        model=model,
        instructions=SYS_PROMPT,
        tools=tools,
        retries=max_iterations
    )
