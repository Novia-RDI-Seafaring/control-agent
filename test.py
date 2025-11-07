"""Simple test script to verify the FMI agent works."""

import asyncio

import os
from dotenv import load_dotenv
from agent.agent import create_agent

from agent.prompts.response_schema import (
    get_json_schema,
    ListModelNamesResponse,
    ListIOPResponse,
    GetMetadataResponse,
    StepResponse,
    SystemIdentificationResponse,
    LambdaTuningResponse,
    UltimateGainResponse
)
# import logfire
load_dotenv()

# logfire.configure()                 # read .logfire/ or env vars (token, project)
# logfire.instrument_pydantic_ai() 

# logfire.info("run test.py", project="fmu-agent")

MODEL_NAME = "PI_FOPDT_2"
QUERY_NAME = "ultimate_gain"

queries = {
    "list_model_names": "List available FMU models.",
    "list_iop": f"List the inputs, outputs, and parameters of the model {MODEL_NAME}.",
    "get_metadata": f"Get THE metadata for the model {MODEL_NAME}.",
    "open_loop_step": f"Simulate an open-loop step response for model {MODEL_NAME} with input change from 0 to 1.",
    "closed_loop_step": f"Simulate a closed-loop step response for model {MODEL_NAME} with input change from 0 to 1",
    "system_identification": f"Make a step response for model {MODEL_NAME} and identify the static gain (K), time constant (T), and dead time (L).",
    "ultimate_gain": f"Perform closed-loop experimentes on the model {MODEL_NAME} to determine the ultimate gain (Ku) and ultimate period (Pu).",
    "lambda_tuning": f"Tune the PI controller of model {MODEL_NAME} using λ-tuning for a balanced response.",
    "z_n": f"Tune the PI controller of model {MODEL_NAME} using Ziegler-Nichols closed-loop method.",
    "tuning_overshoot": f"Tune the PI controller of model {MODEL_NAME} to have approximately 10 percentage overshoot and rise time less than 2 seconds.",
}

response_schema = {
    "list_model_names": get_json_schema(ListModelNamesResponse),
    "list_iop": get_json_schema(ListIOPResponse),
    "get_metadata": get_json_schema(GetMetadataResponse),
    "open_loop_step": get_json_schema(StepResponse),
    "closed_loop_step": get_json_schema(StepResponse),
    "system_identification": get_json_schema(SystemIdentificationResponse),
    "lambda_tuning": get_json_schema(LambdaTuningResponse),
    "ultimate_gain": get_json_schema(UltimateGainResponse),
}

query = f"""
QUERY: {queries[QUERY_NAME]}
RESPONSE SCHEMA: {response_schema[QUERY_NAME]}
"""

async def main():
    """Test the FMI agent."""
    
    print("="*80)
    print("FMI Agent Test")
    print("="*80)
    
    # Create agent
    print("\n1. Creating agent...")
    agent = create_agent(max_retries=3)
    print("Agent created successfully")
    print(agent)

    print(f"\n2. Running query: '{query}'")
    print("   Waiting for response...\n")
    # breakpoint()
    try:
        # logfire.info(f"Execute query: {query}", project="fmu-agent")
        result = await agent.run(query)
        
        print("="*80)
        print("RESPONSE:")
        print("="*80)
        print(result.output)
        print("\n")
        
        # Show tool usage
        print("="*80)
        print("USAGE:")
        print("="*80)
        usage = result.usage()
        print(f"  Total tokens: {usage.total_tokens}")
        print(f"  Request count: {usage.requests}")
        
        print("\n")
        print("="*80)
        print("TEST: PASSED ✓")
        print("="*80)
        
    except Exception as e:
        print("="*80)
        print("ERROR:")
        print("="*80)
        print(f"{type(e).__name__}: {e}")
        print("\n")
        print("="*80)
        print("TEST: FAILED ✗")
        print("="*80)
        raise

if __name__ == "__main__":
    asyncio.run(main())

