"""
Probability modifiers and decision-making system.

Implements the probability calculation engine with need-based modifiers,
environmental factors, and weighted action selection.
"""

import random
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum, auto

from .actions import Action, get_available_actions, TIME_JUMP
from .states import State


def mood_factor(mood: float) -> float:
    """
    Calculate mood modifier for action probability.
    
    Args:
        mood: Actor's mood (-2 to +2)
        
    Returns:
        float: Mood factor (1 + 0.015 * mood)
    """
    return 1.0 + (0.015 * mood)


def hunger_factor(hunger: float) -> float:
    """
    Calculate hunger modifier for action probability.
    
    Args:
        hunger: Actor's hunger level (0-100)
        
    Returns:
        float: Hunger factor (linear scale 0.8 to 1.2)
    """
    # Normalize hunger to 0-1 range, then scale to 0.8-1.2
    normalized = hunger / 100.0
    return 0.8 + (0.4 * normalized)


def fatigue_factor(fatigue: float) -> float:
    """
    Calculate fatigue modifier for action probability.
    
    Args:
        fatigue: Actor's fatigue level (0-100)
        
    Returns:
        float: Fatigue factor (linear scale 0.8 to 1.2)
    """
    # Normalize fatigue to 0-1 range, then scale to 0.8-1.2
    normalized = fatigue / 100.0
    return 0.8 + (0.4 * normalized)


def presence_boost(n_present: int) -> float:
    """
    Calculate presence boost for social actions.
    
    Args:
        n_present: Number of other actors present at location
        
    Returns:
        float: Presence boost (min(n, 3) * 0.2)
    """
    return min(n_present, 3) * 0.2


def calculate_action_probability(action: Action, actor, world_state) -> float:
    """
    Calculate the probability of an actor choosing a specific action.
    
    Args:
        action: The action being considered
        actor: The actor considering the action
        world_state: Current world state
        
    Returns:
        float: Calculated probability weight
    """
    # Start with base weight
    prob = action.weight
    
    # Apply mood factor
    prob *= mood_factor(actor.mood)
    
    # Apply hunger factor - higher hunger increases eating actions
    if action.hunger_delta < 0:  # Action reduces hunger (eating)
        prob *= (1.0 + (actor.hunger / 100.0))  # More hungry = more likely to eat
    else:
        prob *= hunger_factor(actor.hunger)
    
    # Apply fatigue factor - higher fatigue increases rest actions
    if action.fatigue_delta < 0:  # Action reduces fatigue (sleeping, resting)
        prob *= (1.0 + (actor.fatigue / 100.0))  # More tired = more likely to rest
    else:
        prob *= fatigue_factor(actor.fatigue)
    
    # Apply presence boost for social actions
    if action.requires_presence == "Any":
        actors_at_location = world_state.get_actors_at_location(actor.location_id)
        n_present = len([a for a in actors_at_location if a.id != actor.id])
        prob *= (1.0 + presence_boost(n_present))
    
    # Special modifiers for specific action types
    if action.resulting_state == State.Sleeping:
        # More likely to sleep when very tired or at night
        hour = world_state.clock.current_time.hour
        if hour >= 22 or hour <= 6:
            prob *= 2.0
        if actor.fatigue > 80:
            prob *= 3.0
    
    elif action.resulting_state == State.Eating:
        # More likely to eat when very hungry or at meal times
        hour = world_state.clock.current_time.hour
        if hour in [7, 8, 12, 13, 18, 19]:  # Meal times
            prob *= 1.5
        if actor.hunger > 70:
            prob *= 2.5
    
    elif action.resulting_state == State.Focused_Work:
        # More likely to work during business hours
        hour = world_state.clock.current_time.hour
        if 9 <= hour <= 17:
            prob *= 2.0
        else:
            prob *= 0.3
    
    elif action.resulting_state == State.Exercising:
        # Less likely to exercise when very tired
        if actor.fatigue > 70:
            prob *= 0.5
    
    elif action.resulting_state == State.Socialising:
        # More likely to socialize with good mood
        if actor.mood > 1.0:
            prob *= 1.5
        elif actor.mood < -1.0:
            prob *= 0.5
    
    return max(0.0, prob)  # Ensure non-negative


