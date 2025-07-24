"""
Command-line interface for life_state simulation.

Provides argparse wrapper for running simulations with various options.

Example usage:
    python -m life_state.cli --minutes 1440 --log ./runs/run_001
    python -m life_state.cli --actors 5 --ticks 100 --world-forks
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from . import initialize_world, create_sample_actor
from .simulator import run, run_parallel_simulation, create_simulation_config
from .time_jump import WorldManager
from .io_utils import create_run_directory


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        if args.command == 'run':
            run_simulation(args)
        elif args.command == 'parallel':
            run_parallel_simulation_cli(args)
        elif args.command == 'config':
            show_config()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def create_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Life State Simulation - Actor-based life modeling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run --minutes 1440 --actors 3
  %(prog)s run --ticks 100 --log ./my_run
  %(prog)s parallel --actors 5 --ticks 200
  %(prog)s config
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run single-world simulation')
    run_parser.add_argument(
        '--minutes', type=int, default=1440,
        help='Duration in simulation minutes (default: 1440 = 24 hours)'
    )
    run_parser.add_argument(
        '--ticks', type=int,
        help='Duration in ticks (overrides --minutes if specified)'
    )
    run_parser.add_argument(
        '--actors', type=int, default=3,
        help='Number of actors to create (default: 3)'
    )
    run_parser.add_argument(
        '--log', type=str,
        help='Log directory path (default: auto-generated)'
    )
    run_parser.add_argument(
        '--start-time', type=str,
        help='Start time in ISO format (default: current time)'
    )
    run_parser.add_argument(
        '--world-id', type=str, default='main',
        help='World identifier (default: main)'
    )
    run_parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose output'
    )
    
    # Parallel command
    parallel_parser = subparsers.add_parser('parallel', help='Run multi-world simulation')
    parallel_parser.add_argument(
        '--ticks', type=int, default=100,
        help='Number of ticks to simulate (default: 100)'
    )
    parallel_parser.add_argument(
        '--actors', type=int, default=3,
        help='Number of actors to create (default: 3)'
    )
    parallel_parser.add_argument(
        '--max-worlds', type=int, default=10,
        help='Maximum number of concurrent worlds (default: 10)'
    )
    parallel_parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose output'
    )
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show configuration')
    
    return parser


def run_simulation(args):
    """Run a single-world simulation."""
    print("🌍 Life State Simulation - Single World")
    print("=" * 50)
    
    # Parse start time
    if args.start_time:
        try:
            start_time = datetime.fromisoformat(args.start_time)
        except ValueError:
            print(f"Invalid start time format: {args.start_time}")
            print("Use ISO format like: 2024-01-01T09:00:00")
            return
    else:
        start_time = datetime.utcnow()
    
    # Calculate end time
    if args.ticks:
        end_time = start_time + timedelta(minutes=args.ticks * 15)
        print(f"Running for {args.ticks} ticks ({args.ticks * 15} minutes)")
    else:
        end_time = start_time + timedelta(minutes=args.minutes)
        print(f"Running for {args.minutes} simulation minutes")
    
    # Create log directory
    if args.log:
        log_dir = Path(args.log)
        log_dir.mkdir(parents=True, exist_ok=True)
    else:
        log_dir = create_run_directory()
    
    print(f"Logging to: {log_dir}")
    
    # Initialize world
    print(f"\n📍 Initializing world '{args.world_id}'...")
    world = initialize_world(start_time=start_time, world_id=args.world_id)
    
    # Create actors
    print(f"👥 Creating {args.actors} actors...")
    actor_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
    home_letters = "ABCDEFGHIJKL"
    
    for i in range(args.actors):
        name = actor_names[i % len(actor_names)]
        if i >= len(actor_names):
            name = f"{name}{i // len(actor_names) + 1}"
        
        home_letter = home_letters[i % len(home_letters)]
        actor = create_sample_actor(world, name, home_letter)
        
        if args.verbose:
            print(f"  Created {actor.name} at {world.get_location(actor.location_id).name}")
    
    print(f"Created {len(world.actors)} actors in world with {len(world.locations)} locations")
    
    # Setup callback for verbose output
    def tick_callback(worlds):
        if args.verbose and world.clock.tick_count % 10 == 0:
            print(f"Tick {world.clock.tick_count}: {world.clock.current_time.strftime('%Y-%m-%d %H:%M')}")
    
    # Run simulation
    print(f"\n⏰ Starting simulation...")
    print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    worlds = {args.world_id: world}
    
    try:
        run(worlds, end_time, log_dir, tick_callback if args.verbose else None)
        
        print(f"\n✅ Simulation completed!")
        print(f"Final tick: {world.clock.tick_count}")
        print(f"Final time: {world.clock.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Logs written to: {log_dir}")
        
        # Show final actor states
        print(f"\n📊 Final Actor States:")
        for actor in world.actors.values():
            location_name = world.get_location(actor.location_id).name
            print(f"  {actor.name}: {actor.state.name} at {location_name}")
            print(f"    Resources: H={actor.hunger:.1f} F={actor.fatigue:.1f} M={actor.mood:.1f}")
        
    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        raise


def run_parallel_simulation_cli(args):
    """Run a multi-world simulation."""
    print("🌍 Life State Simulation - Multi-World")
    print("=" * 50)
    
    # Initialize world manager
    world_manager = WorldManager()
    
    # Create initial world
    start_time = datetime.utcnow()
    world = initialize_world(start_time=start_time, world_id="main")
    
    # Create actors
    print(f"👥 Creating {args.actors} actors...")
    actor_names = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
    home_letters = "ABCDEFGHIJKL"
    
    for i in range(args.actors):
        name = actor_names[i % len(actor_names)]
        if i >= len(actor_names):
            name = f"{name}{i // len(actor_names) + 1}"
        
        home_letter = home_letters[i % len(home_letters)]
        create_sample_actor(world, name, home_letter)
    
    # Add to world manager
    world_manager.add_world(world)
    
    print(f"Created {len(world.actors)} actors")
    print(f"Max concurrent worlds: {args.max_worlds}")
    
    # Setup callback for verbose output
    def tick_callback(manager):
        if args.verbose and len(manager.worlds) > 0:
            main_world = manager.get_world("main")
            if main_world and main_world.clock.tick_count % 20 == 0:
                summary = manager.get_summary()
                print(f"Tick {main_world.clock.tick_count}: {summary['total_worlds']} worlds, "
                      f"{summary['total_actors']} total actors")
    
    # Run simulation
    print(f"\n⏰ Starting parallel simulation for {args.ticks} ticks...")
    
    try:
        run_parallel_simulation(world_manager, args.ticks, tick_callback if args.verbose else None)
        
        print(f"\n✅ Parallel simulation completed!")
        
        # Show final summary
        summary = world_manager.get_summary()
        print(f"\nFinal Summary:")
        print(f"  Total worlds: {summary['total_worlds']}")
        print(f"  Active forks: {summary['active_forks']}")
        print(f"  Total actors: {summary['total_actors']}")
        
        print(f"\nWorld Details:")
        for world_id in summary['world_ids']:
            world = world_manager.get_world(world_id)
            prob_mass = getattr(world, 'prob_mass', 1.0)
            print(f"  {world_id}: {len(world.actors)} actors, prob={prob_mass:.3f}")
        
    except Exception as e:
        print(f"\n❌ Parallel simulation failed: {e}")
        raise


def show_config():
    """Show current configuration."""
    print("🔧 Life State Simulation Configuration")
    print("=" * 50)
    
    config = create_simulation_config()
    
    for key, value in config.items():
        print(f"{key}: {value}")


if __name__ == '__main__':
    main()