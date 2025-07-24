"""
State management for life_state simulation.

Defines all possible actor states and basic transition logic.
Core states are implemented in Prompt 1, extended states reserved for Prompt 2.
"""

from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Actor


class State(Enum):
    """All possible actor states in the simulation."""
    
    # Core states implemented in Prompt 1
    Sleeping = auto()
    Waking_Up = auto()
    Idle = auto()
    Transitioning = auto()
    Driving = auto()
    Walking = auto()
    Focused_Work = auto()
    Eating = auto()

    # --- Reserved for Prompt 2 logic ---
    Commuting = auto()      # TODO: Prompt 2 - scheduled travel between locations
    Socialising = auto()    # TODO: Prompt 2 - interaction with other actors
    Leisure = auto()        # TODO: Prompt 2 - recreational activities
    Shopping = auto()       # TODO: Prompt 2 - purchasing actions
    Exercising = auto()     # TODO: Prompt 2 - fitness activities
    In_Meeting = auto()     # TODO: Prompt 2 - scheduled work interactions
    TimeJumping = auto()    # TODO: Prompt 2 - triggers multi-world fork
    # -----------------------------------


def can_transition(actor: "Actor", new_state: State) -> bool:
    """
    Check if an actor can transition to a new state.
    
    Args:
        actor: The actor attempting the transition
        new_state: The target state
        
    Returns:
        bool: True if transition is allowed, False otherwise
    """
    # Block transitions to unimplemented states until Prompt 2
    unimplemented_states = {
        State.Commuting,
        State.Socialising,
        State.Leisure,
        State.Shopping,
        State.Exercising,
        State.In_Meeting,
        State.TimeJumping,
    }
    
    if new_state in unimplemented_states:
        # TODO: Prompt 2 - implement transition logic for these states
        return False
    
    # Basic transition rules for core states
    current_state = actor.state
    
    # Universal transitions (can happen from any state)
    if new_state in {State.Transitioning, State.Sleeping}:
        return True
    
    # State-specific transition rules
    if current_state == State.Sleeping:
        return new_state == State.Waking_Up
    
    if current_state == State.Waking_Up:
        return new_state in {State.Idle, State.Eating}
    
    if current_state == State.Idle:
        return new_state in {
            State.Driving, State.Walking, State.Focused_Work, 
            State.Eating, State.Transitioning
        }
    
    if current_state == State.Transitioning:
        # Can transition to any implemented state
        return new_state not in unimplemented_states
    
    if current_state in {State.Driving, State.Walking}:
        # Movement states can go to idle or continue moving
        return new_state in {State.Idle, State.Transitioning}
    
    if current_state == State.Focused_Work:
        return new_state in {State.Idle, State.Transitioning, State.Eating}
    
    if current_state == State.Eating:
        return new_state in {State.Idle, State.Transitioning}
    
    # Default: allow transition
    return True


def get_valid_transitions(actor: "Actor") -> list[State]:
    """
    Get all valid states the actor can transition to from their current state.
    
    Args:
        actor: The actor to check transitions for
        
    Returns:
        list[State]: List of valid target states
    """
    return [state for state in State if can_transition(actor, state)]


def is_core_state(state: State) -> bool:
    """
    Check if a state is implemented in the core (Prompt 1) logic.
    
    Args:
        state: The state to check
        
    Returns:
        bool: True if state is implemented in core logic
    """
    core_states = {
        State.Sleeping,
        State.Waking_Up,
        State.Idle,
        State.Transitioning,
        State.Driving,
        State.Walking,
        State.Focused_Work,
        State.Eating,
    }
    return state in core_states