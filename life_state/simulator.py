"""
Master simulation loop and orchestration.

Implements the main simulation loop with action/probability integration,
multi-world simulation coordination, performance monitoring, and event logging.

TODO: integrate live WebSocket broadcasting in Prompt 3
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import time
import json
import logging

from . import actions, probability, calendar_scheduler
from .time_jump import WorldManager
from .actions import TIME_JUMP
from .models import WorldState
from .states import State

# Configure logging
logger = logging.getLogger(__name__)


def run(worlds: Dict[str, WorldState], 
        end_dt: datetime, 
        log_dir: Path,
        tick_callback: Optional[Callable[[Dict[str, WorldState]], None]] = None) -> None:
    """
    Run the main simulation loop across multiple worlds.
    
    Args:
        worlds: Dictionary of world_id -> WorldState
        end_dt: End datetime for simulation
        log_dir: Directory to write log files
        tick_callback: Optional callback function called after each tick
    """
    from . import io_utils
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize metrics and logging
    metrics = SimulationMetrics()
    logger_sim = SimulationLogger()
    
    metrics.start_tracking()
    
    logger.info(f"Starting simulation with {len(worlds)} worlds until {end_dt}")
    
    # Main simulation loop
    tick_count = 0
    while worlds:  # Continue while there are active worlds
        tick_start = time.time()
        
        # Process each world
        finished_worlds = []
        for world_id, world in worlds.items():
            if world.clock.current_time >= end_dt:
                finished_worlds.append(world_id)
                continue
            
            logger.debug(f"Processing world {world_id} at tick {world.clock.tick_count}")
            
            # Process each actor in the world
            for actor in list(world.actors.values()):
                if actor.current_ticks_left > 0:
                    # Actor is still busy with previous action
                    actor.current_ticks_left -= 1
                    logger.debug(f"Actor {actor.name} busy for {actor.current_ticks_left} more ticks")
                else:
                    # Actor is ready for a new action
                    process_actor_action(actor, world, logger_sim)
            
            # Advance world clock
            world.clock.advance_tick()
            
            # Record metrics
            metrics.record_tick(world)
        
        # Remove finished worlds
        for world_id in finished_worlds:
            logger.info(f"World {world_id} finished at {worlds[world_id].clock.current_time}")
            del worlds[world_id]
        
        # Write snapshot for remaining worlds
        if worlds:
            io_utils.write_snapshot(worlds, log_dir)
        
        # Call tick callback if provided
        if tick_callback:
            tick_callback(worlds)
        
        # Performance tracking
        tick_duration = time.time() - tick_start
        metrics.performance_samples.append(tick_duration)
        
        # Prune old performance samples (keep last 100)
        if len(metrics.performance_samples) > 100:
            metrics.performance_samples = metrics.performance_samples[-100:]
        
        tick_count += 1
        
        # Log progress periodically
        if tick_count % 50 == 0:
            logger.info(f"Completed {tick_count} ticks, {len(worlds)} worlds remaining")
    
    logger.info(f"Simulation completed after {tick_count} ticks")
    
    # Write final summary
    io_utils.write_simulation_summary(worlds, metrics, log_dir)


def process_actor_action(actor, world: WorldState, logger_sim: 'SimulationLogger') -> None:
    """
    Process action selection and execution for a single actor.
    
    Args:
        actor: The actor to process
        world: The world state
        logger_sim: Event logger
    """
    # Check for calendar override first
    forced_state = calendar_scheduler.override_state(actor, world.clock)
    
    if forced_state:
        # Calendar requires a specific state
        action = actions.lookup_forced(forced_state, actor, core_only=True)
        if action:
            logger_sim.log_action(actor, action, True, "calendar_forced")
            success = actions.apply_action(action, actor, world)
            if not success:
                logger_sim.log_action(actor, action, False, "action_failed")
        else:
            # No valid action for forced state, stay idle
            old_state = actor.state
            actor.state = State.Idle
            actor.substate = "calendar_conflict"
            logger_sim.log_state_change(actor, old_state, State.Idle, "calendar_conflict")
    else:
        # Normal probability-based action selection
        chosen_action = probability.choose_action(actor, world, core_only=True)
        
        if chosen_action:
            # Handle special time jump action
            if chosen_action == TIME_JUMP:
                handle_time_jump(actor, world, logger_sim)
            else:
                # Apply normal action
                logger_sim.log_action(actor, chosen_action, True, "probability_selected")
                success = actions.apply_action(chosen_action, actor, world)
                if not success:
                    logger_sim.log_action(actor, chosen_action, False, "action_failed")
                    # Fallback to idle
                    old_state = actor.state
                    actor.state = State.Idle
                    actor.substate = "action_failed"
                    logger_sim.log_state_change(actor, old_state, State.Idle, "action_failed")
        else:
            # No valid actions available, stay idle
            if actor.state != State.Idle:
                old_state = actor.state
                actor.state = State.Idle
                actor.substate = "no_actions_available"
                logger_sim.log_state_change(actor, old_state, State.Idle, "no_actions")


def handle_time_jump(actor, world: WorldState, logger_sim: 'SimulationLogger') -> None:
    """
    Handle time jump action execution.
    
    Args:
        actor: The actor performing the time jump
        world: The current world state
        logger_sim: Event logger
    """
    # Calculate target time (random jump between 1 hour and 24 hours)
    import random
    
    # 70% chance of jumping forward, 30% chance of jumping backward
    if random.random() < 0.7:
        # Jump forward
        hours_jump = random.randint(1, 24)
        target_time = world.clock.current_time + timedelta(hours=hours_jump)
    else:
        # Jump backward
        hours_jump = random.randint(1, 12)  # Shorter backward jumps
        target_time = world.clock.current_time - timedelta(hours=hours_jump)
    
    # Create world fork (this would need access to WorldManager)
    # For now, just apply time jump effects and change state
    from .time_jump import calculate_time_jump_effects
    
    time_delta = target_time - world.clock.current_time
    effects = calculate_time_jump_effects(actor, time_delta)
    
    # Apply effects
    actor.update_resources(
        hunger_delta=effects.get("hunger_delta", 0),
        fatigue_delta=effects.get("fatigue_delta", 0),
        mood_delta=effects.get("mood_delta", 0)
    )
    
    # Update energy if available
    if hasattr(actor, 'energy'):
        actor.energy = max(0.0, min(100.0, 
            actor.energy + effects.get("energy_delta", 0)))
    
    # Update cash and battery
    if "cash_delta" in effects:
        actor.cash = max(0.0, actor.cash + effects["cash_delta"])
    
    if "battery_delta" in effects:
        actor.battery = max(0.0, min(100.0,
            actor.battery + effects["battery_delta"]))
    
    # Set state
    actor.state = State.Idle
    actor.substate = "post_time_jump"
    
    logger_sim.log_time_jump(actor, world.world_id, f"{world.world_id}_hypothetical_fork")


def run_parallel_simulation(world_manager: WorldManager, 
                          num_ticks: int = 100,
                          tick_callback: Optional[Callable[[WorldManager], None]] = None) -> None:
    """
    Run simulation across multiple world timelines using WorldManager.
    
    Args:
        world_manager: Manager containing all world forks
        num_ticks: Number of ticks to simulate
        tick_callback: Optional callback after each tick
    """
    import random
    
    logger.info(f"Starting parallel simulation for {num_ticks} ticks")
    
    for tick in range(num_ticks):
        # Process all worlds
        for world in world_manager.worlds.values():
            for actor in list(world.actors.values()):
                if actor.current_ticks_left > 0:
                    actor.current_ticks_left -= 1
                else:
                    # Process actor action (simplified version)
                    chosen_action = probability.choose_action(actor, world, core_only=False)
                    if chosen_action:
                        if chosen_action == TIME_JUMP:
                            # Create actual world fork
                            target_time = world.clock.current_time + timedelta(hours=random.randint(1, 24))
                            try:
                                new_world_id = world_manager.create_fork(world.world_id, actor, target_time)
                                logger.info(f"Created time jump fork: {new_world_id}")
                            except Exception as e:
                                logger.error(f"Failed to create fork: {e}")
                        else:
                            actions.apply_action(chosen_action, actor, world)
        
        # Advance all worlds
        world_manager.advance_all_worlds()
        
        # Prune inactive forks periodically
        if tick % 50 == 0:
            pruned = world_manager.prune_inactive_forks()
            if pruned:
                logger.info(f"Pruned {len(pruned)} inactive forks")
        
        # Call callback
        if tick_callback:
            tick_callback(world_manager)
    
    logger.info(f"Parallel simulation completed after {num_ticks} ticks")


def simulate_until_condition(world_state: WorldState, 
                           condition_func: Callable[[WorldState], bool], 
                           max_ticks: int = 1000) -> int:
    """
    Run simulation until a condition is met.
    
    Args:
        world_state: Initial world state
        condition_func: Function that returns True when simulation should stop
        max_ticks: Maximum ticks to prevent infinite loops
        
    Returns:
        int: Number of ticks that were simulated
    """
    tick_count = 0
    
    logger.info(f"Running simulation until condition met (max {max_ticks} ticks)")
    
    while tick_count < max_ticks:
        # Check condition
        if condition_func(world_state):
            logger.info(f"Condition met after {tick_count} ticks")
            break
        
        # Process one tick
        for actor in list(world_state.actors.values()):
            if actor.current_ticks_left > 0:
                actor.current_ticks_left -= 1
            else:
                chosen_action = probability.choose_action(actor, world_state, core_only=True)
                if chosen_action and chosen_action != TIME_JUMP:
                    actions.apply_action(chosen_action, actor, world_state)
        
        world_state.clock.advance_tick()
        tick_count += 1
    
    if tick_count >= max_ticks:
        logger.warning(f"Simulation stopped at max_ticks limit: {max_ticks}")
    
    return tick_count


class SimulationMetrics:
    """
    Performance and state metrics tracking.
    
    Tracks ticks per second, actor state distributions over time,
    resource usage patterns, action frequency statistics, and memory usage.
    """
    
    def __init__(self):
        """Initialize metrics tracking."""
        self.start_time: Optional[datetime] = None
        self.tick_count: int = 0
        self.state_history: List[Dict[str, Any]] = []
        self.action_counts: Dict[str, int] = {}
        self.performance_samples: List[float] = []
        self.resource_history: List[Dict[str, float]] = []
        self.world_history: List[Dict[str, Any]] = []
    
    def start_tracking(self) -> None:
        """Start metrics collection."""
        self.start_time = datetime.utcnow()
        self.tick_count = 0
        self.state_history.clear()
        self.action_counts.clear()
        self.performance_samples.clear()
        self.resource_history.clear()
        self.world_history.clear()
        logger.debug("Started metrics tracking")
    
    def record_tick(self, world_state: WorldState) -> None:
        """
        Record metrics for a completed tick.
        
        Args:
            world_state: The world state to record metrics for
        """
        self.tick_count += 1
        
        # Record state distribution
        state_counts = {}
        for state in State:
            count = len(world_state.get_actors_in_state(state))
            if count > 0:
                state_counts[state.name] = count
        
        self.state_history.append({
            'tick': self.tick_count,
            'time': world_state.clock.current_time.isoformat(),
            'world_id': world_state.world_id,
            'states': state_counts
        })
        
        # Record average resources
        if world_state.actors:
            avg_hunger = sum(a.hunger for a in world_state.actors.values()) / len(world_state.actors)
            avg_fatigue = sum(a.fatigue for a in world_state.actors.values()) / len(world_state.actors)
            avg_mood = sum(a.mood for a in world_state.actors.values()) / len(world_state.actors)
            avg_cash = sum(a.cash for a in world_state.actors.values()) / len(world_state.actors)
            
            self.resource_history.append({
                'tick': self.tick_count,
                'world_id': world_state.world_id,
                'hunger': avg_hunger,
                'fatigue': avg_fatigue,
                'mood': avg_mood,
                'cash': avg_cash
            })
        
        # Record world-specific metrics
        self.world_history.append({
            'tick': self.tick_count,
            'world_id': world_state.world_id,
            'actor_count': len(world_state.actors),
            'prob_mass': getattr(world_state, 'prob_mass', 1.0)
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of collected metrics.
        
        Returns:
            Dict containing summary statistics
        """
        if not self.start_time:
            return {}
        
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        ticks_per_second = self.tick_count / elapsed if elapsed > 0 else 0
        
        avg_tick_time = sum(self.performance_samples) / len(self.performance_samples) if self.performance_samples else 0
        
        return {
            'total_ticks': self.tick_count,
            'elapsed_seconds': elapsed,
            'ticks_per_second': ticks_per_second,
            'average_tick_time': avg_tick_time,
            'action_counts': self.action_counts.copy(),
            'state_transitions': len(self.state_history),
            'resource_samples': len(self.resource_history),
            'worlds_tracked': len(set(entry['world_id'] for entry in self.world_history))
        }


