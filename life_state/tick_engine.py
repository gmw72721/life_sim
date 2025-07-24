"""
Tick engine for advancing world state.

Handles the core simulation loop for the 8 implemented states.
Resource updates, basic state transitions, and time progression.
"""

from typing import Dict, Any
import random
import logging

from .models import WorldState, Actor
from .states import State, can_transition, is_core_state, on_enter_state, on_exit_state
from .world import load_config, get_resource_rates

# Configure logging
logger = logging.getLogger(__name__)


def advance_world(world: WorldState) -> None:
    """
    Advance the world by one tick (15 minutes).
    
    This is the core simulation step that:
    1. Updates the world clock
    2. Processes all actors' states and resources
    3. Handles basic state transitions
    
    Args:
        world: The world state to advance
    """
    logger.debug(f"=== TICK {world.clock.tick_count} START === World: {world.world_id} Time: {world.clock.current_time}")
    
    # Load configuration for resource rates
    config = load_config()
    rates = get_resource_rates(config)
    
    # Advance the world clock
    world.clock.advance_tick()
    
    # Process each actor
    for actor in world.actors.values():
        logger.debug(f"Processing actor {actor.name} in state {actor.state}")
        _process_actor_tick(actor, rates, world)
    
    logger.debug(f"=== TICK {world.clock.tick_count} END === World: {world.world_id}")


def _process_actor_tick(actor: Actor, rates: Dict[str, Dict[str, float]], world: WorldState) -> None:
    """
    Process a single actor for one tick.
    
    Args:
        actor: The actor to process
        rates: Resource rate configuration
        world: The world state (for context)
    """
    old_state = actor.state
    
    # Update resources based on current state
    _update_actor_resources(actor, rates)
    
    # Handle state-specific logic
    _handle_state_logic(actor, world)
    
    # Check for automatic state transitions
    _check_automatic_transitions(actor, world)
    
    # Handle state change hooks if state changed
    if actor.state != old_state:
        logger.debug(f"Actor {actor.name} transitioned from {old_state} to {actor.state}")
        try:
            on_exit_state(actor, old_state)
            on_enter_state(actor, actor.state)
        except NotImplementedError as e:
            logger.warning(f"State transition hook not implemented: {e}")


def _update_actor_resources(actor: Actor, rates: Dict[str, Dict[str, float]]) -> None:
    """
    Update actor resources based on their current state.
    
    Args:
        actor: The actor to update
        rates: Resource rate configuration
    """
    state_key = actor.state.name.lower()
    
    # Get rate modifiers for current state with defaults
    fatigue_delta = rates['fatigue_rate'].get(state_key, 0.5)  # Default small fatigue increase
    hunger_delta = rates['hunger_rate'].get(state_key, 0.8)   # Default hunger increase
    mood_delta = rates['mood_modifiers'].get(state_key, 0.0)  # Default neutral mood
    
    # Store old values for logging
    old_hunger = actor.hunger
    old_fatigue = actor.fatigue
    old_mood = actor.mood
    
    # Apply resource changes
    actor.update_resources(hunger_delta, fatigue_delta, mood_delta)
    
    # Log significant resource changes
    if abs(actor.hunger - old_hunger) > 5 or abs(actor.fatigue - old_fatigue) > 5:
        logger.debug(f"Actor {actor.name} resources: H:{old_hunger:.1f}→{actor.hunger:.1f} "
                    f"F:{old_fatigue:.1f}→{actor.fatigue:.1f} M:{old_mood:.2f}→{actor.mood:.2f}")
    
    # Update other resources (basic logic for now)
    if actor.state == State.Driving:
        actor.battery = max(0.0, actor.battery - 2.0)  # Driving drains battery
        if actor.battery <= 0:
            logger.debug(f"Actor {actor.name} battery depleted while driving")
    elif actor.state == State.Focused_Work:
        actor.energy = max(0.0, actor.energy - 1.5)   # Work drains energy
        if actor.energy <= 10:
            logger.debug(f"Actor {actor.name} energy low while working")


def _handle_state_logic(actor: Actor, world: WorldState) -> None:
    """
    Handle state-specific logic and behaviors.
    
    Args:
        actor: The actor to process
        world: The world state
    """
    if actor.state == State.Sleeping:
        # Sleeping actors recover resources faster
        if actor.fatigue < 10.0 and random.random() < 0.3:
            # Chance to wake up when well-rested
            if can_transition(actor, State.Waking_Up):
                logger.debug(f"Actor {actor.name} naturally waking up (fatigue: {actor.fatigue:.1f})")
                actor.state = State.Waking_Up
    
    elif actor.state == State.Waking_Up:
        # Waking up is a brief transition state
        if random.random() < 0.7:  # 70% chance to complete waking up
            logger.debug(f"Actor {actor.name} finished waking up")
            actor.state = State.Idle
    
    elif actor.state == State.Idle:
        # Idle actors may decide to do something based on needs
        _handle_idle_decisions(actor, world)
    
    elif actor.state == State.Transitioning:
        # Transitioning is temporary - move to a target state
        _handle_transitioning(actor, world)
    
    elif actor.state in {State.Driving, State.Walking}:
        # Movement states have a chance to complete
        if random.random() < 0.4:  # 40% chance to arrive
            logger.debug(f"Actor {actor.name} finished {actor.state.name.lower()}")
            actor.state = State.Idle
    
    elif actor.state == State.Focused_Work:
        # Work sessions have natural end points
        if random.random() < 0.2:  # 20% chance to finish work session
            logger.debug(f"Actor {actor.name} finished work session")
            actor.state = State.Idle
    
    elif actor.state == State.Eating:
        # Eating is typically a short activity
        if random.random() < 0.6:  # 60% chance to finish eating
            logger.debug(f"Actor {actor.name} finished eating")
            actor.state = State.Idle


