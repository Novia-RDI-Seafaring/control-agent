"""Simple test script to verify the FMI agent works."""

import asyncio
import os
from dotenv import load_dotenv
from agent.core import create_agent
import logfire

load_dotenv()

logfire.configure()                 # read .logfire/ or env vars (token, project)
logfire.instrument_pydantic_ai() 

logfire.info("run test.py", project="fmu-agent")

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
    
    # Test query - you can change this to any query
    # query = "What simulation models do you have available?"
    # query = "Simualte PI_FOPDT with a step input change"
    # query = "Simualte a step response and analyse the results. Simulate on time interval [0, 30], do the step at t=1 seconds. Analyze the results. Set mode=1."
    # query = "Simulate a closed-loop (mode=1) step response on the time interval [0, 60] seconds, where the input changes from 0 to 1 at t=1 seconds. Record results with 1 second intervals. Analyze the results. Use step_size=0.1s."
    #query = "Simualte from 0 to 60 seconds a step response, where the input (setpoint) changes from 0 to 1 at t=1 seconds. Set mode=1 and tune parameters K_p and T_i, which are the controller gain and integration time constant, respectively, to give approximately 10 percent overshoot. Explain in your result what methods you used to tune the controller. Also return the response of the system with the tuned controller. Record results with 1 second intervals."
    # query = "Tune the PI controller with Lambda tuning based on experiments for balanced response."
    # query = "generate a step signal from 0 to 2 at t=2 seconds with a sampling time of 0.1 seconds over the time intnerval [0, 10]. Return the pydantic models of both the argument you passed to the tool and the response, without modifications."
    #query = (
    #    "Simulate a step response from 0 to 1 at t=2 seconds in the time interval [0, 10].",
    #    "Use sampling time 0.1 seconds. Set controller to manual mode (mode=0).",
    #    "Return step response at 1 second time intervals."
    #)
    # query = "Perform an experiment on the model PI_FOPDT_2 to identify a first order system with time delay using a step experiment ontime interval [0, 30]. Set mode=0 (manual) during the experiment. Analyse the results. Return the identified parameters K, T, L aswell as explenations how they were identified."
    # query = "Explain step by step how you could approximate a FOPDT system from a step response by identifying parameters K, T, L. Do you have access to tools to help you with this? Explain what values from analyse_step_response are useful for this"
    # query = "List available models and their model descriptions."

    queries = {
        "model_description": "List available models and their model descriptions.",
        "open_loop_step": "Simulate an open-loop step response with input change from 0 to 1.",
        "closed_loop_step": "Simulate a closed-loop step response with input change from 0 to 1",
        "system_identification": "Make a step response and identify the static gain K, time constant T , and dead time L of a FOPDT model",
        "lambda_tuning": "Tune the PI controller using λ-tuning (for a FOPDT model) for a balanced response.",
        "z_n": "Perform experiments to tune the PI controller using Ziegler-Nichols closed-loop method. Report the tuned controller parameters Kp, Ti and other intermediate parameters in response.",
        "tuning_overshoot": "Tune the PI controller to have approximately 10 percentage overshoot",
    }

    query = queries["tuning_overshoot"]

    print(f"\n2. Running query: '{query}'")
    print("   Waiting for response...\n")
    # breakpoint()
    try:
        logfire.info(f"Execute query: {query}", project="fmu-agent")
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

