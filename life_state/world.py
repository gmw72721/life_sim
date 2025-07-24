"""
World initialization and configuration management.

Handles creating the initial world state, loading configuration,
and setting up default actors and locations.
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from .models import WorldState, WorldClock, Location, Actor
from .states import State


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml file."""
    config_path = Path(__file__).parent / "config.yaml"
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        # Return default config if file doesn't exist
        return {
            'fatigue_rate': {
                'sleeping': -5.0,
                'waking_up': 0.5,
                'idle': 0.2,
                'transitioning': 1.0,
                'driving': 1.5,
                'walking': 2.0,
                'focused_work': 3.0,
                'eating': 0.5,
            },
            'hunger_rate': {
                'sleeping': 0.3,
                'waking_up': 0.5,
                'idle': 0.8,
                'transitioning': 1.0,
                'driving': 1.2,
                'walking': 1.5,
                'focused_work': 1.8,
                'eating': -15.0,
            },
            'mood_modifiers': {
                'sleeping': 0.1,
                'waking_up': -0.1,
                'idle': -0.05,
                'transitioning': 0.0,
                'driving': -0.02,
                'walking': 0.05,
                'focused_work': 0.02,
                'eating': 0.15,
            }
        }


def initialize_world(world_id: str = "main", start_time: datetime = None) -> WorldState:
    """
    Initialize a new world state with default locations and setup.
    
    Args:
        world_id: Unique identifier for this world instance
        start_time: Starting datetime for the simulation (defaults to now)
        
    Returns:
        WorldState: Fully initialized world ready for simulation
    """
    if start_time is None:
        start_time = datetime.utcnow()
    
    # Create world clock
    clock = WorldClock(current_time=start_time)
    
    # Create world state
    world = WorldState(clock=clock, world_id=world_id)
    
    # Initialize all locations
    locations = Location.create_default_locations()
    for location in locations:
        world.locations[location.id] = location
    
    # Create some sample actors for the demo
    for i, name in enumerate(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]):
        home_letter = chr(ord('A') + (i % 12))  # A through L
        create_sample_actor(world, name, home_letter)
    
    return world


def create_sample_actor(world: WorldState, name: str, home_letter: str = "A") -> Actor:
    """
    Create a sample actor with basic setup.
    
    Args:
        world: The world state to add the actor to
        name: Name for the actor
        home_letter: Letter designation for the actor's home (A-L)
        
    Returns:
        Actor: The created actor
    """
    home_id = f"home_{home_letter.lower()}"
    
    # Verify the home exists
    if home_id not in world.locations:
        raise ValueError(f"Home location {home_id} does not exist")
    
    actor = Actor(
        name=name,
        home_id=home_id,
        location_id=home_id,  # Start at home
        state=State.Idle,
        hunger=25.0,
        fatigue=30.0,
        mood=0.2,
    )
    
    world.add_actor(actor)
    return actor


def get_resource_rates(config: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Extract resource rate configurations.
    
    Args:
        config: Loaded configuration dictionary
        
    Returns:
        Dict containing fatigue_rate, hunger_rate, and mood_modifiers
    """
    return {
        'fatigue_rate': config.get('fatigue_rate', {}),
        'hunger_rate': config.get('hunger_rate', {}),
        'mood_modifiers': config.get('mood_modifiers', {}),
    }


# TODO: Prompt 2 will add functions for:
# - create_scheduled_actor() with pre-populated calendar
# - initialize_probability_weights() from config
# - setup_time_jump_triggers()
# - create_world_fork() for parallel timeline management

# TODO: Prompt 3 will add functions for:
# - initialize_database_connection()
# - setup_api_middleware()
# - configure_real_time_updates()