"""Simple test script to verify the FMI agent works."""
from pathlib import Path
import asyncio
from dotenv import load_dotenv
from control_agent.agent.agent import create_agent
from control_agent.experiment_definitions.definitions import experiment_definitions
from control_agent.evals.report import save_report
from pydantic_evals import Case, Dataset
from typing import Any
from rich.console import Console

load_dotenv()

from control_toolbox.config import *
fmu_path = (Path(__file__).resolve().parent / "models" / "fmus").resolve()
set_fmu_dir(fmu_path)

experiment_definitions.model_name = "PI_FOPDT_2"

async def agent_runner(input: str, output_schema: Any) -> Any:
    """Run the agent with the given input and output schema."""
    agent = create_agent(max_retries=5, output_type=output_schema)
    try:
        # Add timeout to prevent hanging
        result = await asyncio.wait_for(agent.run(input), timeout=600) 
        return result.output
    except asyncio.TimeoutError:
        raise TimeoutError("Agent execution timed out after 5 minutes")


async def main():
    """Test the FMI agent using evaluation framework."""
    query_names = experiment_definitions.get_query_names()
    console = Console()
    
    # Run all experiments, each with its own response schema
    for name in [query_names[5]]:
        console.print(f"\n[yellow]Starting experiment: {name}[/yellow]")
        query = experiment_definitions.construct_query(name)
        response_model = experiment_definitions.get_response_schema(name)
        
        case = Case[str, response_model, Any](
            name=name,
            inputs=query,
            expected_output=None,
            metadata={
                "model_name": experiment_definitions.model_name,
                "query_name": name,
            },
        )
        
        dataset = Dataset[str, response_model, Any](cases=[case])
        
        # Create task function with correct schema for this experiment
        schema = response_model
        async def task_for_experiment(input: str) -> response_model:  # type: ignore
            """Task function that uses the correct output_schema for this experiment."""
            return await agent_runner(input=input, output_schema=schema)
        
        try:
            console.print(f"[yellow]Evaluating experiment: {name}...[/yellow]")
            report = await dataset.evaluate(task_for_experiment, task_name=name, progress=True)
            console.print(f"[green]Evaluation completed for: {name}[/green]")
            
            console.print(f"\n{'='*80}")
            console.print(f"Experiment: {name}")
            console.print(f"{'='*80}")
            
            if report.failures:
                console.print(f"\n[red]Failures: {len(report.failures)}[/red]")
                for failure in report.failures:
                    console.print(f"\n[red]✗ {failure.name}[/red]")
                    console.print(f"  [yellow]Error:[/yellow] {failure.error_message}")
            
            table = report.console_table(
                include_reasons=True,
                include_input=False,
                include_expected_output=False,
                include_output=True,
            )
            console.print("\n")
            console.print(table)
            
            # Save the report
            save_report(name, report)
            
        except Exception as e:
            console.print(f"\n[red]ERROR in experiment '{name}':[/red]")
            console.print(f"[red]{type(e).__name__}: {e}[/red]")
            raise

if __name__ == "__main__":
    asyncio.run(main())