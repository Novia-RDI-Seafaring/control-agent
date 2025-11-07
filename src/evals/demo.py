"""
Demo evaluation agent for testing agent tool usage and reasoning capabilities.

This module demonstrates how to create a simple interactive world simulation
where an AI agent must use tools to navigate and discover information.
The evaluation tests whether the agent can correctly sequence tool calls
to achieve complex goals.
"""

from __future__ import annotations

import os
from typing import Any

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Contains, IsInstance, LLMJudge
from pydantic_ai_examples.evals.custom_evaluators import AgentCalledTool

# Load environment variables
load_dotenv()

# Configure logging and instrumentation
logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'), send_to_logfire=False)
logfire.instrument_pydantic_ai()
logfire.instrument_openai()


# Constants
SECRET_NUMBER = 42
MESSAGE_ON_THE_FRIDGE = "Remember to buy some more milk."

# Global world instance for agent tools
world: World | None = None

# Agent configuration
agent: Agent = Agent(
    'openai:gpt-4o',
    output_type=str,
    name='world_explorer',
    system_prompt=(
        'You are an intelligent agent that interacts with the world using available tools '
        'to achieve your goals. Use the tools systematically to explore and discover information.'
    ),
    retries=20
)

class World:
    """
    A simple interactive world simulation for agent evaluation.
    
    This class simulates a house environment where an agent must navigate through
    various states to discover information. The agent must:
    1. Find the secret code under the doormat
    2. Unlock and open the door
    3. Enter the house and turn on the light
    4. Navigate to the kitchen
    5. Read the message on the fridge
    
    The simulation tests the agent's ability to sequence actions correctly
    and handle state-dependent operations.
    """

    def __init__(self, secret_number: int, message_on_the_fridge: str) -> None:
        """
        Initialize the world simulation.
        
        Args:
            secret_number: The code needed to unlock the door
            message_on_the_fridge: The message that will be revealed on the fridge
        """
        self._secret_number = secret_number
        self._message_on_the_fridge = message_on_the_fridge

        # Initialize world state
        self.door_locked: bool = True
        self.door_open: bool = False
        self.is_inside: bool = False
        self.light_on: bool = False
        self.in_kitchen: bool = False


    def look_under_the_doormat(self) -> str:
        """
        Look under the doormat to find the secret code.
        
        Returns:
            str: Description of what was found or an error message
        """
        if not self.is_inside:
            return f"You look under the doormat and see a number written on it. The number is {self._secret_number}."
        return "You can't look under the doormat from inside the house."

    def unlock_door(self, code: int) -> str:
        """
        Attempt to unlock the door with the provided code.
        
        Args:
            code: The numeric code to unlock the door
            
        Returns:
            str: Result of the unlock attempt
        """
        if not self.door_locked:
            return "The door is already unlocked."
        if code == self._secret_number:
            self.door_locked = False
            return "You unlocked the door."
        return "The code is incorrect."

    def lock_door(self) -> str:
        """
        Lock the door and close it if it's open.
        
        Returns:
            str: Result of the lock attempt
        """
        if self.door_locked:
            return "The door is already locked."
        self.door_locked = True
        self.door_open = False
        return "You locked the door."

    def open_door(self) -> str:
        """
        Open the door if it's unlocked.
        
        Returns:
            str: Result of the open attempt
        """
        if self.door_locked:
            return "The door is locked."
        if self.door_open:
            return "The door is already open."
        self.door_open = True
        return "You opened the door."

    def close_door(self) -> str:
        """
        Close the door if it's open.
        
        Returns:
            str: Result of the close attempt
        """
        if not self.door_open:
            return "The door is already closed."
        self.door_open = False
        return "You closed the door."

    def go_inside(self) -> str:
        """
        Enter the house through the open door.
        
        Returns:
            str: Result of the entry attempt
        """
        if self.is_inside:
            return "You are already inside the house."
        if not self.door_open:
            return "The door is closed."
        self.is_inside = True
        return "You went inside the house."

    def go_outside(self) -> str:
        """
        Exit the house and reset indoor states.
        
        Returns:
            str: Result of the exit attempt
        """
        if not self.is_inside:
            return "You are already outside."
        self.is_inside = False
        self.in_kitchen = False
        self.light_on = False
        return "You went outside the house."

    def turn_on_light(self) -> str:
        """
        Turn on the indoor light.
        
        Returns:
            str: Result of the light operation
        """
        if not self.is_inside:
            return "You are outside, there are no lights here."
        if self.light_on:
            return "The light is already on."
        self.light_on = True
        return "You turned on the light."

    def turn_off_light(self) -> str:
        """
        Turn off the indoor light.
        
        Returns:
            str: Result of the light operation
        """
        if not self.is_inside:
            return "You are outside, there are no lights here."
        if not self.light_on:
            return "The light is already off."
        self.light_on = False
        return "You turned off the light."

    def go_to_kitchen(self) -> str:
        """
        Navigate to the kitchen from inside the house.
        
        Returns:
            str: Result of the navigation attempt
        """
        if not self.is_inside:
            return "You are outside, there is no kitchen here."
        if not self.light_on:
            return "It's too dark to see where you're going."
        if self.in_kitchen:
            return "You are already in the kitchen."
        self.in_kitchen = True
        return "You went to the kitchen."

    def read_fridge_message(self) -> str:
        """
        Read the message on the fridge in the kitchen.
        
        Returns:
            str: The fridge message or an error if conditions aren't met
        """
        if not self.in_kitchen:
            return "You need to be in the kitchen to read the fridge."
        if not self.light_on:
            return "It's too dark to read the message."
        return f'The message on the fridge says: "{self._message_on_the_fridge}"'

    # --- Developer and debugging tools ---
    def get_secret_number(self) -> int:
        """
        Get the secret number for debugging or testing purposes.
        
        Returns:
            int: The secret number used to unlock the door
        """
        return self._secret_number

    def describe_state(self) -> str:
        """
        Get a summary of the current world state for debugging.
        
        Returns:
            str: A formatted description of all world state variables
        """
        return (
            f"Door locked: {self.door_locked}\n"
            f"Door open: {self.door_open}\n"
            f"Inside: {self.is_inside}\n"
            f"Light on: {self.light_on}\n"
            f"In kitchen: {self.in_kitchen}"
        )


