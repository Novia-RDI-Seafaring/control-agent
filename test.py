"""Simple test script to verify the FMI agent works."""
from pathlib import Path
import asyncio
import os
from dotenv import load_dotenv
from control_agent.agent.agent import create_agent
from control_agent.experiment_definitions.definitions import experiment_definitions
# import logfire

from rich.console import Console
from rich.table import Table

load_dotenv()

from control_toolbox.config import *
fmu_path = (Path(__file__).resolve().parent / "models" / "fmus").resolve()
set_fmu_dir(fmu_path)

# logging
# logfire.configure()                 # read .logfire/ or env vars (token, project)
# logfire.instrument_pydantic_ai() 

# logfire.info("run test.py", project="fmu-agent")

########################
# SET EXPERIMENT
########################
# Experiments:
# - list_model_names
# - model_description
# - list_iop
# - get_metadata
# - open_loop_step
# - closed_loop_step
# - system_identification
# - ultimate_gain
# - lambda_tuning
# - z_n
experiment_definitions.model_name = "PI_FOPDT_2"
query = experiment_definitions.construct_query("open_loop_step")

async def main():
    """Test the FMI agent."""
    console = Console()
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
        
        # Display result
        table = Table(title="Agent Response")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Output", str(result.output))
        usage = result.usage()
        table.add_row("Total Tokens", str(usage.total_tokens))
        table.add_row("Request Count", str(usage.requests))
        
        console.print(table)
        
        # print("="*80)
        # print("RESPONSE:")
        # print("="*80)
        # print(result.output)
        # print("\n")
        
        # Show tool usage
        # print("="*80)
        # print("USAGE:")
        # print("="*80)
        # usage = result.usage()
        # print(f"  Total tokens: {usage.total_tokens}")
        # print(f"  Request count: {usage.requests}")
        
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