def choose_action(actor, world_state) -> Optional[Action]:
    """
    Choose an action for an actor using weighted probability selection.
    
    Args:
        actor: The actor choosing an action
        world_state: Current world state
        
    Returns:
        Selected action or None if no valid actions
    """
    from .time_jump import gateway_open, TIME_JUMP_PROB
    
    # Get available actions
    available_actions = get_available_actions(actor, world_state)
    
    if not available_actions:
        return None
    
    # Calculate probabilities for each action
    action_probs = []
    for action in available_actions:
        prob = calculate_action_probability(action, actor, world_state)
        action_probs.append(prob)
    
    # Check if time jump should be inserted
    if gateway_open(actor, world_state.clock):
        # Add time jump action with special probability
        if TIME_JUMP not in available_actions:
            available_actions.append(TIME_JUMP)
            time_jump_prob = TIME_JUMP_PROB * TIME_JUMP.weight
            action_probs.append(time_jump_prob)
    
    # Normalize probabilities
    total_prob = sum(action_probs)
    if total_prob <= 0:
        # Fallback to uniform selection
        return random.choice(available_actions)
    
    normalized_probs = [p / total_prob for p in action_probs]
    
    # Weighted random selection
    return select_action_weighted(available_actions, normalized_probs)


def select_action_weighted(available_actions: List[Action], probabilities: List[float]) -> Optional[Action]:
    """
    Select an action using weighted random selection.
    
    Args:
        available_actions: List of available actions
        probabilities: Corresponding probabilities for each action
        
    Returns:
        Selected action or None
    """
    if not available_actions or not probabilities:
        return None
    
    if len(available_actions) != len(probabilities):
        return None
    
    # Use random.choices for weighted selection
    try:
        selected = random.choices(available_actions, weights=probabilities, k=1)
        return selected[0] if selected else None
    except (ValueError, IndexError):
        # Fallback to uniform selection
        return random.choice(available_actions) if available_actions else None


def apply_need_modifiers(base_prob: float, actor, action: Action) -> float:
    """
    Apply need-based probability modifiers.
    
    Args:
        base_prob: Base probability to modify
        actor: The actor with needs
        action: The action being considered
        
    Returns:
        float: Modified probability
    """
    modified_prob = base_prob
    
    # Hunger-based modifiers
    if actor.hunger > 80 and action.hunger_delta < 0:
        modified_prob *= 2.0  # Very hungry, eating action
    elif actor.hunger < 20 and action.hunger_delta > 0:
        modified_prob *= 0.5  # Not hungry, non-eating action
    
    # Fatigue-based modifiers
    if actor.fatigue > 85 and action.fatigue_delta < 0:
        modified_prob *= 3.0  # Very tired, resting action
    elif actor.fatigue < 15 and action.fatigue_delta < 0:
        modified_prob *= 0.3  # Not tired, resting action
    
    # Mood-based modifiers
    if actor.mood < -1.5 and action.requires_presence == "Any":
        modified_prob *= 0.3  # Very sad, avoid social actions
    elif actor.mood > 1.5 and action.requires_presence == "Any":
        modified_prob *= 1.8  # Very happy, prefer social actions
    
    return modified_prob


