from pydantic_ai import Agent, ModelMessage
from .tools  import simulate_fmu_tool, annotate_simulation_tool, load_result_tool
from typing import Optional
import os

def create_simuation_agent(model:Optional[str]=None):
    return Agent(
        model=model,
        system_prompt="You are a helpful assistant that provides concise responses. always use tools if you can",
        tools=[simulate_fmu_tool, annotate_simulation_tool, load_result_tool],
        retries=20
    )

simulation_agent = create_simuation_agent(os.getenv("SIMULATION_MODEL", "gpt-4o-mini"))
from typing import Dict, List

history: Dict[str, List[ModelMessage]] = {}
async def ask(message:str, session_id:Optional[str]=None, model:Optional[str]=None):
    global history
    messages: List[ModelMessage] = history.setdefault(session_id, []) if session_id is not None else []
    response = await simulation_agent.run(message, message_history=messages)
    history[session_id].extend(response.all_messages()) if session_id is not None else []
    return response.response.text

def get_history(session_id:Optional[str]=None):
    global history
    return history.get(session_id, []) if session_id is not None else []