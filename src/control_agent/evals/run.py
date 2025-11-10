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

# Configure logging and instrumentation
logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'), send_to_logfire=False)
logfire.instrument_pydantic_ai()
logfire.instrument_openai()

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
    
@app.command()
def evaluate(experiment: str="all"):
    from control_agent.evals.experiments import __all__ as experiments
    dataset = all_experiments[experiment][0]
    agent_runner = all_experiments[experiment][1]
    report = dataset.evaluate_sync(agent_runner)

    print(report)


if __name__ == "__main__":
    app()

