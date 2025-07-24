"""
Time-jump and world-fork logic.

Implements world cloning/forking functionality, time-jump trigger detection,
multi-world synchronization, and timeline management.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from copy import deepcopy
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)

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
    try:
        # Location requirement: must be at TimeMachineGateway
        loc_ok = actor.location_id == "time_machine_gateway"
        
        # Time requirement: early morning (6-8 AM) or late night (22+ PM)
        hour = world_clock.current_time.hour
        time_ok = (6 <= hour < 8) or (hour >= 22)
        
        # Mood requirement: must have positive or neutral mood
        mood_ok = actor.mood >= 0
        
        # Resource requirements: not too tired or hungry
        resource_ok = actor.fatigue < 80 and actor.hunger < 70
        
        # Cash requirement: time jumping costs energy/resources
        cash_ok = actor.cash >= 50.0  # Minimum cost for time jump
        
        # Energy requirement: must have sufficient energy
        energy_ok = getattr(actor, 'energy', 100.0) >= 30.0
        
        # Additional edge case: coffee_left check (if actor has this attribute)
        coffee_ok = True
        if hasattr(actor, 'coffee_left'):
            coffee_ok = actor.coffee_left > 0
        
        # Battery level (for devices needed for time travel)
        battery_ok = getattr(actor, 'battery', 100.0) >= 20.0
        
        all_conditions = [loc_ok, time_ok, mood_ok, resource_ok, cash_ok, energy_ok, coffee_ok, battery_ok]
        gateway_is_open = all(all_conditions)
        
        if gateway_is_open:
            logger.debug(f"Gateway open for actor {actor.name}: all conditions met")
        else:
            failed_conditions = []
            if not loc_ok:
                failed_conditions.append("wrong location")
            if not time_ok:
                failed_conditions.append(f"wrong time ({hour}:00)")
            if not mood_ok:
                failed_conditions.append(f"bad mood ({actor.mood:.2f})")
            if not resource_ok:
                failed_conditions.append("too tired/hungry")
            if not cash_ok:
                failed_conditions.append("insufficient cash")
            if not energy_ok:
                failed_conditions.append("low energy")
            if not coffee_ok:
                failed_conditions.append("no coffee")
            if not battery_ok:
                failed_conditions.append("low battery")
            
            logger.debug(f"Gateway closed for actor {actor.name}: {', '.join(failed_conditions)}")
        
        return gateway_is_open
        
    except Exception as e:
        logger.error(f"Error checking gateway conditions for actor {actor.name}: {e}")
        return False


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
        "cash_delta": -50.0,    # Cost of time jumping
        "battery_delta": -10.0, # Drains device battery
    }
    
    # Additional effects based on jump distance
    hours_jumped = abs(time_delta.total_seconds() / 3600)
    
    if hours_jumped > 24:
        # Long jumps are more disorienting
        effects["mood_delta"] -= 0.3
        effects["fatigue_delta"] += 10.0
        effects["cash_delta"] -= 25.0  # Extra cost for long jumps
    
    if hours_jumped > 168:  # More than a week
        # Very long jumps are extremely taxing
        effects["mood_delta"] -= 0.5
        effects["fatigue_delta"] += 20.0
        effects["energy_delta"] -= 30.0
    
    if time_delta.total_seconds() < 0:
        # Jumping to the past is more difficult
        effects["fatigue_delta"] += 5.0
        effects["mood_delta"] -= 0.2
        effects["cash_delta"] -= 15.0  # Past jumps cost more
    
    # Ensure effects don't push resources out of bounds
    # This is a safety check - the actual clamping happens in update_resources
    logger.debug(f"Time jump effects for {hours_jumped:.1f} hour jump: {effects}")
    
    return effects


def fork_world(src_world: 'WorldState', actor: 'Actor', target_time: datetime) -> 'WorldState':
    """
    Create a forked copy of the world for time-jumping.
    
    Args:
        src_world: The original world state to fork
        actor: The actor performing the time jump
        target_time: Target datetime for the jump
        
    Returns:
        New WorldState instance representing the forked timeline
    """
    logger.info(f"Forking world {src_world.world_id} for actor {actor.name} jumping to {target_time}")
    
    try:
        # Create a deep copy of the world (this is expensive but necessary)
        fork_id = f"{src_world.world_id}_fork_{uuid.uuid4().hex[:8]}"
        
        # Pre-fork isolation: ensure we don't modify the original during copy
        logger.debug("Creating deep copy of world state...")
        forked_world = deepcopy(src_world)
        
        # Update world ID
        forked_world.world_id = fork_id
        
        # Update all actors' world_id to maintain consistency
        for forked_actor in forked_world.actors.values():
            forked_actor.world_id = fork_id
        
        # Adjust world clock to target time
        time_delta = target_time - src_world.clock.current_time
        forked_world.clock.current_time = target_time
        
        # Recalculate tick count based on new time
        # This is approximate - in a full implementation we'd track this more carefully
        hours_jumped = time_delta.total_seconds() / 3600
        ticks_jumped = int(hours_jumped * 4)  # 4 ticks per hour (15-minute ticks)
        forked_world.clock.tick_count = max(0, src_world.clock.tick_count + ticks_jumped)
        
        # Find the jumping actor in the forked world
        jumping_actor = forked_world.actors.get(actor.id)
        if jumping_actor:
            # Apply time-jump effects
            effects = calculate_time_jump_effects(jumping_actor, time_delta)
            
            # Apply resource changes with bounds checking
            jumping_actor.update_resources(
                hunger_delta=effects.get("hunger_delta", 0),
                fatigue_delta=effects.get("fatigue_delta", 0),
                mood_delta=effects.get("mood_delta", 0)
            )
            
            # Update other resources safely
            if "energy_delta" in effects:
                jumping_actor.energy = max(0.0, min(100.0, 
                    jumping_actor.energy + effects["energy_delta"]))
            
            if "cash_delta" in effects:
                jumping_actor.cash = max(0.0, jumping_actor.cash + effects["cash_delta"])
            
            if "battery_delta" in effects:
                jumping_actor.battery = max(0.0, min(100.0,
                    jumping_actor.battery + effects["battery_delta"]))
            
            # Set actor state to indicate they just completed a time jump
            from .states import State
            jumping_actor.state = State.Idle  # They arrive in idle state
            jumping_actor.substate = "post_time_jump"
            
            logger.info(f"Applied time jump effects to actor {jumping_actor.name} in forked world")
        else:
            logger.error(f"Could not find jumping actor {actor.id} in forked world")
        
        # Mark original actor as having jumped away (they're now in another timeline)
        actor.state = State.Idle  # Reset to idle
        actor.substate = "time_jumped_away"
        
        # Add probability mass tracking for the forked world
        forked_world.prob_mass = TIME_JUMP_PROB
        if hasattr(src_world, 'prob_mass'):
            src_world.prob_mass *= (1 - TIME_JUMP_PROB)
        else:
            src_world.prob_mass = 1 - TIME_JUMP_PROB
        
        logger.info(f"Successfully created forked world {fork_id}")
        return forked_world
        
    except Exception as e:
        logger.error(f"Failed to fork world: {e}")
        raise RuntimeError(f"World forking failed: {e}")


def synchronize_worlds(world_manager: 'WorldManager') -> None:
    """
    Synchronize multiple world timelines.
    
    Args:
        world_manager: Manager containing all active world forks
    """
    try:
        # Advance all worlds by one tick
        for world in world_manager.worlds.values():
            world.clock.advance_tick()
        
        # Update probability masses (simple decay for now)
        total_mass = sum(getattr(world, 'prob_mass', 1.0) for world in world_manager.worlds.values())
        
        if total_mass > 0:
            # Normalize probability masses
            for world in world_manager.worlds.values():
                if not hasattr(world, 'prob_mass'):
                    world.prob_mass = 1.0 / len(world_manager.worlds)
                # Simple decay - could be more sophisticated
                world.prob_mass *= 0.999
        
        # Log synchronization info periodically
        if len(world_manager.worlds) > 1:
            main_world = world_manager.get_world(world_manager.main_world_id)
            if main_world and main_world.clock.tick_count % 50 == 0:
                logger.debug(f"Synchronized {len(world_manager.worlds)} worlds at tick {main_world.clock.tick_count}")
    
    except Exception as e:
        logger.error(f"Error synchronizing worlds: {e}")


def get_timeline_divergence(world_a: 'WorldState', world_b: 'WorldState') -> float:
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
    
    try:
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
    
    except Exception as e:
        logger.error(f"Error calculating timeline divergence: {e}")
        return 1.0  # Assume maximum divergence on error


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
        logger.info("Initialized WorldManager")
    
    def add_world(self, world: 'WorldState') -> None:
        """
        Add a world to the manager.
        
        Args:
            world: The world state to add
        """
        self.worlds[world.world_id] = world
        
        # Set probability mass if not already set
        if not hasattr(world, 'prob_mass'):
            world.prob_mass = 1.0 if len(self.worlds) == 1 else 1.0 / len(self.worlds)
        
        # Track main world
        if self.main_world_id is None:
            self.main_world_id = world.world_id
            logger.info(f"Set main world: {world.world_id}")
        
        # Add to active forks if it's a fork
        if "_fork_" in world.world_id and world.world_id not in self.active_forks:
            self.active_forks.append(world.world_id)
            logger.debug(f"Added fork world: {world.world_id}")
    
    def remove_world(self, world_id: str) -> None:
        """
        Remove a world from the manager.
        
        Args:
            world_id: ID of the world to remove
        """
        if world_id in self.worlds:
            del self.worlds[world_id]
            logger.debug(f"Removed world: {world_id}")
        
        if world_id in self.active_forks:
            self.active_forks.remove(world_id)
        
        if world_id in self.fork_history:
            del self.fork_history[world_id]
    
    def get_world(self, world_id: str) -> Optional['WorldState']:
        """
        Get a world by ID.
        
        Args:
            world_id: ID of the world to retrieve
            
        Returns:
            WorldState or None if not found
        """
        return self.worlds.get(world_id)
    
    def create_fork(self, source_world_id: str, actor: 'Actor', target_time: datetime) -> str:
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
        
        logger.info(f"Created fork {forked_world.world_id} from {source_world_id}")
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
                logger.debug(f"Pruning world {world_id} due to low probability mass: {prob_mass}")
                self.remove_world(world_id)
                pruned.append(world_id)
                continue
            
            # Check if any actors are still actively time-jumping
            has_active_jumpers = any(
                actor.substate and "time_jump" in actor.substate.lower()
                for actor in world.actors.values()
            )
            
            # Keep at least 3 worlds, but prune inactive ones
            if not has_active_jumpers and len(self.worlds) > 3:
                logger.debug(f"Pruning inactive world {world_id}")
                self.remove_world(world_id)
                pruned.append(world_id)
        
        if pruned:
            logger.info(f"Pruned {len(pruned)} worlds: {pruned}")
        
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