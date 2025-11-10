"""Simple test script to verify the FMI agent works."""
from pathlib import Path
import asyncio
import os
from dotenv import load_dotenv
from control_agent.agent.agent import create_agent
from control_agent.evals.report import render_report, save_report
from control_agent.experiment_definitions.definitions import experiment_definitions
from pydantic_evals import Case, Dataset
from typing import Any

load_dotenv()

from control_toolbox.config import *
fmu_path = (Path(__file__).resolve().parent / "models" / "fmus").resolve()
set_fmu_dir(fmu_path)

experiment_definitions.model_name = "PI_FOPDT_2"
query = experiment_definitions.construct_query("open_loop_step")

async def agent_runner(input: str) -> Any:
    """Run the agent with the given input."""
    agent = create_agent(max_retries=3)
    result = await agent.run(input)
    return result.output

async def main():
    """Test the FMI agent using evaluation framework."""
    
    print("="*80)
    print("FMI Agent Test - All Experiments")
    print("="*80)
    
    # Get all registered query names
    query_names = experiment_definitions.get_query_names()
    print(f"\nFound {len(query_names)} experiments: {', '.join(query_names)}\n")
    
    # Create cases for all registered queries
    cases = []
    i = 0
    for query_name in query_names:
        query = experiment_definitions.construct_query(query_name)
        response_model = experiment_definitions.get_response_schema(query_name)
        cases.append(
            Case[str, response_model, Any](
                name=query_name,
                inputs=query,
                expected_output=None,  # No expected yet output for simple test
                metadata={
                    "model_name": experiment_definitions.model_name,
                    "query_name": query_name,
                },
            )
        )
    
    
    # Create dataset with all cases
    dataset = Dataset[str, Any, Any](cases=cases)
    
    print(f"Running {len(cases)} test cases...")
    print("   Waiting for response...\n")
    
    try:
        # Use await instead of evaluate_sync to avoid event loop issues
        report = await dataset.evaluate(agent_runner)
        
        # Use report functions
        render_report(report, 'test_all_experiments')
        save_report('test_all_experiments', report)
        
        # Also print Rich table
        from rich.console import Console
        console = Console()
        table = report.console_table(
            include_reasons=True,
            include_input=False,  # Query is too long, hide it
            include_expected_output=False,
            include_output=True,
        )
        console.print(table)
        
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