"""
I/O utilities for simulation logging and data persistence.

Handles writing simulation snapshots, daily summaries, and other output formats.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from .models import WorldState


def write_snapshot(worlds: Dict[str, WorldState], log_dir: Path) -> None:
    """
    Write a snapshot of all worlds to JSON Lines format.
    
    Args:
        worlds: Dictionary of world_id -> WorldState
        log_dir: Directory to write snapshot files
    """
    timestamp = datetime.utcnow().isoformat()
    
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
            actor_data = {
                "id": actor.id,
                "name": actor.name,
                "state": actor.state.name,
                "substate": actor.substate,
                "location_id": actor.location_id,
                "hunger": round(actor.hunger, 2),
                "fatigue": round(actor.fatigue, 2),
                "mood": round(actor.mood, 2),
                "cash": round(actor.cash, 2),
                "energy": round(actor.energy, 2),
                "battery": round(actor.battery, 2),
                "current_ticks_left": actor.current_ticks_left
            }
            snapshot["actors"].append(actor_data)
        
        # Append to file
        with open(snapshot_file, 'a') as f:
            f.write(json.dumps(snapshot) + '\n')


def write_daily_summary(world: WorldState, log_dir: Path) -> None:
    """
    Write a daily summary for a world at midnight.
    
    Args:
        world: The world state to summarize
        log_dir: Directory to write summary files
    """
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
    else:
        avg_hunger = avg_fatigue = avg_mood = avg_cash = 0.0
    
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
            "cash": round(avg_cash, 2)
        }
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)


def write_simulation_summary(worlds: Dict[str, WorldState], metrics, log_dir: Path) -> None:
    """
    Write final simulation summary with metrics.
    
    Args:
        worlds: Dictionary of all worlds
        metrics: SimulationMetrics instance
        log_dir: Directory to write summary
    """
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
            actor_summary = {
                "id": actor.id,
                "name": actor.name,
                "final_state": actor.state.name,
                "final_location": actor.location_id,
                "final_resources": {
                    "hunger": round(actor.hunger, 2),
                    "fatigue": round(actor.fatigue, 2),
                    "mood": round(actor.mood, 2),
                    "cash": round(actor.cash, 2)
                }
            }
            world_summary["actors"].append(actor_summary)
        
        summary["worlds"][world_id] = world_summary
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)


def load_snapshot(snapshot_file: Path) -> list:
    """
    Load snapshots from a JSON Lines file.
    
    Args:
        snapshot_file: Path to the snapshot file
        
    Returns:
        List of snapshot dictionaries
    """
    snapshots = []
    
    if snapshot_file.exists():
        with open(snapshot_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    snapshots.append(json.loads(line))
    
    return snapshots


def export_csv(worlds: Dict[str, WorldState], log_dir: Path) -> None:
    """
    Export world data to CSV format for analysis.
    
    Args:
        worlds: Dictionary of worlds to export
        log_dir: Directory to write CSV files
    """
    import csv
    
    for world_id, world in worlds.items():
        csv_file = log_dir / f"{world_id}_actors.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'actor_id', 'name', 'state', 'substate', 'location_id',
                'hunger', 'fatigue', 'mood', 'cash', 'energy', 'battery',
                'current_ticks_left', 'world_id'
            ])
            
            # Actor data
            for actor in world.actors.values():
                writer.writerow([
                    actor.id, actor.name, actor.state.name, actor.substate,
                    actor.location_id, actor.hunger, actor.fatigue, actor.mood,
                    actor.cash, actor.energy, actor.battery, actor.current_ticks_left,
                    actor.world_id
                ])


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
    
    base_dir.mkdir(exist_ok=True)
    
    # Create timestamped directory
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / f"run_{timestamp}"
    run_dir.mkdir(exist_ok=True)
    
    return run_dir