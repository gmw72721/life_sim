"""
Time-jump and world-fork logic.

Implements world cloning/forking functionality, time-jump trigger detection,
multi-world synchronization, and timeline management.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from copy import deepcopy
import uuid

# Time jump configuration
TIME_JUMP_PROB = 0.02  # Base insertion weight for time jump actions


def gateway_open(actor, world_clock) -> bool:
    """
    Detect if an actor should trigger a time-jump based on gateway conditions.
    
    Args:
        actor: The actor to check for time-jump conditions
        world_clock: The world clock with current time
        
    Returns:
        bool: True if time-jump should be triggered
    """
    # Location requirement: must be at TimeMachineGateway
    loc_ok = actor.location_id == "time_machine_gateway"
    
    # Time requirement: early morning (6-8 AM) or late night (22+ PM)
    hour = world_clock.current_time.hour
    time_ok = (6 <= hour < 8) or (hour >= 22)
    
    # Mood requirement: must have positive or neutral mood
    mood_ok = actor.mood >= 0
    
    return loc_ok and time_ok and mood_ok


def calculate_time_jump_effects(actor, time_delta: timedelta) -> Dict[str, float]:
    """
    Calculate effects of time-jumping on an actor.
    
    Args:
        actor: The actor performing the time jump
        time_delta: How far in time the jump goes (positive = future, negative = past)
        
    Returns:
        Dict of resource changes to apply to the actor
    """
    # Base effects of time jumping
    effects = {
        "fatigue_delta": 15.0,  # Time jumping is tiring
        "hunger_delta": 8.0,    # Time jumping makes you hungry
        "mood_delta": -0.5,     # Disorientation penalty
        "energy_delta": -20.0,  # Drains energy
    }
    
    # Additional effects based on jump distance
    hours_jumped = abs(time_delta.total_seconds() / 3600)
    
    if hours_jumped > 24:
        # Long jumps are more disorienting
        effects["mood_delta"] -= 0.3
        effects["fatigue_delta"] += 10.0
    
    if time_delta.total_seconds() < 0:
        # Jumping to the past is more difficult
        effects["fatigue_delta"] += 5.0
        effects["mood_delta"] -= 0.2
    
    return effects


def fork_world(src_world, actor, target_time: datetime) -> 'WorldState':
    """
    Create a forked copy of the world for time-jumping.
    
    Args:
        src_world: The original world state to fork
        actor: The actor performing the time jump
        target_time: Target datetime for the jump
        
    Returns:
        New WorldState instance representing the forked timeline
    """
    # Create a deep copy of the world
    fork_id = f"{src_world.world_id}_fork_{uuid.uuid4().hex[:8]}"
    forked_world = deepcopy(src_world)
    
    # Update world ID
    forked_world.world_id = fork_id
    
    # Update all actors' world_id
    for forked_actor in forked_world.actors.values():
        forked_actor.world_id = fork_id
    
    # Adjust world clock to target time
    forked_world.clock.current_time = target_time
    
    # Find the jumping actor in the forked world
    jumping_actor = forked_world.actors.get(actor.id)
    if jumping_actor:
        # Apply time-jump effects
        time_delta = target_time - src_world.clock.current_time
        effects = calculate_time_jump_effects(jumping_actor, time_delta)
        
        jumping_actor.update_resources(
            hunger_delta=effects.get("hunger_delta", 0),
            fatigue_delta=effects.get("fatigue_delta", 0),
            mood_delta=effects.get("mood_delta", 0)
        )
        
        # Update energy if the actor has it
        if hasattr(jumping_actor, 'energy'):
            jumping_actor.energy = max(0.0, min(100.0, 
                jumping_actor.energy + effects.get("energy_delta", 0)))
        
        # Set actor state to indicate they just completed a time jump
        jumping_actor.state = State.Idle  # They arrive in idle state
        jumping_actor.substate = "post_time_jump"
    
    # Mark original actor as "Absent" (they've jumped to another timeline)
    actor.state = State.Idle  # Reset to idle
    actor.substate = "time_jumped_away"
    
    return forked_world


def synchronize_worlds(world_manager) -> None:
    """
    Synchronize multiple world timelines.
    
    Args:
        world_manager: Manager containing all active world forks
    """
    # Advance all worlds by one tick
    for world in world_manager.worlds.values():
        world.clock.advance_tick()
    
    # Update probability masses (simple decay for now)
    total_mass = sum(getattr(world, 'prob_mass', 1.0) for world in world_manager.worlds.values())
    
    if total_mass > 0:
        for world in world_manager.worlds.values():
            if not hasattr(world, 'prob_mass'):
                world.prob_mass = 1.0 / len(world_manager.worlds)
            # Simple decay - could be more sophisticated
            world.prob_mass *= 0.999


def get_timeline_divergence(world_a, world_b) -> float:
    """
    Calculate how much two timelines have diverged.
    
    Args:
        world_a: First world state
        world_b: Second world state
        
    Returns:
        float: Divergence score (0.0 = identical, 1.0 = completely different)
    """
    if world_a.world_id == world_b.world_id:
        return 0.0
    
    divergence_factors = []
    
    # Time difference
    time_diff = abs((world_a.clock.current_time - world_b.clock.current_time).total_seconds())
    time_divergence = min(1.0, time_diff / (24 * 3600))  # Normalize to days
    divergence_factors.append(time_divergence)
    
    # Actor state differences
    common_actors = set(world_a.actors.keys()) & set(world_b.actors.keys())
    if common_actors:
        state_differences = 0
        for actor_id in common_actors:
            actor_a = world_a.actors[actor_id]
            actor_b = world_b.actors[actor_id]
            
            # Compare states
            if actor_a.state != actor_b.state:
                state_differences += 1
            
            # Compare locations
            if actor_a.location_id != actor_b.location_id:
                state_differences += 1
            
            # Compare resource levels (normalized)
            resource_diff = (
                abs(actor_a.hunger - actor_b.hunger) +
                abs(actor_a.fatigue - actor_b.fatigue) +
                abs(actor_a.mood - actor_b.mood) * 50  # Scale mood to 0-100 range
            ) / 300.0  # Normalize
            
            state_differences += resource_diff
        
        state_divergence = min(1.0, state_differences / (len(common_actors) * 3))
        divergence_factors.append(state_divergence)
    
    # Return average divergence
    return sum(divergence_factors) / len(divergence_factors) if divergence_factors else 0.0


class WorldManager:
    """
    Manager for multiple world timelines.
    
    Handles active world tracking, fork creation and management,
    timeline pruning, and cross-world queries.
    """
    
    def __init__(self):
        """Initialize the world manager."""
        self.worlds: Dict[str, 'WorldState'] = {}
        self.active_forks: List[str] = []
        self.fork_history: Dict[str, List[str]] = {}
        self.main_world_id: Optional[str] = None
    
    def add_world(self, world) -> None:
        """
        Add a world to the manager.
        
        Args:
            world: The world state to add
        """
        self.worlds[world.world_id] = world
        
        # Set probability mass if not already set
        if not hasattr(world, 'prob_mass'):
            world.prob_mass = 1.0 if not self.worlds else 1.0 / len(self.worlds)
        
        # Track main world
        if self.main_world_id is None:
            self.main_world_id = world.world_id
        
        # Add to active forks if it's a fork
        if "_fork_" in world.world_id and world.world_id not in self.active_forks:
            self.active_forks.append(world.world_id)
    
    def remove_world(self, world_id: str) -> None:
        """
        Remove a world from the manager.
        
        Args:
            world_id: ID of the world to remove
        """
        if world_id in self.worlds:
            del self.worlds[world_id]
        
        if world_id in self.active_forks:
            self.active_forks.remove(world_id)
        
        if world_id in self.fork_history:
            del self.fork_history[world_id]
    
    def get_world(self, world_id: str):
        """
        Get a world by ID.
        
        Args:
            world_id: ID of the world to retrieve
            
        Returns:
            WorldState or None if not found
        """
        return self.worlds.get(world_id)
    
    def create_fork(self, source_world_id: str, actor, target_time: datetime) -> str:
        """
        Create a new world fork.
        
        Args:
            source_world_id: ID of the source world
            actor: Actor performing the time jump
            target_time: Target time for the fork
            
        Returns:
            str: ID of the new forked world
        """
        source_world = self.worlds.get(source_world_id)
        if not source_world:
            raise ValueError(f"Source world {source_world_id} not found")
        
        # Create the fork
        forked_world = fork_world(source_world, actor, target_time)
        
        # Add to manager
        self.add_world(forked_world)
        
        # Update probability masses
        if hasattr(source_world, 'prob_mass'):
            original_mass = source_world.prob_mass
            # Split probability mass
            source_world.prob_mass *= (1 - TIME_JUMP_PROB)
            forked_world.prob_mass = original_mass * TIME_JUMP_PROB
        
        # Track fork history
        if source_world_id not in self.fork_history:
            self.fork_history[source_world_id] = []
        self.fork_history[source_world_id].append(forked_world.world_id)
        
        return forked_world.world_id
    
    def advance_all_worlds(self) -> None:
        """Advance all managed worlds by one tick."""
        synchronize_worlds(self)
    
    def prune_inactive_forks(self, min_prob_mass: float = 0.001) -> List[str]:
        """
        Remove worlds with very low probability mass or no active time-jumpers.
        
        Args:
            min_prob_mass: Minimum probability mass to keep a world
            
        Returns:
            List of pruned world IDs
        """
        pruned = []
        
        for world_id in list(self.worlds.keys()):
            if world_id == self.main_world_id:
                continue  # Never prune main world
            
            world = self.worlds[world_id]
            
            # Check probability mass
            prob_mass = getattr(world, 'prob_mass', 1.0)
            if prob_mass < min_prob_mass:
                self.remove_world(world_id)
                pruned.append(world_id)
                continue
            
            # Check if any actors are still actively time-jumping
            has_active_jumpers = any(
                actor.substate and "time_jump" in actor.substate.lower()
                for actor in world.actors.values()
            )
            
            if not has_active_jumpers and len(self.worlds) > 3:
                # Keep at least 3 worlds, but prune inactive ones
                self.remove_world(world_id)
                pruned.append(world_id)
        
        return pruned
    
    def get_divergence_matrix(self) -> Dict[Tuple[str, str], float]:
        """
        Get divergence scores between all world pairs.
        
        Returns:
            Dict mapping world ID pairs to divergence scores
        """
        matrix = {}
        world_ids = list(self.worlds.keys())
        
        for i, world_a_id in enumerate(world_ids):
            for world_b_id in world_ids[i+1:]:
                world_a = self.worlds[world_a_id]
                world_b = self.worlds[world_b_id]
                divergence = get_timeline_divergence(world_a, world_b)
                matrix[(world_a_id, world_b_id)] = divergence
                matrix[(world_b_id, world_a_id)] = divergence  # Symmetric
        
        return matrix
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all managed worlds.
        
        Returns:
            Dict containing world manager statistics
        """
        return {
            "total_worlds": len(self.worlds),
            "active_forks": len(self.active_forks),
            "main_world": self.main_world_id,
            "world_ids": list(self.worlds.keys()),
            "total_actors": sum(len(world.actors) for world in self.worlds.values()),
            "probability_masses": {
                world_id: getattr(world, 'prob_mass', 1.0)
                for world_id, world in self.worlds.items()
            }
        }


# Import State here to avoid circular imports
from .states import State