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
from .world import initialize_world, create_sample_actor
from .tick_engine import advance_world, get_world_summary

# Prompt 2 additions
from .actions import Action, get_available_actions, apply_action
from .probability import choose_action, mood_factor, hunger_factor, fatigue_factor
from .time_jump import WorldManager, gateway_open, fork_world
from .calendar_scheduler import override_state
from .simulator import run, run_parallel_simulation, SimulationMetrics, SimulationLogger

__all__ = [
    # Core models and states
    "Actor",
    "Location", 
    "TimeBlock",
    "WorldClock",
    "WorldState",
    "State",
    "can_transition",
    
    # World management
    "initialize_world",
    "create_sample_actor",
    "advance_world",
    "get_world_summary",
    
    # Actions and probability (Prompt 2)
    "Action",
    "get_available_actions",
    "apply_action",
    "choose_action",
    "mood_factor",
    "hunger_factor", 
    "fatigue_factor",
    
    # Time jumping (Prompt 2)
    "WorldManager",
    "gateway_open",
    "fork_world",
    
    # Calendar scheduling (Prompt 2)
    "override_state",
    
    # Simulation (Prompt 2)
    "run",
    "run_parallel_simulation",
    "SimulationMetrics",
    "SimulationLogger",
]