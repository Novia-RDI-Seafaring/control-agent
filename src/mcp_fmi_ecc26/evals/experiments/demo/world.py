
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



# Constants
SECRET_NUMBER = 42
MESSAGE_ON_THE_FRIDGE = "Remember to buy some more milk."

# Global world instance for agent tools
world: World | None = None

def initialize_world() -> None:
    """Initialize the global world instance for the agent tools."""
    global world
    world = World(
        secret_number=SECRET_NUMBER, 
        message_on_the_fridge=MESSAGE_ON_THE_FRIDGE
    )

initialize_world()
