"""Core agent configuration and initialization."""

import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.tools import BaseTool, tool
from langchain.agents import create_agent as langchain_create_agent

from agent.prompts import SYS_PROMPT
from agent.prompts.sim_prompt import SIM_PROMPT
from agent.tools import (
    get_fmu_info_tool,
    simulate_fmu_tool,
    create_step_signal_tool,
    identify_fopdt_tool,
    calculate_metrics_tool,
    set_fmu_parameters_tool,
)

# Load environment variables
load_dotenv()

# System prompt with tuning method documentation
SYSTEM_PROMPT = SYS_PROMPT

# add this tool (anywhere top-level)
@tool("finish", return_direct=True)
def finish(text: str) -> str:
    """Use this to end the task. Input must be the final answer in Markdown."""
    return text


def create_agent(
    model_name: Optional[str] = None,
    temperature: float = 0.0,
    verbose: bool = True,
    max_iterations: int = 20,
):
    """Create and configure the FMI agent using LangGraph.
    
    Args:
        model_name: Azure OpenAI deployment name (default from env)
        temperature: LLM temperature (default: 0.0 for deterministic)
        verbose: Enable verbose logging (default: True)
        max_iterations: Maximum agent iterations (default: 20)
        
    Returns:
        Configured LangGraph agent ready to run.
    """
    # Get Azure OpenAI configuration
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = model_name or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    
    if not endpoint or not api_key:
        raise ValueError(
            "Azure OpenAI credentials not found. "
            "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in environment or .env file."
        )
    
    # Initialize LLM
    # Note: temperature parameter may not be supported by all Azure OpenAI deployments
    llm = AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        azure_deployment=deployment,
        api_version=api_version,
    )
    
    # Define tools
    tools: List[BaseTool] = [
        get_fmu_info_tool,
        simulate_fmu_tool,
        create_step_signal_tool,
        identify_fopdt_tool,
        calculate_metrics_tool,
        set_fmu_parameters_tool,
        finish,
    ]
    
    # Create agent using official LangChain 1.0 API
    agent_executor = langchain_create_agent(
        llm,
        tools,
        system_prompt=SYSTEM_PROMPT
    )
    
    return agent_executor
