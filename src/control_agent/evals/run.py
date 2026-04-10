from __future__ import annotations
from control_agent.agent.common import *
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
#logfire.instrument_openai()


from control_agent.agent.agent import OutputDataT, create_agent
from control_agent.agent.tools_ctx import get_tools as get_tools_ctx
from control_agent.agent.tools import get_tools
from control_agent.agent.model import get_default_model
from control_agent.evals.report import save_report
from control_agent.evals.export_results import export_results_to_csv
from control_agent.evals.experiments import datasets # type: ignore
from control_toolbox.config import set_fmu_dir
from pydantic_ai.ag_ui import StateDeps
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
        output_type=output_model,
        max_retries=20,
    )
    def runner(input: str) -> OutputDataT:
        result = agent.run_sync(input, output_type=output_model) # type: ignore
        return result.output # type: ignore
    return runner # type: ignore


from control_agent.agent.tools_ctx import DepsType, SimContext
def get_agent_runner(output_model: Type[OutputDataT], results_keeper: Dict[str, AgentRunResult[OutputDataT]], ctx_keeper: Dict[str, SimContext]) -> Callable[[str], Coroutine[Any, Any, AgentRunResult[OutputDataT]]]:
    console = Console()
    from pydantic import BaseModel
    class Resp(BaseModel):
        message: str
        output: OutputDataT

    agent = create_agent(
        model=get_default_model(),
        tools=get_tools_ctx(),
        deps=DepsType,
        output_type=output_model,
        max_retries=20,

    )
    def runner(input: str) -> Resp:
        try:
            sim_context = SimContext(fmu_folder=str(Path("models/fmus")), notes=[])
            sim_context.current_fmu = "PI_FOPDT_2"
            ctx_keeper[input] = sim_context
            
            result = agent.run_sync(input, output_type=output_model, deps=StateDeps(sim_context)) # type: ignore
            results_keeper[input] = result
        except Exception as e:
            #console.print(f"[red]ERROR in agent runner: {e}[/red]")
            raise
        return result # type: ignore
    return runner # type: ignore

def print_report(report: EvaluationReport, title: str, note:str|None = None, results_keeper: Dict[str, AgentRunResult[Any]] = {}, ctx_keeper: Dict[str, SimContext] = {}) -> None:
    console = Console()

    for name, sim_state in ctx_keeper.items():
        console.print(f"\nContext for {name}:")
        console.print(f"\tCurrent FMU: {sim_state.current_fmu}")
        try:
            fmu = sim_state.fmu
        except Exception as e:
            pass
    for name, result in results_keeper.items():
        console.print(f"\nResult for {name}:")
        console.print(f"\t{result}")
        for message  in result.all_messages():
            for part in message.parts:
                
                if isinstance(part, UserPromptPart):
                    console.print(f"\t\tUser: {part.content}")
                if isinstance(part, ToolCallPart) and part.tool_name != "final_result":
                    console.print(f"\t\t\tTool call: {part.tool_name}")
                    """import json
                    for key, value in json.loads(part.args).items():
                        console.print(f"\t\t\t{key}={value},")
                    console.print(f"\t\t)", end="")"""
                if isinstance(part, ToolReturnPart) and part.tool_name == "final_result":
                    console.print(f"\t\tAgent: {part.content}")

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



        console.print(f"\tEvaluators:")
        for name, assertion in case.assertions.items():
            if not assertion.value:
                console.print(f"\t\t[red]✗ {name}[/red]", end=", ")
            else:
                console.print(f"\t\t[green]✓ {name}[/green]", end=", ")
            console.print(f"- {assertion.reason}")
        console.print(f"\n")

        """if case.output:
            if hasattr(case.output, 'message'):
                console.print(f"\nMessage:")
                console.print(case.output.message)
            if hasattr(case.output, 'output'):
                console.print(f"\t\tOutput:\n")
                console.print(case.output.output)"""
    

    

    
from typing import Dict
results: Dict[str, Any] = {}

