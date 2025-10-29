from __future__ import annotations

import os, json, logfire, time
from typing import Any, Optional, Literal, Dict, Any
from dotenv import load_dotenv
from pydantic_ai import Agent
from pathlib import Path
from pydantic_evals.reporting import EvaluationReport

# Load environment variables
load_dotenv()

# Configure logging and instrumentation
logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'), send_to_logfire=False)
logfire.instrument_pydantic_ai()
logfire.instrument_openai()

from agent.core import create_agent
from mcp_fmi_ecc26.evals.report import render_report, save_report

models = ["gpt-4o-mini", "gpt-4o", "gpt-5", "gpt-3.5-turbo"]

async def agent_runner(question: str) -> str:
    fmi_agent = create_agent(model="gpt-4o-mini", model_name="fmi_agent")
    result = await fmi_agent.run(question)
    return result.output

from typer import Typer

app = Typer()

@app.command()
def evaluate(experiment: Optional[str] = None):
    from mcp_fmi_ecc26.evals.datasets import all as datasets
    """Evaluate the agent on all datasets"""
    for key, dataset in datasets.items():
        if experiment and key != experiment: continue
        
        report = dataset.evaluate_sync(agent_runner)
        render_report(report, key)

        
if __name__ == "__main__":
    app()

