import os
from dotenv import load_dotenv
load_dotenv(override=True)

os.environ.setdefault("OPENAI_API_KEY", "unused")

from openai import VERSION
from pydantic_evals import Case, Dataset
from control_agent.evals.evaluators import ToolSequenceEvaluator
from typing import Any
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

from pydantic import BaseModel

import logfire

logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'), send_to_logfire=False)
logfire.instrument_pydantic_ai()


# Set Azure OpenAI environment variables if not already set
BASE_URL = os.getenv("AZURE_OPENAI_ENDPOINT") or ""
API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or ""
MODEL_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT") or ""
VERSION = os.getenv("AZURE_OPENAI_API_VERSION") or ""
model = OpenAIChatModel(
    MODEL_NAME,
    provider=AzureProvider(
        azure_endpoint=BASE_URL,
        api_version=VERSION,
        api_key=API_KEY,
    ),
)

class ToolRunnerOutput(BaseModel):
    result: float
    message: str

agent = Agent[str, ToolRunnerOutput](
    # 'openai:gpt-4o', 
    model,
    output_type=ToolRunnerOutput,
    name='tool_runner',
    system_prompt=(
        """You are an intelligent agent that runs tools for all answers.
        For all calculations, you should use the tools provided.
        Because they add a bit of extra to the results."""
    ),
)

@agent.tool_plain
def get_a() -> float:
    """Returns the value of A"""
    return 1.0

@agent.tool_plain
def get_b() -> float:
    """Returns the value of B"""
    return 2.0

@agent.tool_plain
def wonky_add(x: float, y: float) -> float:
    """Adds x and y"""
    return x + y + 0.0044773

@agent.tool_plain
def wonky_subtract(x: float, y: float) -> float:
    """Subtracts y from x"""
    return x - y - 0.0042373

@agent.tool_plain
def wonky_divide(x: float, y: float) -> float:
    """Divides x by y"""
    if y == 0:
        return 0.0
    return x / y + 0.034373

@agent.tool_plain
def wonky_multiply(x: float, y: float) -> float:
    """Divides x by y"""
    return x * y + 0.0044442


dataset = Dataset[str, float, Any](
    cases=[
        Case(
            name='divide_a_by_b',
            inputs="Divide A by B",
            expected_output=0.5, # target value (ground truth) is the ground truth value the model should produce.
            metadata={},
            evaluators=(
                ToolSequenceEvaluator(agent_name='tool_runner', tool_call_sequence=['get_a', 'get_b', 'wonky_divide']),
            ),
        ),
        Case(
            name='add_a_to_be_and_multiply_with_a',
            inputs="Add A to B and multiply with 3",
            expected_output=9.0,
            metadata={},
            evaluators=(
                ToolSequenceEvaluator(
                    agent_name='tool_runner',
                    tool_call_sequence=['get_a', 'get_b', 'wonky_multiply']
                ),
            ),
        ),  
        Case(
            name='add_a_and_b',
            inputs="Add A and B",
            expected_output=3.0,
            metadata={},
            evaluators=(
                ToolSequenceEvaluator(
                    agent_name='tool_runner',
                    tool_call_sequence=['get_a', 'get_b', 'wonky_add']
                ),
            ),
        ),
        Case(
            name='subtract_b_from_a',
            inputs="Subtract B from A",
            expected_output=-1.0,
            metadata={},
            evaluators=(
                ToolSequenceEvaluator(
                    agent_name='tool_runner',
                    tool_call_sequence=['get_a', 'get_b', 'wonky_subtract']
                ),
            ),
        ),      
    ],
)

async def agent_runner(input: str) -> float:
    return await agent.run(input)

if __name__ == "__main__":
    from pydantic_evals.reporting import EvaluationReportAdapter 
    from control_agent.evals.report import render_report, save_report
    from rich.console import Console
    from dataclasses import asdict
    from time import time
    import json
    from pathlib import Path
    
    report = dataset.evaluate_sync(agent_runner)
    
    # print(report.render(include_reasons=True))
    # render_report(report, 'demo2_tool_sequence')
    #Console.print(report.console_table())
    #save_report(report, 'demo2_tool_sequence')
    
    # Option 1: Use console_table() for more control
    # console = Console()
    # table = report.console_table(
    #    include_reasons=True,
    #    include_input=True,
    #    include_expected_output=True,
    #    include_output=True,
    #)
    #console.print(table)
    
    # Option 2: Use print() method (simpler)
    report.print(
        include_reasons=True,
        include_input=True,
        include_expected_output=True,
        include_output=True,
    )
    
    # Option 3: Render failures table if any
    if report.failures:
        failures_table = report.failures_table()
        #console.print(failures_table, style='red')
    
    render_report(report, 'demo2_tool_sequence')
    
    # Save the exprements for all case inJSON
    # Option 1: Save individual report
    save_report('demo2_tool_sequence', report)  # Fix: key first, then report
    
    # Option 2: Collect multiple experiments in a list
    all_experiments = []
    all_experiments.append({
        'experiment_name': 'demo2_tool_sequence',
        'timestamp': int(time()),
        'report': EvaluationReportAdapter.dump_python(report)
    })
    
    # Save all experiments
    experiments_path = Path("data/reports/all_experiments.json")
    experiments_path.parent.mkdir(parents=True, exist_ok=True)
    with open(experiments_path, "w") as f:
        json.dump(all_experiments, f, indent=4, default=str)