def run_experiment(name: str, ctx_tools: bool = False, save: bool = False) -> None:
    try:
        console = Console()
        
        if name == "demo":
            from control_agent.evals.experiments.demo import agent_runner as runner, dataset as dataset # type: ignore
            report = dataset.evaluate_sync(runner, retries=20) # type: ignore
            print_report(report, "Demo", "This is a demo experiment")

        else:
            dataset, OutputDataT = datasets[name] # type: ignore
            # Debug: Print evaluators immediately after getting from dict
            if dataset.cases:
                evaluator_names = [type(e).__name__ for e in dataset.cases[0].evaluators]
                console.print(f"[yellow][DEBUG] Evaluators immediately after datasets[{name}]: {evaluator_names}[/yellow]")
            results_keeper: Dict[str, Any] = {}
            ctx_keeper: Dict[str, Any] = {}
            if not ctx_tools:
                runner = get_normal_agent_runner(OutputDataT) # type: ignore
                note = f"Data is passed to tools via context window"
                _key = f"{name}_data_in_context_window"

            else:
                runner = get_agent_runner(OutputDataT, results_keeper, ctx_keeper) # type: ignore
                note = f"Tools have access to data via stored model"
                _key = f"{name}_data_in_stored_model"

            # Debug: Print evaluator info BEFORE evaluation
            if dataset.cases:
                evaluator_names = [type(e).__name__ for e in dataset.cases[0].evaluators]
                evaluator_types = [type(e) for e in dataset.cases[0].evaluators]
                console.print(f"[yellow][DEBUG] Evaluators in dataset BEFORE eval: {evaluator_names}[/yellow]")
                console.print(f"[yellow][DEBUG] Evaluator types: {evaluator_types}[/yellow]")
                console.print(f"[yellow][DEBUG] Evaluator count: {len(dataset.cases[0].evaluators)}[/yellow]")
            
            report = dataset.evaluate_sync(runner) # type: ignore
            #console.print(f"[debug] Report has {len(report.cases)} cases, {len(report.failures) if hasattr(report, 'failures') else 0} failures")
            # Debug: Print evaluator info AFTER evaluation
            if report.cases:
                case = report.cases[0]
                assertion_names = list(case.assertions.keys())
                console.print(f"[yellow][DEBUG] Assertions in report AFTER eval: {assertion_names}[/yellow]")
            print_report(report, name, note, results_keeper, ctx_keeper)
            # Save the report
            if save:
                save_report(_key, report)
                # Export to CSV and pickle for analysis
                csv_path, pickle_path = export_results_to_csv(report, name, results_keeper)
                console.print(f"[green]Results exported to CSV: {csv_path}[/green]")
                console.print(f"[green]Results exported to pickle: {pickle_path}[/green]")
            else:
                console.print(f"[dim]Note: Report not saved. Use --save flag to save the report.[/dim]")
        
    except Exception as e:
        console.print(f"\n[red]ERROR in experiment '{name}':[/red]")
        console.print(f"[red]{type(e).__name__}: {e}[/red]")
        raise

@app.command()
def evaluate(experiment: str="all", ctx_tools: bool  = False, save: bool = False, fmu_dir: Path=Path("models/fmus"), skip_eval: bool = False):
    set_fmu_dir(fmu_dir)
    if skip_eval:
        runner = get_agent_runner(str)
        dataset, OutputDataT = datasets[experiment] # type: ignore
        cases = dataset.cases
        for case in cases:
            query = case.inputs
            result = runner(query)
            print(result)
        
    else:

            
        if experiment == "all":
            experiment_names = preferred_order + [k for k in datasets.keys() if k not in preferred_order]
            for exp_name in experiment_names:
                run_experiment(exp_name, ctx_tools, save)
            
            # If saving, also create a combined DataFrame with all experiments
            if save:
                from control_agent.evals.export_results import combine_all_experiments
                combine_all_experiments()
        elif "," in experiment:
            # Multiple experiments specified as comma-separated list
            experiment_names = [name.strip() for name in experiment.split(",")]
            for exp_name in experiment_names:
                if exp_name in datasets:
                    run_experiment(exp_name, ctx_tools, save)
                else:
                    print(f"Warning: Experiment '{exp_name}' not found. Skipping.")
            
            # If saving, combine the specified experiments
            if save:
                from control_agent.evals.export_results import combine_all_experiments
                combine_all_experiments()
        else:
            run_experiment(experiment, ctx_tools, save)





if __name__ == "__main__":
    app()