# Agent tool definitions
# These tools allow the agent to interact with the world simulation

@agent.tool_plain(
    name="look_under_the_doormat", 
    description="Look under the doormat to find the secret code needed to unlock the door."
)
def look_under_the_doormat() -> str:
    """Look under the doormat to discover the secret code."""
    global world
    if world is None:
        return "World not initialized."
    return world.look_under_the_doormat()

@agent.tool_plain(
    name="unlock_door", 
    description="Unlock the door using the secret code found under the doormat."
)
def unlock_door(code: int) -> str:
    """Unlock the door with the provided numeric code."""
    global world
    if world is None:
        return "World not initialized."
    return world.unlock_door(code)

@agent.tool_plain(
    name="lock_door", 
    description="Lock the door and close it if it's currently open."
)
def lock_door() -> str:
    """Lock the door and close it."""
    global world
    if world is None:
        return "World not initialized."
    return world.lock_door()

@agent.tool_plain(
    name="open_door", 
    description="Open the door if it's unlocked."
)
def open_door() -> str:
    """Open the door if it's unlocked."""
    global world
    if world is None:
        return "World not initialized."
    return world.open_door()

@agent.tool_plain(
    name="close_door", 
    description="Close the door if it's currently open."
)
def close_door() -> str:
    """Close the door if it's open."""
    global world
    if world is None:
        return "World not initialized."
    return world.close_door()

@agent.tool_plain(
    name="go_inside", 
    description="Enter the house through the open door."
)
def go_inside() -> str:
    """Go inside the house through the open door."""
    global world
    if world is None:
        return "World not initialized."
    return world.go_inside()

@agent.tool_plain(
    name="go_outside", 
    description="Exit the house and return to the outside."
)
def go_outside() -> str:
    """Go outside the house."""
    global world
    if world is None:
        return "World not initialized."
    return world.go_outside()

@agent.tool_plain(
    name="turn_on_light", 
    description="Turn on the indoor light to illuminate the house."
)
def turn_on_light() -> str:
    """Turn on the indoor light."""
    global world
    if world is None:
        return "World not initialized."
    return world.turn_on_light()

@agent.tool_plain(
    name="turn_off_light", 
    description="Turn off the indoor light."
)
def turn_off_light() -> str:
    """Turn off the indoor light."""
    global world
    if world is None:
        return "World not initialized."
    return world.turn_off_light()

@agent.tool_plain(
    name="go_to_kitchen", 
    description="Navigate to the kitchen from inside the house. Requires the light to be on."
)
def go_to_kitchen() -> str:
    """Go to the kitchen from inside the house."""
    global world
    if world is None:
        return "World not initialized."
    return world.go_to_kitchen()

@agent.tool_plain(
    name="read_message_on_the_fridge", 
    description="Read the message displayed on the fridge in the kitchen."
)
def read_message_on_the_fridge() -> str:
    """Read the message on the fridge."""
    global world
    if world is None:
        return "World not initialized."
    return world.read_fridge_message()


async def answer_question(question: str) -> str:
    """
    Process a question using the agent and return the response.
    
    Args:
        question: The question to ask the agent
        
    Returns:
        str: The agent's response
    """
    result = await agent.run(question)
    return result.output



