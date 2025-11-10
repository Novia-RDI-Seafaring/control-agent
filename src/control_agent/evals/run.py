from __future__ import annotations

import os
from typing import Any, Optional, Type, Callable, Coroutine
from pathlib import Path
from rich.console import Console

from dotenv import load_dotenv
load_dotenv(override=True)

import logfire
logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'), send_to_logfire=False)
logfire.instrument_pydantic_ai()
from control_agent.agent.stored_model import TypedStore
from control_agent.agent.agent import get_tools, OutputDataT, create_agent
from control_agent.agent.tools_ctx import get_tools as get_tools_ctx
from control_agent.agent.model import get_default_model
from control_agent.evals.report import save_report
from control_agent.evals.experiments import datasets # type: ignore
from control_toolbox.config import set_fmu_dir

from typer import Typer
app = Typer()

preferred_order = [
    "list_model_names",
    "list_iop",  # Note: dataset name is "list_iop", not "list_io"
    "get_metadata",
    "model_description",
    "open_loop_step",
    "closed_loop_step",
    "system_identification",
    "ultimate_gain",
    "lambda_tuning",
    "z_n",
    "tuning_overshoot",
]


def get_agent_runner(output_model: Type[OutputDataT]) -> Callable[[str], Coroutine[Any, Any, OutputDataT]]:
    agent = create_agent(
        model=get_default_model(),
        tools=get_tools_ctx(),
        deps=TypedStore.__class__,
        output_type=output_model,
    )
    def runner(input: str) -> OutputDataT:
        result = agent.run_sync(input, output_type=output_model, deps=TypedStore()) # type: ignore
        return result.output # type: ignore
    return runner # type: ignore


def run_experiment(name: str) -> None:
    try:
        console = Console()
        if name == "demo":
            from control_agent.evals.experiments.demo import agent_runner as runner, dataset as dataset # type: ignore

        else:
            dataset, OutputDataT = datasets[name] # type: ignore
            runner = get_agent_runner(OutputDataT) # type: ignore
            
        report = dataset.evaluate_sync(runner) # type: ignore
        
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

@app.command()
def evaluate(experiment: str="all", fmu_dir: Path=Path("models/fmus")):
    set_fmu_dir(fmu_dir)
    if experiment == "all":
       for experiment in preferred_order + [k for k in datasets.keys() if k not in preferred_order]:
            run_experiment(experiment)
    else:
        run_experiment(experiment)




if __name__ == "__main__":
    app()

