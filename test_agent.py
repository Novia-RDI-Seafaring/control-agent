"""Simple test script to verify agent responds to 'hello'."""

import asyncio
import sys
from pathlib import Path

# Add src to path if needed
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents import Runner
from agent.core_agent import create_fmi_agent


def test_hello():
    """Test agent response to 'hello'."""
    print("Creating FMI agent...")
    agent = create_fmi_agent()
    
    print(f"\nAgent config: ", agent)
    
    print("\nSending 'hello' to agent...")
    print("User: prompt\n")
    
    result = Runner.run_sync(agent, input="List all FMU models in the directory, list only the tools and nothing else", max_turns=15)
    
    print(f"\nAgent: {result.final_output}\n")
    
    # messages = result.to_input_list()
    # iterations = len([m for m in messages if m.get("role") == "assistant"])
    
    print("="*50)
    print("RESULT:")
    print("="*50)
    #print(f"Response: {result.final_output}")
    #print(f"Iterations: {iterations}")
    print("="*50)
    
    return result


async def test_hello_async():
    """Test agent response to 'hello' (async version)."""
    print("Creating FMI agent...")
    agent = create_fmi_agent()
    
    print(f"\nAgent config: ", agent)
    
    print("\nSending 'hello' to agent (async)...")
    print("User: hello\n")
    
    result = await Runner.run(agent, input="hello", max_turns=15)
    
    print(f"\nAgent: {result.final_output}\n")
    
    messages = result.to_input_list()
    iterations = len([m for m in messages if m.get("role") == "assistant"])
    
    print("="*50)
    print("RESULT:")
    print("="*50)
    print(f"Response: {result.final_output}")
    print(f"Iterations: {iterations}")
    print("="*50)
    
    return result


if __name__ == "__main__":
    # Test synchronous version
    test_hello()
    
    # Uncomment to test async version
    # asyncio.run(test_hello_async())

