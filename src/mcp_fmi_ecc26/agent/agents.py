from pydantic_ai import Agent
from .tools  import SimlationToolResponse, simulate_fmu as simulate_fmu_fn
from typing import Optional
import os

def create_simuation_agent(model:Optional[str]=None):
    return Agent(
        model=model,
        system_prompt="You are a helpful assistant that provides concise responses. always use tools if you can",
        tools=[simulate_fmu_fn]
    )

simulation_agent = create_simuation_agent(os.getenv("SIMULATION_MODEL", "gpt-4o-mini"))
