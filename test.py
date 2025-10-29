"""Simple test script to verify the FMI agent works."""

import asyncio
import os
from dotenv import load_dotenv
from agent.core import create_agent

load_dotenv()

async def main():
    """Test the FMI agent."""
    
    print("="*80)
    print("FMI Agent Test")
    print("="*80)
    
    # Create agent
    print("\n1. Creating agent...")
    agent = create_agent()
    print("Agent created successfully")
    print(agent)
    
    # Test query - you can change this to any query
    # query = "What simulation models do you have available?"
    query = "Simulate an open-loop step response with input change from 0 to 1"
    # query = "Tune the PI controller with Lambda tuning for balanced response"
    
    print(f"\n2. Running query: '{query}'")
    print("   Waiting for response...\n")
    # breakpoint()
    try:
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

