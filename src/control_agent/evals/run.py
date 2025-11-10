from __future__ import annotations

import os, json, logfire, time
from typing import Any, Optional, Literal, Dict, Any, Tuple
from dotenv import load_dotenv
from pydantic_ai import Agent
from pathlib import Path
from pydantic_evals.reporting import EvaluationReport
from pydantic_evals import Case, Dataset
from control_agent.agent.agent import (AgentDepsT, OutputDataT, create_agent)
# Load environment variables
load_dotenv()
from rich.console import Console

# Configure logging and instrumentation
logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'), send_to_logfire=False)
logfire.instrument_pydantic_ai()

from control_agent.evals.report import render_report, save_report
from control_agent.evals.common import get_agent_runner

from typer import Typer
app = Typer()

all_experiments = {}
import importlib
from control_agent.evals.experiments import __all__ as experiments
for experiment in experiments:
    module = importlib.import_module(f"control_agent.evals.experiments.{experiment}")
    dataset = module.dataset
    OutputDataT = module.OutputDataT
    name = dataset.name
    agent_runner = module.get_agent_runner(OutputDataT)
    all_experiments[name] = (dataset, agent_runner)
    
def run_experiment(name: str) -> None:
    try:
        console = Console()
        if name == "demo":
            from control_agent.evals.experiments.demo import agent_runner as runner, dataset as dataset # type: ignore

        else:
            dataset = all_experiments[name][0]
            runner = all_experiments[name][1]

        report = dataset.evaluate_sync(runner)
        
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
def evaluate(experiment: str="all", fmu_dir: Optional[Path]=Path("models/fmus")):
    from control_agent.evals.experiments import __all__ as experiments
    if fmu_dir is not None:
        from control_toolbox.config import set_fmu_dir
        set_fmu_dir(fmu_dir)
    if experiment == "all":
        for name in experiments:
            run_experiment(name)
    else:
        run_experiment(experiment)




if __name__ == "__main__":
    app()