def apply_environmental_modifiers(base_prob: float, actor, action: Action, world_state) -> float:
    """
    Apply environmental probability modifiers.
    
    Args:
        base_prob: Base probability to modify
        actor: The actor in the environment
        action: The action being considered
        world_state: Current world state
        
    Returns:
        float: Modified probability
    """
    modified_prob = base_prob
    
    # Location-based modifiers
    current_location = world_state.get_location(actor.location_id)
    if current_location:
        if current_location.category == "home":
            # At home - more likely to do home activities
            if action.next_location is None:  # Staying at current location
                modified_prob *= 1.3
        elif current_location.category == "public":
            # In public - more likely to do public activities
            if action.requires_presence == "Any":
                modified_prob *= 1.2
    
    # Time-based modifiers
    hour = world_state.clock.current_time.hour
    
    # Night time (22:00 - 06:00)
    if hour >= 22 or hour <= 6:
        if action.resulting_state == State.Sleeping:
            modified_prob *= 2.5
        elif action.resulting_state in [State.Focused_Work, State.Exercising]:
            modified_prob *= 0.2
    
    # Morning (07:00 - 09:00)
    elif 7 <= hour <= 9:
        if action.resulting_state == State.Eating:
            modified_prob *= 1.8
        elif action.resulting_state == State.Commuting:
            modified_prob *= 2.0
    
    # Work hours (09:00 - 17:00)
    elif 9 <= hour <= 17:
        if action.resulting_state == State.Focused_Work:
            modified_prob *= 2.5
        elif action.resulting_state in [State.Leisure, State.Exercising]:
            modified_prob *= 0.4
    
    # Evening (18:00 - 21:00)
    elif 18 <= hour <= 21:
        if action.resulting_state in [State.Leisure, State.Socialising, State.Eating]:
            modified_prob *= 1.5
    
    return modified_prob


def apply_schedule_modifiers(base_prob: float, actor, action: Action, world_state) -> float:
    """
    Apply schedule/calendar-based modifiers.
    
    Args:
        base_prob: Base probability to modify
        actor: The actor with a schedule
        action: The action being considered
        world_state: Current world state with time
        
    Returns:
        float: Modified probability
    """
    modified_prob = base_prob
    
    # Check if there's a current time block
    current_block = actor.get_current_time_block(world_state.clock.current_time)
    if current_block:
        # If action matches scheduled state, boost probability
        if action.resulting_state == current_block.required_state:
            modified_prob *= 3.0
        else:
            # If action conflicts with schedule, reduce probability
            modified_prob *= 0.3
    
    # Check upcoming schedule (next hour)
    next_hour = world_state.clock.current_time.replace(
        hour=(world_state.clock.current_time.hour + 1) % 24,
        minute=0
    )
    
    for block in actor.calendar:
        if block.start_dt <= next_hour < block.end_dt:
            # Prepare for upcoming scheduled activity
            if action.resulting_state == State.Transitioning:
                modified_prob *= 1.5
            break
    
    return modified_prob


def generate_random_events(world_state) -> List[Dict[str, Any]]:
    """
    Generate random events that affect probabilities.
    
    Args:
        world_state: Current world state
        
    Returns:
        List of random events to process
    """
    events = []
    
    # Random chance of various events
    if random.random() < 0.05:  # 5% chance per tick
        event_type = random.choice([
            "weather_change",
            "equipment_failure", 
            "social_encounter",
            "emergency_situation"
        ])
        
        events.append({
            "type": event_type,
            "tick": world_state.clock.tick_count,
            "time": world_state.clock.current_time,
            "description": f"Random {event_type} occurred"
        })
    
    return events


def calculate_final_probability(actor, action: Action, world_state) -> float:
    """
    Calculate final probability after all modifiers.
    
    Args:
        actor: The actor considering the action
        action: The action being considered
        world_state: Current world state
        
    Returns:
        float: Final probability (0.0 to 1.0)
    """
    # Start with base calculation
    base_prob = calculate_action_probability(action, actor, world_state)
    
    # Apply all modifier layers
    prob = apply_need_modifiers(base_prob, actor, action)
    prob = apply_environmental_modifiers(prob, actor, action, world_state)
    prob = apply_schedule_modifiers(prob, actor, action, world_state)
    
    # Clamp to valid range
    return max(0.0, min(10.0, prob))  # Allow up to 10x base weight