class SimulationLogger:
    """
    Event logging and debugging support.
    
    Handles action execution logging, state transition logging,
    error and exception tracking, and debug output formatting.
    """
    
    def __init__(self, log_level: str = "INFO"):
        """Initialize logging system."""
        self.log_level = log_level
        self.events: List[Dict[str, Any]] = []
    
    def log_action(self, actor, action, result: bool, reason: str = "") -> None:
        """
        Log an action execution.
        
        Args:
            actor: The actor performing the action
            action: The action being performed
            result: Whether the action succeeded
            reason: Reason for the action selection or failure
        """
        current_action = action.name if action else "None"
        
        self.events.append({
            'type': 'action',
            'timestamp': datetime.utcnow().isoformat(),
            'actor_id': actor.id,
            'actor_name': actor.name,
            'action_name': action.name if action else "None",
            'current_action': current_action,
            'success': result,
            'reason': reason,
            'world_id': actor.world_id,
            'location_id': actor.location_id,
            'state': actor.state.name,
            'substate': actor.substate
        })
    
    def log_state_change(self, actor, old_state: State, new_state: State, reason: str = "") -> None:
        """
        Log a state transition.
        
        Args:
            actor: The actor changing state
            old_state: Previous state
            new_state: New state
            reason: Reason for the state change
        """
        self.events.append({
            'type': 'state_change',
            'timestamp': datetime.utcnow().isoformat(),
            'actor_id': actor.id,
            'actor_name': actor.name,
            'old_state': old_state.name,
            'new_state': new_state.name,
            'reason': reason,
            'world_id': actor.world_id,
            'location_id': actor.location_id,
            'current_action': getattr(actor, 'current_action', 'None')
        })
    
    def log_time_jump(self, actor, source_world_id: str, target_world_id: str) -> None:
        """
        Log a time-jump event.
        
        Args:
            actor: The actor performing the time jump
            source_world_id: ID of the source world
            target_world_id: ID of the target world
        """
        self.events.append({
            'type': 'time_jump',
            'timestamp': datetime.utcnow().isoformat(),
            'actor_id': actor.id,
            'actor_name': actor.name,
            'source_world': source_world_id,
            'target_world': target_world_id,
            'current_action': 'TIME_JUMP',
            'location_id': actor.location_id
        })
    
    def get_events(self, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get logged events, optionally filtered by type.
        
        Args:
            filter_type: Optional event type to filter by
            
        Returns:
            List of matching events
        """
        if filter_type:
            return [e for e in self.events if e.get('type') == filter_type]
        return self.events.copy()


def create_simulation_config() -> Dict[str, Any]:
    """
    Create default simulation configuration.
    
    Returns:
        Dict containing simulation parameters
    """
    return {
        'tick_rate': 15,  # minutes per tick
        'max_worlds': 10,  # maximum concurrent world forks
        'prune_threshold': 0.001,  # minimum probability mass to keep world
        'log_level': 'INFO',
        'performance_monitoring': True,
        'time_jump_probability': 0.02,
        'calendar_enforcement': True,
        'resource_constraints': True,
        'core_actions_only': True  # Only use Prompt 1 actions by default
    }


def validate_simulation_state(world_state: WorldState) -> List[str]:
    """
    Validate world state for consistency.
    
    Args:
        world_state: World state to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check all actors have valid locations
    for actor in world_state.actors.values():
        if actor.location_id not in world_state.locations:
            errors.append(f"Actor {actor.name} at invalid location {actor.location_id}")
    
    # Check resource bounds
    for actor in world_state.actors.values():
        if not (0 <= actor.hunger <= 100):
            errors.append(f"Actor {actor.name} has invalid hunger: {actor.hunger}")
        if not (0 <= actor.fatigue <= 100):
            errors.append(f"Actor {actor.name} has invalid fatigue: {actor.fatigue}")
        if not (-2 <= actor.mood <= 2):
            errors.append(f"Actor {actor.name} has invalid mood: {actor.mood}")
        if actor.cash < 0:
            errors.append(f"Actor {actor.name} has negative cash: {actor.cash}")
    
    # Check calendar consistency
    for actor in world_state.actors.values():
        for i, block in enumerate(actor.calendar):
            if block.start_dt >= block.end_dt:
                errors.append(f"Actor {actor.name} has invalid time block {i}: start >= end")
    
    # Check world consistency
    if not world_state.world_id:
        errors.append("World missing world_id")
    
    if not world_state.clock:
        errors.append("World missing clock")
    
    return errors