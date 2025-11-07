"""Simple test script to verify the FMI agent works."""

import asyncio
import os
from dotenv import load_dotenv
from control_agent.agent.agent import create_agent
# import logfire
from control_toolbox.config import set_fmu_dir
from control_agent.experiment_definitions.definitions import experiment_definitions
from pathlib import Path
import logfire

load_dotenv()

logfire.configure()                 # read .logfire/ or env vars (token, project)
logfire.instrument_pydantic_ai() 

logfire.info("run test.py", project="fmu-agent")

set_fmu_dir(Path(__file__).parents[2] / "models" / "fmus")

experiment_definitions.model_name = "PI_FOPDT_2"
query = experiment_definitions.construct_query("open_loop_step")

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

