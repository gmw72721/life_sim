"""
World initialization and configuration management.

Handles creating the initial world state, loading configuration,
and setting up default actors and locations.
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging

from .models import WorldState, WorldClock, Location, Actor
from .states import State

# Configure logging
logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml file."""
    config_path = Path(__file__).parent / "config.yaml"
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.debug(f"Loaded configuration from {config_path}")
        return config
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}, using defaults")
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
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {e}")
        raise


def initialize_world(start_time: datetime = None, world_id: str = "main") -> WorldState:
    """
    Initialize a new world state with default locations and setup.
    
    Args:
        start_time: Starting datetime for the simulation (defaults to now)
        world_id: Unique identifier for this world instance
        
    Returns:
        WorldState: Fully initialized world ready for simulation
    """
    if start_time is None:
        start_time = datetime.utcnow()
    
    logger.info(f"Initializing world '{world_id}' at {start_time}")
    
    # Create world clock
    clock = WorldClock(current_time=start_time)
    
    # Create world state
    world = WorldState(clock=clock, world_id=world_id)
    
    # Initialize all locations
    locations = Location.create_default_locations()
    for location in locations:
        world.locations[location.id] = location
    
    logger.info(f"Created world with {len(world.locations)} locations")
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
        world_id=world.world_id,  # Ensure world_id is set
        state=State.Idle,     # Start in idle state
        hunger=25.0,
        fatigue=30.0,
        mood=0.2,
    )
    
    world.add_actor(actor)
    logger.debug(f"Created actor {name} at {home_id}")
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


def add_actor_to_world(world: WorldState, actor: Actor) -> None:
    """
    Add an actor to the world with proper initialization.
    
    Args:
        world: The world to add the actor to
        actor: The actor to add
    """
    # Ensure actor has valid state and location
    if not hasattr(actor, 'state') or actor.state is None:
        actor.state = State.Idle
        logger.debug(f"Set default state for actor {actor.name}")
    
    if not hasattr(actor, 'location_id') or not actor.location_id:
        # Default to their home if available
        if actor.home_id in world.locations:
            actor.location_id = actor.home_id
        else:
            # Fallback to first available home
            home_locations = [loc_id for loc_id in world.locations.keys() if loc_id.startswith('home_')]
            if home_locations:
                actor.location_id = home_locations[0]
                actor.home_id = home_locations[0]
            else:
                raise ValueError("No valid home locations available for actor")
        logger.debug(f"Set default location for actor {actor.name}: {actor.location_id}")
    
    # Ensure world_id is correct
    actor.world_id = world.world_id
    
    # Add to world
    world.add_actor(actor)


def remove_actor_from_world(world: WorldState, actor_id: str) -> bool:
    """
    Remove an actor from the world.
    
    Args:
        world: The world to remove the actor from
        actor_id: ID of the actor to remove
        
    Returns:
        bool: True if actor was removed, False if not found
    """
    if actor_id in world.actors:
        actor_name = world.actors[actor_id].name
        del world.actors[actor_id]
        logger.debug(f"Removed actor {actor_name} from world {world.world_id}")
        return True
    return False


def fork_world_basic(src_world: WorldState, new_world_id: str) -> WorldState:
    """
    Create a basic fork of a world (stub for time_jump module).
    
    Args:
        src_world: Source world to fork
        new_world_id: ID for the new world
        
    Returns:
        WorldState: New forked world
    """
    # This is a basic stub - full implementation in time_jump.py
    from copy import deepcopy
    
    forked_world = deepcopy(src_world)
    forked_world.world_id = new_world_id
    
    # Update all actors' world_id
    for actor in forked_world.actors.values():
        actor.world_id = new_world_id
    
    logger.info(f"Created basic fork {new_world_id} from {src_world.world_id}")
    return forked_world


# TODO: Prompt 2 will add functions for:
# - create_scheduled_actor() with pre-populated calendar
# - initialize_probability_weights() from config
# - setup_time_jump_triggers()
# - create_world_fork() for parallel timeline management

# TODO: Prompt 3 will add functions for:
# - initialize_database_connection()
# - setup_api_middleware()
# - configure_real_time_updates()