# Evaluation dataset for testing agent capabilities
explore_world_dataset = Dataset["str", "str", Any](
    cases=[
        Case(
            name='discover_secret_code',
            inputs="What is the code to unlock the door?",
            metadata={
                'focus': 'tool_discovery_and_correct_answer',
                'description': 'Tests if agent can discover and use the look_under_the_doormat tool'
            },
            evaluators=(
                IsInstance(type_name='str'),
                Contains(value=str(SECRET_NUMBER), case_sensitive=False),
                LLMJudge(
                    rubric=f'The agent should discover that the correct code is {SECRET_NUMBER}.',
                    include_input=True,
                    model='openai:gpt-4o',
                ),
                AgentCalledTool(agent_name='world_explorer', tool_name='look_under_the_doormat'),
            ),
        ),
        
        Case(
            name='complete_kitchen_mission',
            inputs="What is the message on the fridge?",
            metadata={
                'focus': 'sequential_tool_usage',
                'description': 'Tests if agent can sequence multiple tools correctly to achieve complex goal'
            },
            evaluators=(
                IsInstance(type_name='str'),
                Contains(value="milk", case_sensitive=False),
                LLMJudge(
                    rubric=f'The agent should find the message: "{MESSAGE_ON_THE_FRIDGE}".',
                    include_input=True,
                    model='openai:gpt-4o',
                ),
                # Required tool sequence for success
                AgentCalledTool(agent_name='world_explorer', tool_name='look_under_the_doormat'),
                AgentCalledTool(agent_name='world_explorer', tool_name='unlock_door'),
                AgentCalledTool(agent_name='world_explorer', tool_name='open_door'),
                AgentCalledTool(agent_name='world_explorer', tool_name='go_inside'),
                AgentCalledTool(agent_name='world_explorer', tool_name='turn_on_light'),
                AgentCalledTool(agent_name='world_explorer', tool_name='go_to_kitchen'),
                AgentCalledTool(agent_name='world_explorer', tool_name='read_message_on_the_fridge'),
            ),
        ),
        
        Case(
            name='planning_and_sequencing',
            inputs="List the steps needed to read the message on the fridge.",
            expected_output="look_under_the_doormat, unlock_door, open_door, go_inside, turn_on_light, go_to_kitchen, read_message_on_the_fridge",
            metadata={
                'focus': 'planning_ability',
                'description': 'Tests if agent can plan the correct sequence of actions'
            },
        ),
    ],
    evaluators=[
        LLMJudge(
            rubric='The agent should demonstrate correct tool usage and provide accurate answers.',
            include_input=True,
            model='openai:gpt-4o',
        ),
    ],
)


def initialize_world() -> None:
    """Initialize the global world instance for the agent tools."""
    global world
    world = World(
        secret_number=SECRET_NUMBER, 
        message_on_the_fridge=MESSAGE_ON_THE_FRIDGE
    )


def run_demo() -> None:
    """
    Run the evaluation demo.
    
    This function initializes the world, runs the evaluation dataset,
    and prints the results.
    """
    print("🚀 Starting Agent Evaluation Demo")
    print("=" * 50)
    
    # Initialize the world simulation
    initialize_world()
    print("✅ World simulation initialized")
    
    # Run the evaluation
    print("🔄 Running evaluation dataset...")
    try:
        report = explore_world_dataset.evaluate_sync(answer_question)
        print("\n📊 Evaluation Results:")
        print("=" * 50)
        print(report)
        print("\n✅ Demo completed successfully!")
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        raise


def run_manual_test() -> None:
    """
    Run a manual test of the world simulation.
    
    This demonstrates the expected sequence of actions
    to successfully read the fridge message.
    """
    print("🧪 Running Manual Test")
    print("=" * 30)
    
    test_world = World(
        secret_number=SECRET_NUMBER, 
        message_on_the_fridge=MESSAGE_ON_THE_FRIDGE
    )
    
    # Demonstrate the correct sequence
    print("Testing incorrect code:")
    print(f"  {test_world.unlock_door(11)}")
    
    print("\nTesting correct sequence:")
    print(f"  {test_world.unlock_door(SECRET_NUMBER)}")
    print(f"  {test_world.open_door()}")
    print(f"  {test_world.go_inside()}")
    print(f"  {test_world.turn_on_light()}")
    print(f"  {test_world.go_to_kitchen()}")
    print(f"  {test_world.read_fridge_message()}")
    
    print(f"\nFinal state:\n{test_world.describe_state()}")


if __name__ == "__main__":
    # Run the evaluation demo
    run_demo()
    
    print("\n" + "=" * 50)
    
    # Optionally run manual test for demonstration
    run_manual_test()