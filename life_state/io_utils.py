"""
I/O utilities for simulation logging and data persistence.

Handles writing simulation snapshots, daily summaries, and other output formats.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import logging

from .models import WorldState

# Configure logging
logger = logging.getLogger(__name__)


def write_snapshot(worlds: Dict[str, WorldState], log_dir: Path) -> None:
    """
    Write a snapshot of all worlds to JSON Lines format.
    
    Args:
        worlds: Dictionary of world_id -> WorldState
        log_dir: Directory to write snapshot files
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Ensure log directory is writable
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        logger.error(f"Cannot create log directory {log_dir}: {e}")
        return
    
    for world_id, world in worlds.items():
        snapshot_file = log_dir / f"{world_id}_snapshots.jsonl"
        
        # Create snapshot data
        snapshot = {
            "timestamp": timestamp,
            "world_id": world_id,
            "tick": world.clock.tick_count,
            "simulation_time": world.clock.current_time.isoformat(),
            "actors": []
        }
        
        # Add actor data
        for actor in world.actors.values():
            # Determine current action from substate or state
            current_action = "Idle"
            if actor.substate:
                if actor.substate.startswith("action_"):
                    current_action = actor.substate[7:].replace("_", " ").title()
                else:
                    current_action = actor.substate.replace("_", " ").title()
            else:
                current_action = actor.state.name
            
            actor_data = {
                "id": actor.id,
                "name": actor.name,
                "state": actor.state.name,
                "substate": actor.substate,
                "current_action": current_action,
                "location_id": actor.location_id,
                "hunger": round(actor.hunger, 2),
                "fatigue": round(actor.fatigue, 2),
                "mood": round(actor.mood, 2),
                "cash": round(actor.cash, 2),
                "energy": round(actor.energy, 2),
                "battery": round(actor.battery, 2),
                "current_ticks_left": actor.current_ticks_left,
                "world_id": actor.world_id
            }
            snapshot["actors"].append(actor_data)
        
        # Write to file with error handling and flushing
        try:
            with open(snapshot_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(snapshot, ensure_ascii=False) + '\n')
                f.flush()  # Ensure data is written immediately
        except (OSError, PermissionError) as e:
            logger.error(f"Cannot write to snapshot file {snapshot_file}: {e}")
        except (TypeError, ValueError) as e:
            logger.error(f"Error serializing snapshot data: {e}")


def write_daily_summary(world: WorldState, log_dir: Path) -> None:
    """
    Write a daily summary for a world at midnight.
    
    Args:
        world: The world state to summarize
        log_dir: Directory to write summary files
    """
    # Ensure log directory is writable
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        logger.error(f"Cannot create log directory {log_dir}: {e}")
        return
    
    date_str = world.clock.current_time.strftime("%Y-%m-%d")
    summary_file = log_dir / f"{world.world_id}_daily_{date_str}.json"
    
    # Calculate daily statistics
    total_actors = len(world.actors)
    
    # State distribution
    state_counts = {}
    for actor in world.actors.values():
        state_name = actor.state.name
        state_counts[state_name] = state_counts.get(state_name, 0) + 1
    
    # Resource averages
    if total_actors > 0:
        avg_hunger = sum(actor.hunger for actor in world.actors.values()) / total_actors
        avg_fatigue = sum(actor.fatigue for actor in world.actors.values()) / total_actors
        avg_mood = sum(actor.mood for actor in world.actors.values()) / total_actors
        avg_cash = sum(actor.cash for actor in world.actors.values()) / total_actors
        avg_energy = sum(actor.energy for actor in world.actors.values()) / total_actors
        avg_battery = sum(actor.battery for actor in world.actors.values()) / total_actors
    else:
        avg_hunger = avg_fatigue = avg_mood = avg_cash = avg_energy = avg_battery = 0.0
    
    # Location distribution
    location_counts = {}
    for actor in world.actors.values():
        location_counts[actor.location_id] = location_counts.get(actor.location_id, 0) + 1
    
    summary = {
        "date": date_str,
        "world_id": world.world_id,
        "total_actors": total_actors,
        "tick_count": world.clock.tick_count,
        "state_distribution": state_counts,
        "location_distribution": location_counts,
        "average_resources": {
            "hunger": round(avg_hunger, 2),
            "fatigue": round(avg_fatigue, 2),
            "mood": round(avg_mood, 2),
            "cash": round(avg_cash, 2),
            "energy": round(avg_energy, 2),
            "battery": round(avg_battery, 2)
        },
        "probability_mass": getattr(world, 'prob_mass', 1.0)
    }
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
            f.flush()
        logger.info(f"Wrote daily summary to {summary_file}")
    except (OSError, PermissionError) as e:
        logger.error(f"Cannot write daily summary to {summary_file}: {e}")
    except (TypeError, ValueError) as e:
        logger.error(f"Error serializing daily summary: {e}")


