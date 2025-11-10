from pydantic_ai import Agent
from control_agent.evals.experiments.demo.world import world

agent_name  = "world_explorer"
# Agent configuration
agent: Agent = Agent(
    'openai:gpt-4o',
    output_type=str,
    name=agent_name,
    system_prompt=(
        'You are an intelligent agent that interacts with the world using available tools '
        'to achieve your goals. Use the tools systematically to explore and discover information.'
    ),
    retries=20
)


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





def answer_question(question: str) -> str:
    result = agent.run_sync(question)
    return result.output