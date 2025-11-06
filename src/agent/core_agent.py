"""Core agent implementation using OpenAI Agents SDK."""

import asyncio
import os
from pathlib import Path
from typing import Optional

from agents import (
    Agent,
    ModelSettings,
    Runner,
    function_tool,
    set_default_openai_client,
    set_default_openai_api,
    set_tracing_disabled,
)

from openai import AsyncAzureOpenAI, AsyncOpenAI

from .tools_wrapper import ALL_TOOLS

from dotenv import load_dotenv
# Load environment variables
load_dotenv(override=True)


# System instructions for the FMI agent
SYSTEM_INSTRUCTIONS = """
You are an expert control systems engineer specializing FMI simulation.

You have access to tools for simulation to use.
"""


def create_fmi_agent(
    model: str = "gpt-5",
    name: str = "FMI Control Engineer",
) -> Agent:
    """
    Create an FMI agent instance using OpenAI Agents SDK.
    
    Args:
        model: OpenAI model name (default: "gpt-5") WOULD NOT WORK for AZURE use "AZURE_OPENAI_DEPLOYMENT"
        name: Agent name (default: "FMI Control Engineer")
    
    Returns:
        Agent instance configured with FMI simulation tools
    
    Example:
        >>> agent = create_fmi_agent()
        >>> result = Runner.run_sync(agent, "Calculate ZN tuning for K=2.0, T=1.5, L=0.5")
    """
    # Verify API key is set
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_version = os.getenv("AZURE_OPENAI_API_VERSION")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    # Configure based on provider
    if azure_key and azure_endpoint:
        # Use deployment from env var if available, otherwise use model parameter
        deployment_name = deployment if deployment else model
        
        # Azure OpenAI - set environment variables for SDK auto-detection
        # The SDK will automatically use these to configure AzureOpenAI client
        os.environ["OPENAI_API_KEY"] = azure_key
        os.environ["AZURE_OPENAI_ENDPOINT"] = azure_endpoint  
        os.environ["OPENAI_API_VERSION"] = azure_version
        os.environ["AZURE_OPENAI_DEPLOYMENT"] = deployment_name
        

        # Ensure the Agents SDK uses the Azure client instead of the public API
        set_default_openai_client(
            AsyncAzureOpenAI(
                api_key=azure_key,
                azure_endpoint=azure_endpoint,
                api_version=azure_version,
            ),
            use_for_tracing=False,
        )
        set_default_openai_api("chat_completions")
        set_tracing_disabled(True)
        
        # Create agent - SDK will detect Azure from env vars
        agent = Agent(
            name=name,
            instructions=SYSTEM_INSTRUCTIONS,
            tools=ALL_TOOLS,
            model=deployment_name,  # Use the actual Azure deployment name
        )
    else:
        raise ValueError(
            "API key not found. Set OPENAI_API_KEY (for OpenAI) or "
            "AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT (for Azure OpenAI)."
        )
    
    return agent


