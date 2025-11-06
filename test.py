"""Simple test script to verify the FMI agent works."""

import asyncio
import os
from dotenv import load_dotenv
from agent.agent import create_agent
# import logfire

load_dotenv()

# logfire.configure()                 # read .logfire/ or env vars (token, project)
# logfire.instrument_pydantic_ai() 

# logfire.info("run test.py", project="fmu-agent")

async def main():
    """Test the FMI agent."""
    
    print("="*80)
    print("FMI Agent Test")
    print("="*80)
    
    # Create agent
    print("\n1. Creating agent...")
    agent = create_agent(max_retries=3)
    print("Agent created successfully")
    print(agent)
    
    queries = {
        "model_description": "List available models and their model descriptions.",
        "open_loop_step": "Simulate an open-loop step response with input change from 0 to 1.",
        "closed_loop_step": "Simulate a closed-loop step response with input change from 0 to 1",
        "system_identification": "Make a step response and identify the static gain K, time constant T, and dead time L of a FOPDT model",
        "lambda_tuning": "Tune the PI controller using λ-tuning for a balanced response.",
        "z_n": "Perform experiments to tune the PI controller using Ziegler-Nichols closed-loop method. Report the tuned controller parameters Kp, Ti and other intermediate parameters in response.",
        "tuning_overshoot": "Tune the PI controller to have approximately 10 percentage overshoot and rise time less than 2 seconds.",
    }

    query = queries["open_loop_step"]

    print(f"\n2. Running query: '{query}'")
    print("   Waiting for response...\n")
    # breakpoint()
    try:
        # logfire.info(f"Execute query: {query}", project="fmu-agent")
        result = await agent.run(query)
        
        print("="*80)
        print("RESPONSE:")
        print("="*80)
        print(result.output)
        print("\n")
        
        # Show tool usage
        print("="*80)
        print("USAGE:")
        print("="*80)
        usage = result.usage()
        print(f"  Total tokens: {usage.total_tokens}")
        print(f"  Request count: {usage.requests}")
        
        print("\n")
        print("="*80)
        print("TEST: PASSED ✓")
        print("="*80)
        
    except Exception as e:
        print("="*80)
        print("ERROR:")
        print("="*80)
        print(f"{type(e).__name__}: {e}")
        print("\n")
        print("="*80)
        print("TEST: FAILED ✗")
        print("="*80)
        raise

if __name__ == "__main__":
    asyncio.run(main())

