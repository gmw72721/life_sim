"""
life_state - A simulation framework for actor-based life modeling.

This is the foundation layer (Prompt 1) that establishes:
- Core data models and state management
- Basic time and location systems
- Hooks for future features (actions, probability, time-jumping)
"""

__version__ = "0.1.0"

from .models import Actor, Location, TimeBlock, WorldClock, WorldState
from .states import State, can_transition
from .world import initialize_world
from .tick_engine import advance_world

__all__ = [
    "Actor",
    "Location", 
    "TimeBlock",
    "WorldClock",
    "WorldState",
    "State",
    "can_transition",
    "initialize_world",
    "advance_world",
]