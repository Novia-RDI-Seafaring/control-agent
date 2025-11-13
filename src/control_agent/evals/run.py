from __future__ import annotations
from control_agent.agent.common import *
import os
from typing import Any, Optional, Type, Callable, Coroutine
from pathlib import Path
from rich.console import Console
from rich.text import Text
from pydantic_evals.reporting import EvaluationReport, ReportCase
from dotenv import load_dotenv
load_dotenv(override=True)

import logfire
logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'), send_to_logfire=False)
logfire.instrument_pydantic_ai()
#logfire.instrument_openai()


from control_agent.agent.agent import OutputDataT, create_agent
from control_agent.agent.tools_ctx import get_tools as get_tools_ctx
from control_agent.agent.model import get_default_model
from control_agent.evals.report import save_report
from control_agent.evals.experiments import datasets # type: ignore
from control_agent.evals.planning import plan_experiment, plan_all_experiments, ExperimentPlan
from control_agent.evals.plan_executor import get_plan_executor_runner, execute_plan, PlanExecutionResult
from control_toolbox.config import set_fmu_dir
from pydantic_ai.ag_ui import StateDeps
from typer import Typer
app = Typer()
console = Console()

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

def run_experiment(name: str, ctx_tools: bool = False, save: bool = False, use_planning: bool = False) -> None:
    try:
        console = Console()
        
        if name == "demo":
            from control_agent.evals.experiments.demo import agent_runner as runner, dataset as dataset # type: ignore
            report = dataset.evaluate_sync(runner, retries=20) # type: ignore
            print_report(report, "Demo", "This is a demo experiment")

        else:
            dataset, OutputDataT = datasets[name] # type: ignore
            results_keeper: Dict[str, Any] = {}
            ctx_keeper: Dict[str, Any] = {}
            
            if use_planning:
                # Planning mode: create plan first, then execute
                console.print(f"\n[cyan]Planning experiment: {name}[/cyan]")
                plan = plan_experiment(name)
                
                console.print(f"\n[green]Execution Plan for {name}:[/green]")
                console.print(f"  Input Query: {plan.input_query}")
                console.print(f"  Tool Sequence:")
                for i, tool in enumerate(plan.tool_sequence, 1):
                    req_marker = "[REQUIRED]" if tool.is_required else "[OPTIONAL]"
                    console.print(f"    {i}. {tool.tool_name} {req_marker}")
                    console.print(f"       Description: {tool.description}")
                    if tool.motivation:
                        console.print(f"       [dim]Why: {tool.motivation}[/dim]")
                if plan.notes:
                    console.print(f"  Notes:")
                    for note in plan.notes:
                        console.print(f"    - {note}")
                
                # Create plan-guided runner
                runner = get_plan_executor_runner(plan, OutputDataT, results_keeper, ctx_keeper) # type: ignore
                note = f"Plan-guided execution (Tools have access to data via stored model)"
                _key = f"{name}_planned_execution"
            elif not ctx_tools:
                runner = get_normal_agent_runner(OutputDataT) # type: ignore
                note = f"Data is passed to tools via context window"
                _key = f"{name}_data_in_context_window"
            else:
                runner = get_agent_runner(OutputDataT, results_keeper, ctx_keeper) # type: ignore
                note = f"Tools have access to data via stored model"
                _key = f"{name}_data_in_stored_model"

            report = dataset.evaluate_sync(runner) # type: ignore
            #console.print(f"[debug] Report has {len(report.cases)} cases, {len(report.failures) if hasattr(report, 'failures') else 0} failures")
            print_report(report, name, note, results_keeper, ctx_keeper)
            
            # If planning was used, show plan execution verification
            if use_planning:
                plan = plan_experiment(name)
                for case in report.cases:
                    if case.name in results_keeper:
                        result = results_keeper[case.name]
                        from control_agent.evals.plan_executor import extract_executed_tools, verify_plan_execution
                        executed_tools = extract_executed_tools(result)
                        verification = verify_plan_execution(plan, executed_tools)
                        console.print(f"\n[cyan]Plan Execution Verification:[/cyan]")
                        console.print(f"  Executed tools: {', '.join(verification.executed_tools)}")
                        if verification.skipped_tools:
                            console.print(f"  Skipped optional tools: {', '.join(verification.skipped_tools)}")
                        if verification.errors:
                            console.print(f"  [red]Errors: {', '.join(verification.errors)}[/red]")
                        else:
                            console.print(f"  [green]✓ Plan executed successfully[/green]")
            
            # Save the report
            if save:
                save_report(_key, report)
            else:
                console.print(f"[dim]Note: Report not saved. Use --save flag to save the report.[/dim]")
        
    except Exception as e:
        console.print(f"\n[red]ERROR in experiment '{name}':[/red]")
        # Safely print exception without Rich markup interpretation
        # Handle cases where exception message might contain binary data
        try:
            error_msg = str(e)
            # Check if message contains binary data (non-printable characters)
            if any(ord(c) < 32 and c not in '\n\r\t' for c in error_msg[:100]):
                error_msg = repr(error_msg)
        except Exception:
            error_msg = repr(e)
        
        error_text = Text()
        error_text.append(f"{type(e).__name__}: ", style="red")
        error_text.append(error_msg, style="red")
        console.print(error_text)
        raise

@app.command()
def evaluate(
    experiment: str="all", 
    ctx_tools: bool = False, 
    save: bool = False, 
    fmu_dir: Path=Path("models/fmus"), 
    skip_eval: bool = False,
    use_planning: bool = False
):
    """
    Run evaluation experiments.
    
    Args:
        experiment: Experiment name or "all" to run all experiments
        ctx_tools: Use context-aware tools (stored model)
        save: Save evaluation reports
        fmu_dir: Directory containing FMU files
        skip_eval: Skip evaluation framework, just run agent
        use_planning: Use planning agent to create execution plan first (rule-based, extracts from evaluators)
    """
    set_fmu_dir(fmu_dir)
    
    if use_planning and experiment == "all":
        # Plan all experiments first
        console.print("\n[cyan]Planning all experiments...[/cyan]")
        experiment_list = preferred_order + [k for k in datasets.keys() if k not in preferred_order]
        plans = plan_all_experiments(experiment_list)
        console.print(f"\n[green]Created plans for {len(plans)} experiments[/green]")
    
    if skip_eval:
        runner = get_agent_runner(str, {}, {}) # type: ignore
        dataset, OutputDataT = datasets[experiment] # type: ignore
        cases = dataset.cases
        for case in cases:
            query = case.inputs
            result = runner(query)
            print(result)
        
    else:
        if experiment == "all":
            for exp_name in preferred_order + [k for k in datasets.keys() if k not in preferred_order]:
                run_experiment(exp_name, ctx_tools, save, use_planning)
        else:
            run_experiment(experiment, ctx_tools, save, use_planning)





if __name__ == "__main__":
    app()

