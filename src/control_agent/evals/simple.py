from __future__ import annotations

import os
from typing import Any, Optional
import json
import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent
from pathlib import Path
from pydantic_evals.reporting import EvaluationReport
import time
# Load environment variables
load_dotenv()
from typing import Literal
# Configure logging and instrumentation
logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'), send_to_logfire=False)
logfire.instrument_pydantic_ai()
logfire.instrument_openai()

from control_agent.agent.tools import simulate_fmu_tool, annotate_simulation_tool, load_result_tool
import os


models = ["gpt-4o-mini", "gpt-4o", "gpt-5", "gpt-3.5-turbo"]

def run_simulation() -> str:
    """Run the simulation tool on the FMU named PI_FOPDT.fmu"""
    return simulate_fmu_tool("PI_FOPDT.fmu")

#from control_agent.sys import FOPDT, ControllerPI

Method = Literal["zn", "lam"]
## output_type=ControllerPI,
## input_type=FOPDT,
##
#id_tuning_agent = Agent[ControllerPI, FOPDT](
class SomeInput(BaseModel):
    input: str

step_changer = Agent[SomeInput, SomeInput](
        model="gpt-4o-mini",
       
        system_prompt="You are a helpful assistant that provides concise responses. always use tools if you can",
        tools=[run_simulation],
        retries=20
    )


async def agent_runner(question: str) -> str:
    result = await simulation_agent.run(question)
    return result.output

from typer import Typer

app = Typer()

@app.command()
def evaluate(experiment: Optional[str] = None):
    from control_agent.evals.datasets import all as datasets
    """Evaluate the agent on all datasets"""
    for key, dataset in datasets.items():
        if experiment and key != experiment: continue
        
        report = dataset.evaluate_sync(agent_runner)
        path = Path("data/reports")
        path.mkdir(parents=True, exist_ok=True) 
        from dataclasses import asdict, is_dataclass

        
        report_dict = asdict(report)
        with open(path / f"{key}-{time.time()}.json", "w") as f:
            json.dump(report_dict, f, indent=4, default=str)
        print(report)
        print(f"Wrote {key} report to {path / f'{key}.json'}")
        
if __name__ == "__main__":
    app()

