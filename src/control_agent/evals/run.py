from __future__ import annotations

import os
from typing import Any, Optional, Type, Callable, Coroutine
from pathlib import Path
from rich.console import Console
from pydantic_evals.reporting import EvaluationReport, ReportCase
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



def get_normal_agent_runner(output_model: Type[OutputDataT]) -> Callable[[str], Coroutine[Any, Any, OutputDataT]]:
    agent = create_agent(
        model=get_default_model(),
        tools=get_tools(),
        deps=TypedStore.__class__,
        output_type=output_model,
    )
    def runner(input: str) -> OutputDataT:
        result = agent.run_sync(input, output_type=output_model, deps=TypedStore()) # type: ignore
        return result.output # type: ignore
    return runner # type: ignore

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

def print_report(report: EvaluationReport, title: str, note:str|None = None) -> None:
    console = Console()
    console.print(f"\n{'='*80}")
    console.print(f"Experiment: {title}")
    console.print(f"{'='*80}")
    if note:
        console.print(f"Note: {note}")
    

    for case in report.cases:
        console.print(f"\nCase: {case.name}")
        console.print(f"\n\tInputs: {case.inputs}")
        console.print(f"\tAssertions: ", end=" ")
        for name, assertion in case.assertions.items():
            console.print(f"✅" if assertion.value else "🚫", end=" ")
        console.print(f"\n")
        console.print(f"\tDuration: {case.task_duration:.2f}s")
        console.print(f"\tTotal duration: {case.total_duration:.2f}s")
        console.print(f"\tMetrics:")
        for name, metric in case.metrics.items():
            console.print(f"\t\t{name}: {metric:.2f}")
        from devtools import debug

        console.print(f"\n\tAssertion Details:")
        if case.expected_output:
            console.print(f"\tExpected Output: {case.expected_output}")
        if case.output:
            console.print(f"\tOutput: {case.output}")
        console.print(f"\tEvaluators:")
        for name, assertion in case.assertions.items():
            if not assertion.value:
                console.print(f"\t\t[red]✗ {name}[/red]", end=", ")
            else:
                console.print(f"\t\t[green]✓ {name}[/green]", end=", ")
            console.print(f"- {assertion.reason}")
        console.print(f"\n")


def run_experiment(name: str, ctx_tools: bool = False, save: bool = False) -> None:
    try:
        console = Console()
        report2 = None
        if name == "demo":
            from control_agent.evals.experiments.demo import agent_runner as runner, dataset as dataset # type: ignore
            report = dataset.evaluate_sync(runner) # type: ignore
            print_report(report, "Demo", "This is a demo experiment")
            if save:
                save_report("get_fmu_names_exp", report)

        else:
            dataset, OutputDataT = datasets[name] # type: ignore
            if not ctx_tools:
                runner = get_normal_agent_runner(OutputDataT) # type: ignore
                note = f"Data is passed to tools via context window"
                _key = f"{name}_data_in_context_window"

            else:
                runner = get_agent_runner(OutputDataT) # type: ignore
                note = f"Tools have access to data via stored model"
                _key = f"{name}_data_in_stored_model"

            report = dataset.evaluate_sync(runner) # type: ignore
            #console.print(f"[debug] Report has {len(report.cases)} cases, {len(report.failures) if hasattr(report, 'failures') else 0} failures")
            print_report(report, name, note)
            # Save the report
            if save:
                save_report(_key, report)
            else:
                console.print(f"[dim]Note: Report not saved. Use --save flag to save the report.[/dim]")
        
    except Exception as e:
        console.print(f"\n[red]ERROR in experiment '{name}':[/red]")
        console.print(f"[red]{type(e).__name__}: {e}[/red]")
        raise

@app.command()
def evaluate(experiment: str="all", fmu_dir: Path=Path("models/fmus"), ctx_tools: bool  = False, save: bool = False):
    set_fmu_dir(fmu_dir)
    
    if experiment == "all":
       for experiment in preferred_order + [k for k in datasets.keys() if k not in preferred_order]:
            run_experiment(experiment, ctx_tools, save)
    else:
        run_experiment(experiment, ctx_tools, save)




if __name__ == "__main__":
    app()