def write_simulation_summary(worlds: Dict[str, WorldState], metrics, log_dir: Path) -> None:
    """
    Write final simulation summary with metrics.
    
    Args:
        worlds: Dictionary of all worlds
        metrics: SimulationMetrics instance
        log_dir: Directory to write summary
    """
    # Ensure log directory is writable
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        logger.error(f"Cannot create log directory {log_dir}: {e}")
        return
    
    summary_file = log_dir / "simulation_summary.json"
    
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_worlds": len(worlds),
        "metrics": metrics.get_summary(),
        "worlds": {}
    }
    
    # Add per-world summaries
    for world_id, world in worlds.items():
        world_summary = {
            "world_id": world_id,
            "final_tick": world.clock.tick_count,
            "final_time": world.clock.current_time.isoformat(),
            "total_actors": len(world.actors),
            "probability_mass": getattr(world, 'prob_mass', 1.0)
        }
        
        # Actor summaries
        world_summary["actors"] = []
        for actor in world.actors.values():
            # Determine final action
            final_action = "Idle"
            if actor.substate:
                if actor.substate.startswith("action_"):
                    final_action = actor.substate[7:].replace("_", " ").title()
                else:
                    final_action = actor.substate.replace("_", " ").title()
            else:
                final_action = actor.state.name
            
            actor_summary = {
                "id": actor.id,
                "name": actor.name,
                "final_state": actor.state.name,
                "final_action": final_action,
                "final_location": actor.location_id,
                "final_resources": {
                    "hunger": round(actor.hunger, 2),
                    "fatigue": round(actor.fatigue, 2),
                    "mood": round(actor.mood, 2),
                    "cash": round(actor.cash, 2),
                    "energy": round(actor.energy, 2),
                    "battery": round(actor.battery, 2)
                }
            }
            world_summary["actors"].append(actor_summary)
        
        summary["worlds"][world_id] = world_summary
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
            f.flush()
        logger.info(f"Wrote simulation summary to {summary_file}")
    except (OSError, PermissionError) as e:
        logger.error(f"Cannot write simulation summary to {summary_file}: {e}")
    except (TypeError, ValueError) as e:
        logger.error(f"Error serializing simulation summary: {e}")


def load_snapshot(snapshot_file: Path) -> list:
    """
    Load snapshots from a JSON Lines file.
    
    Args:
        snapshot_file: Path to the snapshot file
        
    Returns:
        List of snapshot dictionaries
    """
    snapshots = []
    
    if not snapshot_file.exists():
        logger.warning(f"Snapshot file does not exist: {snapshot_file}")
        return snapshots
    
    try:
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        snapshots.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON on line {line_num} of {snapshot_file}: {e}")
        logger.debug(f"Loaded {len(snapshots)} snapshots from {snapshot_file}")
    except (OSError, PermissionError) as e:
        logger.error(f"Cannot read snapshot file {snapshot_file}: {e}")
    
    return snapshots