def _handle_idle_decisions(actor: Actor, world: WorldState) -> None:
    """
    Handle decision-making for idle actors based on their needs.
    
    Args:
        actor: The idle actor
        world: The world state
    """
    # Check for high-priority needs
    if actor.hunger > 70.0:
        # Very hungry - try to eat
        if can_transition(actor, State.Eating):
            logger.debug(f"Actor {actor.name} eating due to high hunger ({actor.hunger:.1f})")
            actor.state = State.Eating
            return
    
    if actor.fatigue > 80.0:
        # Very tired - try to sleep
        if can_transition(actor, State.Sleeping):
            logger.debug(f"Actor {actor.name} sleeping due to high fatigue ({actor.fatigue:.1f})")
            actor.state = State.Sleeping
            return
    
    # Random activities for idle actors (low probability)
    if random.random() < 0.1:  # 10% chance per tick
        possible_states = [State.Focused_Work, State.Eating, State.Transitioning]
        valid_states = [s for s in possible_states if can_transition(actor, s)]
        
        if valid_states:
            new_state = random.choice(valid_states)
            logger.debug(f"Actor {actor.name} spontaneously starting {new_state.name}")
            actor.state = new_state


def _handle_transitioning(actor: Actor, world: WorldState) -> None:
    """
    Handle actors in the transitioning state.
    
    Args:
        actor: The transitioning actor
        world: The world state
    """
    # Transitioning actors move to a random valid state
    possible_states = [
        State.Idle, State.Driving, State.Walking, 
        State.Focused_Work, State.Eating
    ]
    
    valid_states = [s for s in possible_states if can_transition(actor, s)]
    
    if valid_states:
        new_state = random.choice(valid_states)
        logger.debug(f"Actor {actor.name} transitioning to {new_state.name}")
        actor.state = new_state
    else:
        # Fallback to idle if no valid transitions
        logger.debug(f"Actor {actor.name} transitioning to idle (no valid states)")
        actor.state = State.Idle


def _check_automatic_transitions(actor: Actor, world: WorldState) -> None:
    """
    Check for automatic state transitions based on conditions.
    
    Args:
        actor: The actor to check
        world: The world state
    """
    # Emergency transitions based on critical resource levels
    if actor.fatigue >= 95.0 and actor.state != State.Sleeping:
        # Force sleep when critically tired
        if can_transition(actor, State.Sleeping):
            logger.debug(f"Actor {actor.name} emergency sleep (fatigue: {actor.fatigue:.1f})")
            actor.state = State.Sleeping
    
    elif actor.hunger >= 90.0 and actor.state != State.Eating:
        # Force eating when critically hungry
        if can_transition(actor, State.Eating):
            logger.debug(f"Actor {actor.name} emergency eating (hunger: {actor.hunger:.1f})")
            actor.state = State.Eating


def get_world_summary(world: WorldState) -> Dict[str, Any]:
    """
    Generate a summary of the current world state.
    
    Args:
        world: The world state to summarize
        
    Returns:
        Dict containing summary statistics
    """
    state_counts = {}
    total_actors = len(world.actors)
    
    # Count actors by state
    for state in State:
        if is_core_state(state):
            count = len(world.get_actors_in_state(state))
            state_counts[state.name] = count
    
    # Calculate average resources
    if total_actors > 0:
        avg_hunger = sum(actor.hunger for actor in world.actors.values()) / total_actors
        avg_fatigue = sum(actor.fatigue for actor in world.actors.values()) / total_actors
        avg_mood = sum(actor.mood for actor in world.actors.values()) / total_actors
    else:
        avg_hunger = avg_fatigue = avg_mood = 0.0
    
    return {
        'tick': world.clock.tick_count,
        'current_time': world.clock.current_time.isoformat(),
        'world_id': world.world_id,
        'total_actors': total_actors,
        'state_distribution': state_counts,
        'average_resources': {
            'hunger': round(avg_hunger, 2),
            'fatigue': round(avg_fatigue, 2),
            'mood': round(avg_mood, 2),
        }
    }


# TODO: Prompt 2 will add:
# - Action execution system integration
# - Probability-based decision making
# - Calendar/schedule following logic
# - Time-jump trigger detection
# - Multi-world synchronization

# TODO: Prompt 3 will add:
# - Real-time state broadcasting
# - Performance metrics collection
# - Database persistence hooks