#!/usr/bin/env python3
"""
Example script demonstrating the life_state foundation.

This shows how to use the core components implemented in Prompt 1.
Prompt 2 will add actions, probability, and time-jumping.
Prompt 3 will add the web API and React frontend.
"""

from datetime import datetime, timedelta
import time

from life_state import (
    initialize_world, create_sample_actor, advance_world, 
    get_world_summary, State
)


def main():
    """Demonstrate the basic life_state simulation."""
    print("🌍 Life State Simulation - Foundation Demo")
    print("=" * 50)
    
    # Initialize the world
    print("\n📍 Initializing world...")
    start_time = datetime(2024, 1, 1, 9, 0)  # 9 AM on New Year's Day
    world = initialize_world(start_time=start_time, world_id="demo_world")
    
    print(f"World created with {len(world.locations)} locations")
    print(f"Starting time: {world.clock.current_time}")
    
    # Create some actors
    print("\n👥 Creating actors...")
    alice = create_sample_actor(world, "Alice", "A")
    bob = create_sample_actor(world, "Bob", "B")
    charlie = create_sample_actor(world, "Charlie", "C")
    
    print(f"Created {len(world.actors)} actors:")
    for actor in world.actors.values():
        print(f"  - {actor.name} at {world.get_location(actor.location_id).name}")
    
    # Show initial state
    print("\n📊 Initial world summary:")
    summary = get_world_summary(world)
    print_summary(summary)
    
    # Run simulation for a few ticks
    print("\n⏰ Running simulation...")
    print("(Each tick = 15 minutes)")
    
    for tick in range(10):
        print(f"\n--- Tick {tick + 1} ---")
        advance_world(world)
        
        # Show what happened
        current_time = world.clock.current_time
        print(f"Time: {current_time.strftime('%H:%M')}")
        
        for actor in world.actors.values():
            location_name = world.get_location(actor.location_id).name
            print(f"  {actor.name}: {actor.state.name} at {location_name}")
            print(f"    Hunger: {actor.hunger:.1f}, Fatigue: {actor.fatigue:.1f}, Mood: {actor.mood:.1f}")
        
        # Brief pause for readability
        time.sleep(0.5)
    
    # Final summary
    print("\n📊 Final world summary:")
    final_summary = get_world_summary(world)
    print_summary(final_summary)
    
    print("\n✨ Foundation demo complete!")
    print("\nNext steps:")
    print("  • Prompt 2: Add actions, probability, and time-jumping")
    print("  • Prompt 3: Add FastAPI backend and React frontend")


def print_summary(summary):
    """Print a formatted world summary."""
    print(f"  Tick: {summary['tick']}")
    print(f"  Time: {summary['current_time']}")
    print(f"  Actors: {summary['total_actors']}")
    
    print("  State distribution:")
    for state_name, count in summary['state_distribution'].items():
        if count > 0:
            print(f"    {state_name}: {count}")
    
    print("  Average resources:")
    resources = summary['average_resources']
    print(f"    Hunger: {resources['hunger']}")
    print(f"    Fatigue: {resources['fatigue']}")
    print(f"    Mood: {resources['mood']}")


if __name__ == "__main__":
    main()