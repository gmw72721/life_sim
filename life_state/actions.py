"""
Action catalogue and execution system.

Defines all possible actor actions with their requirements, effects, and probabilities.
Integrates with the state transition system and probability engine.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum, auto

from .states import State


class Action(BaseModel):
    """Complete action data structure with all requirements and effects."""
    
    name: str = Field(description="Human-readable name of the action")
    resulting_state: State = Field(description="State the actor will be in after this action")
    duration_ticks: int = Field(default=1, description="How many ticks this action takes")
    location_req: Optional[List[str]] = Field(default=None, description="Allowed current locations (None = any)")
    next_location: Optional[str] = Field(default=None, description="Where actor ends up (None = unchanged)")
    hunger_delta: int = Field(default=0, description="Change in hunger level")
    fatigue_delta: int = Field(default=0, description="Change in fatigue level")
    cash_delta: float = Field(default=0.0, description="Change in cash amount")
    allowed_moods: tuple[int, int] = Field(default=(-2, 2), description="Mood range required for this action")
    requires_presence: Literal["Self", "Any", "Specific"] = Field(default="Self", description="Presence requirement")
    weight: float = Field(default=1.0, description="Base probability weight")


# ============================================================================
# ACTION DEFINITIONS - Core States (from Prompt 1)
# ============================================================================

GO_TO_SLEEP = Action(
    name="Go to Sleep",
    resulting_state=State.Sleeping,
    duration_ticks=1,
    location_req=["home_a", "home_b", "home_c", "home_d", "home_e", "home_f", 
                  "home_g", "home_h", "home_i", "home_j", "home_k", "home_l"],
    fatigue_delta=-20,
    hunger_delta=2,
    weight=2.0
)

WAKE_UP = Action(
    name="Wake Up",
    resulting_state=State.Waking_Up,
    duration_ticks=1,
    fatigue_delta=5,
    weight=1.5
)

STAY_IDLE = Action(
    name="Stay Idle",
    resulting_state=State.Idle,
    duration_ticks=1,
    hunger_delta=1,
    fatigue_delta=1,
    weight=1.0
)

START_TRANSITION = Action(
    name="Start Transition",
    resulting_state=State.Transitioning,
    duration_ticks=1,
    fatigue_delta=2,
    weight=1.2
)

DRIVE_TO_OFFICE = Action(
    name="Drive to Office",
    resulting_state=State.Driving,
    duration_ticks=2,
    next_location="public_office",
    fatigue_delta=3,
    cash_delta=-5.0,
    weight=1.5
)

DRIVE_HOME = Action(
    name="Drive Home",
    resulting_state=State.Driving,
    duration_ticks=2,
    location_req=["public_office", "public_coffee_shop", "public_restaurant", "public_mall"],
    fatigue_delta=3,
    cash_delta=-5.0,
    weight=1.8
)

WALK_TO_PARK = Action(
    name="Walk to Park",
    resulting_state=State.Walking,
    duration_ticks=3,
    next_location="public_park",
    fatigue_delta=5,
    hunger_delta=3,
    weight=1.2
)

WALK_TO_COFFEE_SHOP = Action(
    name="Walk to Coffee Shop",
    resulting_state=State.Walking,
    duration_ticks=2,
    next_location="public_coffee_shop",
    fatigue_delta=4,
    hunger_delta=2,
    weight=1.3
)

START_WORK = Action(
    name="Start Focused Work",
    resulting_state=State.Focused_Work,
    duration_ticks=4,
    location_req=["public_office", "home_a", "home_b", "home_c", "home_d", "home_e", "home_f"],
    fatigue_delta=8,
    hunger_delta=6,
    cash_delta=25.0,
    allowed_moods=(-1, 2),
    weight=1.8
)

EAT_MEAL = Action(
    name="Eat a Meal",
    resulting_state=State.Eating,
    duration_ticks=2,
    location_req=["public_restaurant", "public_coffee_shop", "home_a", "home_b", "home_c", 
                  "home_d", "home_e", "home_f", "home_g", "home_h", "home_i", "home_j", "home_k", "home_l"],
    hunger_delta=-25,
    fatigue_delta=2,
    cash_delta=-15.0,
    weight=2.5
)

GRAB_SNACK = Action(
    name="Grab a Snack",
    resulting_state=State.Eating,
    duration_ticks=1,
    hunger_delta=-10,
    cash_delta=-5.0,
    weight=1.5
)

# ============================================================================
# ACTION DEFINITIONS - Commuting Actions
# ============================================================================

COMMUTE_BY_CAR = Action(
    name="Commute by Car",
    resulting_state=State.Commuting,
    duration_ticks=3,
    location_req=["home_a", "home_b", "home_c", "home_d", "home_e", "home_f"],
    next_location="public_office",
    fatigue_delta=4,
    cash_delta=-8.0,
    weight=2.0
)

COMMUTE_WALKING = Action(
    name="Commute Walking",
    resulting_state=State.Commuting,
    duration_ticks=6,
    location_req=["home_a", "home_b", "home_c", "home_d", "home_e", "home_f"],
    next_location="public_office",
    fatigue_delta=12,
    hunger_delta=8,
    weight=1.0
)

TAKE_BUS = Action(
    name="Take Bus",
    resulting_state=State.Commuting,
    duration_ticks=4,
    location_req=["public_bus"],
    next_location="public_office",
    fatigue_delta=2,
    cash_delta=-3.0,
    weight=1.3
)

RETURN_HOME_CAR = Action(
    name="Return Home by Car",
    resulting_state=State.Commuting,
    duration_ticks=3,
    location_req=["public_office"],
    fatigue_delta=4,
    cash_delta=-8.0,
    weight=2.2
)

# ============================================================================
# ACTION DEFINITIONS - Social Actions
# ============================================================================

MEET_COLLEAGUE = Action(
    name="Meet with Colleague",
    resulting_state=State.Socialising,
    duration_ticks=3,
    location_req=["public_office", "public_coffee_shop"],
    fatigue_delta=3,
    hunger_delta=2,
    requires_presence="Any",
    allowed_moods=(-1, 2),
    weight=1.5
)

CHAT_WITH_FRIEND = Action(
    name="Chat with Friend",
    resulting_state=State.Socialising,
    duration_ticks=2,
    location_req=["public_coffee_shop", "public_bar", "public_park"],
    fatigue_delta=1,
    requires_presence="Any",
    allowed_moods=(0, 2),
    weight=1.8
)

ATTEND_SOCIAL_EVENT = Action(
    name="Attend Social Event",
    resulting_state=State.Socialising,
    duration_ticks=4,
    location_req=["public_bar", "public_restaurant"],
    fatigue_delta=6,
    hunger_delta=3,
    cash_delta=-20.0,
    requires_presence="Any",
    allowed_moods=(0, 2),
    weight=1.2
)

NETWORK_EVENT = Action(
    name="Attend Networking Event",
    resulting_state=State.Socialising,
    duration_ticks=3,
    location_req=["public_office", "public_restaurant"],
    fatigue_delta=5,
    hunger_delta=2,
    cash_delta=-10.0,
    requires_presence="Any",
    allowed_moods=(-1, 2),
    weight=1.0
)

# ============================================================================
# ACTION DEFINITIONS - Exercise Actions
# ============================================================================

GYM_WORKOUT = Action(
    name="Gym Workout",
    resulting_state=State.Exercising,
    duration_ticks=4,
    location_req=["public_gym"],
    fatigue_delta=15,
    hunger_delta=12,
    cash_delta=-12.0,
    allowed_moods=(-1, 2),
    weight=1.3
)

JOG_IN_PARK = Action(
    name="Jog in Park",
    resulting_state=State.Exercising,
    duration_ticks=3,
    location_req=["public_park"],
    fatigue_delta=10,
    hunger_delta=8,
    allowed_moods=(0, 2),
    weight=1.5
)

HOME_EXERCISE = Action(
    name="Exercise at Home",
    resulting_state=State.Exercising,
    duration_ticks=2,
    location_req=["home_a", "home_b", "home_c", "home_d", "home_e", "home_f", 
                  "home_g", "home_h", "home_i", "home_j", "home_k", "home_l"],
    fatigue_delta=8,
    hunger_delta=6,
    weight=1.2
)

WALK_FOR_EXERCISE = Action(
    name="Walk for Exercise",
    resulting_state=State.Exercising,
    duration_ticks=2,
    location_req=["public_walking_path", "public_park"],
    fatigue_delta=6,
    hunger_delta=4,
    weight=1.4
)

# ============================================================================
# ACTION DEFINITIONS - Leisure Actions
# ============================================================================

WATCH_MOVIE = Action(
    name="Watch Movie",
    resulting_state=State.Leisure,
    duration_ticks=6,
    location_req=["public_cinema", "home_a", "home_b", "home_c", "home_d", "home_e", "home_f"],
    fatigue_delta=2,
    hunger_delta=3,
    cash_delta=-15.0,
    weight=1.4
)

READ_BOOK = Action(
    name="Read Book",
    resulting_state=State.Leisure,
    duration_ticks=3,
    location_req=["public_library", "home_a", "home_b", "home_c", "home_d", "home_e", "home_f"],
    fatigue_delta=1,
    hunger_delta=1,
    allowed_moods=(-1, 2),
    weight=1.3
)

BROWSE_LIBRARY = Action(
    name="Browse Library",
    resulting_state=State.Leisure,
    duration_ticks=2,
    location_req=["public_library"],
    fatigue_delta=2,
    hunger_delta=1,
    weight=1.1
)

RELAX_AT_HOME = Action(
    name="Relax at Home",
    resulting_state=State.Leisure,
    duration_ticks=2,
    location_req=["home_a", "home_b", "home_c", "home_d", "home_e", "home_f", 
                  "home_g", "home_h", "home_i", "home_j", "home_k", "home_l"],
    fatigue_delta=-3,
    hunger_delta=2,
    weight=1.6
)

ENJOY_PARK = Action(
    name="Enjoy Time in Park",
    resulting_state=State.Leisure,
    duration_ticks=2,
    location_req=["public_park"],
    fatigue_delta=1,
    hunger_delta=2,
    allowed_moods=(-1, 2),
    weight=1.3
)

# ============================================================================
# ACTION DEFINITIONS - Shopping Actions
# ============================================================================

GROCERY_SHOPPING = Action(
    name="Grocery Shopping",
    resulting_state=State.Shopping,
    duration_ticks=3,
    location_req=["public_grocery_store"],
    fatigue_delta=5,
    hunger_delta=3,
    cash_delta=-40.0,
    weight=1.5
)

MALL_SHOPPING = Action(
    name="Mall Shopping",
    resulting_state=State.Shopping,
    duration_ticks=4,
    location_req=["public_mall"],
    fatigue_delta=6,
    hunger_delta=4,
    cash_delta=-60.0,
    allowed_moods=(0, 2),
    weight=1.2
)

QUICK_SHOPPING = Action(
    name="Quick Shopping",
    resulting_state=State.Shopping,
    duration_ticks=2,
    location_req=["public_grocery_store", "public_mall"],
    fatigue_delta=3,
    hunger_delta=2,
    cash_delta=-25.0,
    weight=1.4
)

WINDOW_SHOPPING = Action(
    name="Window Shopping",
    resulting_state=State.Shopping,
    duration_ticks=2,
    location_req=["public_mall"],
    fatigue_delta=4,
    hunger_delta=2,
    cash_delta=-5.0,
    weight=1.0
)

# ============================================================================
# ACTION DEFINITIONS - Meeting Actions
# ============================================================================

FORMAL_MEETING = Action(
    name="Attend Formal Meeting",
    resulting_state=State.In_Meeting,
    duration_ticks=3,
    location_req=["public_office"],
    fatigue_delta=4,
    hunger_delta=3,
    requires_presence="Any",
    allowed_moods=(-1, 2),
    weight=1.8
)

TEAM_MEETING = Action(
    name="Team Meeting",
    resulting_state=State.In_Meeting,
    duration_ticks=2,
    location_req=["public_office"],
    fatigue_delta=3,
    hunger_delta=2,
    requires_presence="Any",
    weight=1.6
)

CLIENT_MEETING = Action(
    name="Client Meeting",
    resulting_state=State.In_Meeting,
    duration_ticks=4,
    location_req=["public_office", "public_restaurant"],
    fatigue_delta=6,
    hunger_delta=4,
    cash_delta=-30.0,
    requires_presence="Specific",
    allowed_moods=(0, 2),
    weight=1.4
)

VIRTUAL_MEETING = Action(
    name="Virtual Meeting",
    resulting_state=State.In_Meeting,
    duration_ticks=2,
    location_req=["home_a", "home_b", "home_c", "home_d", "home_e", "home_f", "public_office"],
    fatigue_delta=3,
    hunger_delta=2,
    weight=1.5
)

# ============================================================================
# ACTION DEFINITIONS - Movement Actions
# ============================================================================

GO_TO_COFFEE_SHOP = Action(
    name="Go to Coffee Shop",
    resulting_state=State.Transitioning,
    duration_ticks=1,
    next_location="public_coffee_shop",
    fatigue_delta=2,
    weight=1.3
)

GO_TO_RESTAURANT = Action(
    name="Go to Restaurant",
    resulting_state=State.Transitioning,
    duration_ticks=1,
    next_location="public_restaurant",
    fatigue_delta=2,
    weight=1.2
)

GO_TO_MALL = Action(
    name="Go to Mall",
    resulting_state=State.Transitioning,
    duration_ticks=2,
    next_location="public_mall",
    fatigue_delta=3,
    weight=1.1
)

GO_TO_GYM = Action(
    name="Go to Gym",
    resulting_state=State.Transitioning,
    duration_ticks=1,
    next_location="public_gym",
    fatigue_delta=2,
    weight=1.2
)

GO_TO_LIBRARY = Action(
    name="Go to Library",
    resulting_state=State.Transitioning,
    duration_ticks=1,
    next_location="public_library",
    fatigue_delta=2,
    weight=1.0
)

GO_TO_CLINIC = Action(
    name="Go to Clinic",
    resulting_state=State.Transitioning,
    duration_ticks=2,
    next_location="public_clinic",
    fatigue_delta=3,
    allowed_moods=(-2, 1),
    weight=0.8
)

GO_TO_GATEWAY = Action(
    name="Go to Time Machine Gateway",
    resulting_state=State.Transitioning,
    duration_ticks=3,
    next_location="time_machine_gateway",
    fatigue_delta=5,
    allowed_moods=(0, 2),
    weight=0.5
)

# ============================================================================
# ACTION DEFINITIONS - Special Actions
# ============================================================================

TIME_JUMP = Action(
    name="Perform Time Jump",
    resulting_state=State.TimeJumping,
    duration_ticks=1,
    location_req=["time_machine_gateway"],
    fatigue_delta=20,
    hunger_delta=10,
    allowed_moods=(0, 2),
    weight=1.0  # Will be modified by gateway conditions
)

# ============================================================================
# ACTION REGISTRY
# ============================================================================

# Core state actions (Prompt 1 implementation)
CORE_ACTIONS: List[Action] = [
    GO_TO_SLEEP, WAKE_UP, STAY_IDLE, START_TRANSITION,
    DRIVE_TO_OFFICE, DRIVE_HOME, WALK_TO_PARK, WALK_TO_COFFEE_SHOP,
    START_WORK, EAT_MEAL, GRAB_SNACK,
]

# Extended actions (Prompt 2 - currently available but not fully integrated)
EXTENDED_ACTIONS: List[Action] = [
    # Commuting actions
    COMMUTE_BY_CAR, COMMUTE_WALKING, TAKE_BUS, RETURN_HOME_CAR,
    
    # Social actions
    MEET_COLLEAGUE, CHAT_WITH_FRIEND, ATTEND_SOCIAL_EVENT, NETWORK_EVENT,
    
    # Exercise actions
    GYM_WORKOUT, JOG_IN_PARK, HOME_EXERCISE, WALK_FOR_EXERCISE,
    
    # Leisure actions
    WATCH_MOVIE, READ_BOOK, BROWSE_LIBRARY, RELAX_AT_HOME, ENJOY_PARK,
    
    # Shopping actions
    GROCERY_SHOPPING, MALL_SHOPPING, QUICK_SHOPPING, WINDOW_SHOPPING,
    
    # Meeting actions
    FORMAL_MEETING, TEAM_MEETING, CLIENT_MEETING, VIRTUAL_MEETING,
    
    # Movement actions
    GO_TO_COFFEE_SHOP, GO_TO_RESTAURANT, GO_TO_MALL, GO_TO_GYM,
    GO_TO_LIBRARY, GO_TO_CLINIC, GO_TO_GATEWAY,
    
    # Special actions
    TIME_JUMP
]

# All actions combined
ALL_ACTIONS: List[Action] = CORE_ACTIONS + EXTENDED_ACTIONS

# Create lookup dictionaries for efficient access
ACTIONS_BY_NAME: Dict[str, Action] = {action.name: action for action in ALL_ACTIONS}
ACTIONS_BY_STATE: Dict[State, List[Action]] = {}

# Populate state lookup
for action in ALL_ACTIONS:
    if action.resulting_state not in ACTIONS_BY_STATE:
        ACTIONS_BY_STATE[action.resulting_state] = []
    ACTIONS_BY_STATE[action.resulting_state].append(action)

# Create core actions registry (only actions for implemented states)
CORE_ACTIONS_BY_STATE: Dict[State, List[Action]] = {}
for action in CORE_ACTIONS:
    if action.resulting_state not in CORE_ACTIONS_BY_STATE:
        CORE_ACTIONS_BY_STATE[action.resulting_state] = []
    CORE_ACTIONS_BY_STATE[action.resulting_state].append(action)


def get_action_registry() -> Dict[str, List[Action]]:
    """
    Get organized action registry by category.
    
    Returns:
        Dict mapping category names to action lists
    """
    return {
        'core': CORE_ACTIONS,
        'commuting': [COMMUTE_BY_CAR, COMMUTE_WALKING, TAKE_BUS, RETURN_HOME_CAR],
        'social': [MEET_COLLEAGUE, CHAT_WITH_FRIEND, ATTEND_SOCIAL_EVENT, NETWORK_EVENT],
        'exercise': [GYM_WORKOUT, JOG_IN_PARK, HOME_EXERCISE, WALK_FOR_EXERCISE],
        'leisure': [WATCH_MOVIE, READ_BOOK, BROWSE_LIBRARY, RELAX_AT_HOME, ENJOY_PARK],
        'shopping': [GROCERY_SHOPPING, MALL_SHOPPING, QUICK_SHOPPING, WINDOW_SHOPPING],
        'meetings': [FORMAL_MEETING, TEAM_MEETING, CLIENT_MEETING, VIRTUAL_MEETING],
        'movement': [GO_TO_COFFEE_SHOP, GO_TO_RESTAURANT, GO_TO_MALL, GO_TO_GYM,
                    GO_TO_LIBRARY, GO_TO_CLINIC, GO_TO_GATEWAY],
        'special': [TIME_JUMP]
    }


def get_available_actions(actor, world_state, core_only: bool = True) -> List[Action]:
    """
    Get all actions available to an actor based on their current state and conditions.
    
    Args:
        actor: The actor to get actions for
        world_state: Current world state
        core_only: If True, only return core actions (Prompt 1 states)
        
    Returns:
        List of actions the actor can perform
    """
    available = []
    action_pool = CORE_ACTIONS if core_only else ALL_ACTIONS
    
    for action in action_pool:
        # Check location requirements
        if action.location_req is not None:
            if actor.location_id not in action.location_req:
                continue
        
        # Check mood requirements
        if not (action.allowed_moods[0] <= actor.mood <= action.allowed_moods[1]):
            continue
        
        # Check if resource deltas would push values out of bounds
        new_hunger = actor.hunger + action.hunger_delta
        new_fatigue = actor.fatigue + action.fatigue_delta
        
        if not (0 <= new_hunger <= 100) or not (0 <= new_fatigue <= 100):
            continue
        
        # Check cash requirements
        if actor.cash + action.cash_delta < 0:
            continue
        
        # For core_only mode, skip actions that lead to unimplemented states
        if core_only:
            from .states import is_core_state
            if not is_core_state(action.resulting_state):
                continue
        
        available.append(action)
    
    return available


def lookup_forced(target_state: State, actor, core_only: bool = True) -> Optional[Action]:
    """
    Find an action that transitions to the target state for calendar enforcement.
    
    Args:
        target_state: The required state
        actor: The actor who needs to transition
        core_only: If True, only consider core actions
        
    Returns:
        Action that leads to the target state, or None if not possible
    """
    action_pool = CORE_ACTIONS_BY_STATE if core_only else ACTIONS_BY_STATE
    possible_actions = action_pool.get(target_state, [])
    
    for action in possible_actions:
        # Check basic requirements
        if action.location_req is not None:
            if actor.location_id not in action.location_req:
                continue
        
        # Check mood requirements
        if not (action.allowed_moods[0] <= actor.mood <= action.allowed_moods[1]):
            continue
        
        # Check resource bounds
        new_hunger = actor.hunger + action.hunger_delta
        new_fatigue = actor.fatigue + action.fatigue_delta
        
        if not (0 <= new_hunger <= 100) or not (0 <= new_fatigue <= 100):
            continue
        
        # Check cash
        if actor.cash + action.cash_delta < 0:
            continue
        
        return action
    
    return None


def apply_action(action: Action, actor, world_state) -> bool:
    """
    Apply an action's effects to an actor.
    
    Args:
        action: The action to apply
        actor: The actor performing the action
        world_state: Current world state
        
    Returns:
        bool: True if action was successfully applied
    """
    try:
        # Update actor state
        old_state = actor.state
        actor.state = action.resulting_state
        
        # Set descriptive substate
        action_name_clean = action.name.lower().replace(' ', '_').replace('-', '_')
        actor.substate = f"action_{action_name_clean}"
        
        # Update location if specified
        if action.next_location is not None:
            old_location = actor.location_id
            actor.location_id = action.next_location
            if old_location != action.next_location:
                # Log location change for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Actor {actor.name} moved from {old_location} to {action.next_location}")
        
        # Apply resource changes with bounds checking
        actor.update_resources(
            hunger_delta=action.hunger_delta,
            fatigue_delta=action.fatigue_delta,
            mood_delta=0  # Mood changes handled separately for now
        )
        
        # Update cash with bounds checking
        new_cash = actor.cash + action.cash_delta
        if new_cash < 0:
            # This should have been caught earlier, but safety check
            actor.cash = 0.0
        else:
            actor.cash = new_cash
        
        # Set action duration (subtract 1 because current tick counts)
        actor.current_ticks_left = max(0, action.duration_ticks - 1)
        
        return True
        
    except Exception as e:
        # Action failed - log error and don't change actor state
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to apply action {action.name} to actor {actor.name}: {e}")
        return False


def validate_action(action: Action) -> List[str]:
    """
    Validate an action definition for consistency.
    
    Args:
        action: The action to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check required fields
    if not action.name:
        errors.append("Action name is required")
    
    if action.duration_ticks < 1:
        errors.append(f"Duration must be at least 1 tick, got {action.duration_ticks}")
    
    if action.weight <= 0:
        errors.append(f"Weight must be positive, got {action.weight}")
    
    # Check mood range
    if not (-2 <= action.allowed_moods[0] <= action.allowed_moods[1] <= 2):
        errors.append(f"Invalid mood range: {action.allowed_moods}")
    
    # Check resource deltas are reasonable
    if abs(action.hunger_delta) > 50:
        errors.append(f"Hunger delta seems excessive: {action.hunger_delta}")
    
    if abs(action.fatigue_delta) > 50:
        errors.append(f"Fatigue delta seems excessive: {action.fatigue_delta}")
    
    return errors


def get_action_statistics() -> Dict[str, Any]:
    """
    Get statistics about the action registry.
    
    Returns:
        Dict containing action statistics
    """
    registry = get_action_registry()
    
    stats = {
        'total_actions': len(ALL_ACTIONS),
        'core_actions': len(CORE_ACTIONS),
        'extended_actions': len(EXTENDED_ACTIONS),
        'actions_by_category': {cat: len(actions) for cat, actions in registry.items()},
        'actions_by_state': {state.name: len(actions) for state, actions in ACTIONS_BY_STATE.items()},
        'average_duration': sum(action.duration_ticks for action in ALL_ACTIONS) / len(ALL_ACTIONS),
        'average_weight': sum(action.weight for action in ALL_ACTIONS) / len(ALL_ACTIONS)
    }
    
    return stats