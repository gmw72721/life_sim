"""
Tick engine for advancing world state.

Handles the core simulation loop for the 8 implemented states.
Resource updates, basic state transitions, and time progression.
"""

from typing import Dict, Any
import random

from .models import WorldState, Actor
from .states import State, can_transition, is_core_state
from .world import load_config, get_resource_rates


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
    # Load configuration for resource rates
    config = load_config()
    rates = get_resource_rates(config)
    
    # Advance the world clock
    world.clock.advance_tick()
    
    # Process each actor
    for actor in world.actors.values():
        _process_actor_tick(actor, rates, world)


def _process_actor_tick(actor: Actor, rates: Dict[str, Dict[str, float]], world: WorldState) -> None:
    """
    Process a single actor for one tick.
    
    Args:
        actor: The actor to process
        rates: Resource rate configuration
        world: The world state (for context)
    """
    # Update resources based on current state
    _update_actor_resources(actor, rates)
    
    # Handle state-specific logic
    _handle_state_logic(actor, world)
    
    # Check for automatic state transitions
    _check_automatic_transitions(actor, world)


def _update_actor_resources(actor: Actor, rates: Dict[str, Dict[str, float]]) -> None:
    """
    Update actor resources based on their current state.
    
    Args:
        actor: The actor to update
        rates: Resource rate configuration
    """
    state_key = actor.state.name.lower()
    
    # Get rate modifiers for current state
    fatigue_delta = rates['fatigue_rate'].get(state_key, 0.0)
    hunger_delta = rates['hunger_rate'].get(state_key, 0.0)
    mood_delta = rates['mood_modifiers'].get(state_key, 0.0)
    
    # Apply resource changes
    actor.update_resources(hunger_delta, fatigue_delta, mood_delta)
    
    # Update other resources (basic logic for now)
    if actor.state == State.Driving:
        actor.battery = max(0.0, actor.battery - 2.0)  # Driving drains battery
    elif actor.state == State.Focused_Work:
        actor.energy = max(0.0, actor.energy - 1.5)   # Work drains energy


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
                actor.state = State.Waking_Up
                actor.substate = "natural_wake"
    
    elif actor.state == State.Waking_Up:
        # Waking up is a brief transition state
        if random.random() < 0.7:  # 70% chance to complete waking up
            actor.state = State.Idle
            actor.substate = None
    
    elif actor.state == State.Idle:
        # Idle actors may decide to do something based on needs
        _handle_idle_decisions(actor, world)
    
    elif actor.state == State.Transitioning:
        # Transitioning is temporary - move to a target state
        _handle_transitioning(actor, world)
    
    elif actor.state in {State.Driving, State.Walking}:
        # Movement states have a chance to complete
        if random.random() < 0.4:  # 40% chance to arrive
            actor.state = State.Idle
            actor.substate = None
    
    elif actor.state == State.Focused_Work:
        # Work sessions have natural end points
        if random.random() < 0.2:  # 20% chance to finish work session
            actor.state = State.Idle
            actor.substate = None
    
    elif actor.state == State.Eating:
        # Eating is typically a short activity
        if random.random() < 0.6:  # 60% chance to finish eating
            actor.state = State.Idle
            actor.substate = None


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
            actor.state = State.Eating
            actor.substate = "hunger_driven"
            return
    
    if actor.fatigue > 80.0:
        # Very tired - try to sleep
        if can_transition(actor, State.Sleeping):
            actor.state = State.Sleeping
            actor.substate = "fatigue_driven"
            return
    
    # Random activities for idle actors (low probability)
    if random.random() < 0.1:  # 10% chance per tick
        possible_states = [State.Focused_Work, State.Eating, State.Transitioning]
        valid_states = [s for s in possible_states if can_transition(actor, s)]
        
        if valid_states:
            new_state = random.choice(valid_states)
            actor.state = new_state
            actor.substate = "spontaneous"


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
        actor.state = new_state
        actor.substate = "from_transition"
    else:
        # Fallback to idle if no valid transitions
        actor.state = State.Idle
        actor.substate = None


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
            actor.state = State.Sleeping
            actor.substate = "emergency_sleep"
    
    elif actor.hunger >= 90.0 and actor.state != State.Eating:
        # Force eating when critically hungry
        if can_transition(actor, State.Eating):
            actor.state = State.Eating
            actor.substate = "emergency_eating"


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