from __future__ import annotations

import os, json, logfire, time
from typing import Any, Optional, Literal, Dict, Any, Tuple
from dotenv import load_dotenv
from pydantic_ai import Agent
from pathlib import Path
from pydantic_evals.reporting import EvaluationReport
from pydantic_evals import Case, Dataset
from agent.agent import (AgentDepsT, OutputDataT, create_agent)
# Load environment variables
load_dotenv()

# Configure logging and instrumentation
logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'), send_to_logfire=False)
logfire.instrument_pydantic_ai()
logfire.instrument_openai()

from evals.report import render_report, save_report
from evals.dataset_types import dataset_types


from typer import Typer

app = Typer()


@app.command()
def evaluate(experiment: Optional[str] = None):
    from evals.experiments import all as experiments
    """Evaluate the agent on all datasets"""
    for key, (dataset, agent) in experiments.items():
        if experiment and key != experiment: continue
       
        async def agent_runner(experiment_input): # type: ignore
            result = await agent.run(experiment_input)
            return result.output

        report = dataset.evaluate_sync(agent_runner)
        render_report(report, key)

        
if __name__ == "__main__":
    app()