def export_csv(worlds: Dict[str, WorldState], log_dir: Path) -> None:
    """
    Export world data to CSV format for analysis.
    
    Args:
        worlds: Dictionary of worlds to export
        log_dir: Directory to write CSV files
    """
    import csv
    
    # Ensure log directory is writable
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        logger.error(f"Cannot create log directory {log_dir}: {e}")
        return
    
    for world_id, world in worlds.items():
        csv_file = log_dir / f"{world_id}_actors.csv"
        
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'actor_id', 'name', 'state', 'substate', 'current_action', 'location_id',
                    'hunger', 'fatigue', 'mood', 'cash', 'energy', 'battery',
                    'current_ticks_left', 'world_id'
                ])
                
                # Actor data
                for actor in world.actors.values():
                    # Determine current action
                    current_action = "Idle"
                    if actor.substate:
                        if actor.substate.startswith("action_"):
                            current_action = actor.substate[7:].replace("_", " ").title()
                        else:
                            current_action = actor.substate.replace("_", " ").title()
                    else:
                        current_action = actor.state.name
                    
                    writer.writerow([
                        actor.id, actor.name, actor.state.name, actor.substate,
                        current_action, actor.location_id, actor.hunger, actor.fatigue, actor.mood,
                        actor.cash, actor.energy, actor.battery, actor.current_ticks_left,
                        actor.world_id
                    ])
                
                f.flush()
            logger.info(f"Exported CSV data to {csv_file}")
        except (OSError, PermissionError) as e:
            logger.error(f"Cannot write CSV file {csv_file}: {e}")


def create_run_directory(base_dir: Path = None) -> Path:
    """
    Create a new run directory with timestamp.
    
    Args:
        base_dir: Base directory for runs (defaults to ./runs)
        
    Returns:
        Path to the created run directory
    """
    if base_dir is None:
        base_dir = Path("runs")
    
    try:
        base_dir.mkdir(exist_ok=True)
    except (OSError, PermissionError) as e:
        logger.error(f"Cannot create base directory {base_dir}: {e}")
        # Fallback to current directory
        base_dir = Path(".")
    
    # Create timestamped directory
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / f"run_{timestamp}"
    
    try:
        run_dir.mkdir(exist_ok=True)
        logger.info(f"Created run directory: {run_dir}")
    except (OSError, PermissionError) as e:
        logger.error(f"Cannot create run directory {run_dir}: {e}")
        # Fallback to base directory
        run_dir = base_dir
    
    return run_dir


def write_error_log(error_msg: str, log_dir: Path) -> None:
    """
    Write error messages to a dedicated error log file.
    
    Args:
        error_msg: Error message to log
        log_dir: Directory to write error log
    """
    error_file = log_dir / "errors.log"
    timestamp = datetime.utcnow().isoformat()
    
    try:
        with open(error_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {error_msg}\n")
            f.flush()
    except (OSError, PermissionError) as e:
        # If we can't write error logs, at least log to console
        logger.error(f"Cannot write to error log {error_file}: {e}")
        logger.error(f"Original error: {error_msg}")


def validate_log_directory(log_dir: Path) -> bool:
    """
    Validate that the log directory is writable.
    
    Args:
        log_dir: Directory to validate
        
    Returns:
        bool: True if directory is writable
    """
    try:
        # Try to create the directory
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to write a test file
        test_file = log_dir / "test_write.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
            f.flush()
        
        # Clean up test file
        test_file.unlink()
        
        return True
    except (OSError, PermissionError) as e:
        logger.error(f"Log directory {log_dir} is not writable: {e}")
        return False


def get_log_file_stats(log_dir: Path) -> Dict[str, Any]:
    """
    Get statistics about log files in the directory.
    
    Args:
        log_dir: Directory to analyze
        
    Returns:
        Dict containing log file statistics
    """
    stats = {
        "total_files": 0,
        "total_size_bytes": 0,
        "file_types": {},
        "largest_file": None,
        "oldest_file": None,
        "newest_file": None
    }
    
    if not log_dir.exists():
        return stats
    
    try:
        for file_path in log_dir.iterdir():
            if file_path.is_file():
                stats["total_files"] += 1
                file_size = file_path.stat().st_size
                stats["total_size_bytes"] += file_size
                
                # File type counting
                suffix = file_path.suffix
                stats["file_types"][suffix] = stats["file_types"].get(suffix, 0) + 1
                
                # Track largest file
                if stats["largest_file"] is None or file_size > stats["largest_file"][1]:
                    stats["largest_file"] = (str(file_path), file_size)
                
                # Track oldest and newest files
                mtime = file_path.stat().st_mtime
                if stats["oldest_file"] is None or mtime < stats["oldest_file"][1]:
                    stats["oldest_file"] = (str(file_path), mtime)
                if stats["newest_file"] is None or mtime > stats["newest_file"][1]:
                    stats["newest_file"] = (str(file_path), mtime)
    
    except (OSError, PermissionError) as e:
        logger.error(f"Error analyzing log directory {log_dir}: {e}")
    
    return stats