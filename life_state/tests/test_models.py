"""
Basic tests for life_state models.

Tests the core data structures and their basic functionality.
"""

import pytest
from datetime import datetime, timedelta

from life_state.models import (
    TimeBlock, Location, WorldClock, Actor, WorldState
)
from life_state.states import State
from life_state.world import initialize_world, create_sample_actor


class TestTimeBlock:
    """Test TimeBlock model functionality."""
    
    def test_time_block_creation(self):
        """Test creating a time block."""
        start = datetime(2024, 1, 1, 9, 0)
        end = datetime(2024, 1, 1, 10, 0)
        
        block = TimeBlock(
            start_dt=start,
            end_dt=end,
            required_state=State.Focused_Work,
            description="Morning work session"
        )
        
        assert block.start_dt == start
        assert block.end_dt == end
        assert block.required_state == State.Focused_Work
        assert block.description == "Morning work session"
    
    def test_duration_calculation(self):
        """Test duration calculation in minutes."""
        start = datetime(2024, 1, 1, 9, 0)
        end = datetime(2024, 1, 1, 10, 30)
        
        block = TimeBlock(
            start_dt=start,
            end_dt=end,
            required_state=State.Focused_Work
        )
        
        assert block.duration_minutes() == 90
    
    def test_overlap_detection(self):
        """Test time block overlap detection."""
        block1 = TimeBlock(
            start_dt=datetime(2024, 1, 1, 9, 0),
            end_dt=datetime(2024, 1, 1, 10, 0),
            required_state=State.Focused_Work
        )
        
        # Overlapping block
        block2 = TimeBlock(
            start_dt=datetime(2024, 1, 1, 9, 30),
            end_dt=datetime(2024, 1, 1, 10, 30),
            required_state=State.Eating
        )
        
        # Non-overlapping block
        block3 = TimeBlock(
            start_dt=datetime(2024, 1, 1, 10, 0),
            end_dt=datetime(2024, 1, 1, 11, 0),
            required_state=State.Eating
        )
        
        assert block1.overlaps_with(block2) is True
        assert block1.overlaps_with(block3) is False


class TestLocation:
    """Test Location model functionality."""
    
    def test_location_creation(self):
        """Test creating a location."""
        location = Location(
            id="test_office",
            name="Test Office",
            category="public"
        )
        
        assert location.id == "test_office"
        assert location.name == "Test Office"
        assert location.category == "public"
    
    def test_default_locations_creation(self):
        """Test creating the default set of locations."""
        locations = Location.create_default_locations()
        
        # Should have 14 public + 12 homes + 1 special = 27 total
        assert len(locations) == 27
        
        # Check we have the right categories
        public_count = sum(1 for loc in locations if loc.category == "public")
        home_count = sum(1 for loc in locations if loc.category == "home")
        special_count = sum(1 for loc in locations if loc.category == "special")
        
        assert public_count == 14
        assert home_count == 12
        assert special_count == 1
        
        # Check specific locations exist
        location_names = [loc.name for loc in locations]
        assert "Office" in location_names
        assert "Home-A" in location_names
        assert "TimeMachineGateway" in location_names


class TestWorldClock:
    """Test WorldClock functionality."""
    
    def test_clock_creation(self):
        """Test creating a world clock."""
        start_time = datetime(2024, 1, 1, 9, 0)
        clock = WorldClock(current_time=start_time)
        
        assert clock.current_time == start_time
        assert clock.tick_duration_minutes == 15
        assert clock.tick_count == 0
    
    def test_advance_tick(self):
        """Test advancing the clock by one tick."""
        start_time = datetime(2024, 1, 1, 9, 0)
        clock = WorldClock(current_time=start_time)
        
        clock.advance_tick()
        
        expected_time = start_time + timedelta(minutes=15)
        assert clock.current_time == expected_time
        assert clock.tick_count == 1
    
    def test_tick_time_methods(self):
        """Test tick start and end time methods."""
        start_time = datetime(2024, 1, 1, 9, 0)
        clock = WorldClock(current_time=start_time)
        
        assert clock.get_tick_start_time() == start_time
        assert clock.get_tick_end_time() == start_time + timedelta(minutes=15)


class TestActor:
    """Test Actor model functionality."""
    
    def test_actor_creation(self):
        """Test creating an actor."""
        actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a"
        )
        
        assert actor.name == "Test Actor"
        assert actor.home_id == "home_a"
        assert actor.location_id == "home_a"
        assert actor.state == State.Idle  # default
        assert actor.world_id == "main"  # default
        assert len(actor.id) > 0  # UUID should be generated
    
    def test_resource_updates(self):
        """Test updating actor resources."""
        actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a",
            hunger=50.0,
            fatigue=30.0,
            mood=0.0
        )
        
        actor.update_resources(hunger_delta=10.0, fatigue_delta=-5.0, mood_delta=0.5)
        
        assert actor.hunger == 60.0
        assert actor.fatigue == 25.0
        assert actor.mood == 0.5
    
    def test_resource_clamping(self):
        """Test that resources are clamped to valid ranges."""
        actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a",
            hunger=95.0,
            fatigue=5.0,
            mood=1.8
        )
        
        # Try to exceed limits
        actor.update_resources(hunger_delta=20.0, fatigue_delta=-10.0, mood_delta=1.0)
        
        assert actor.hunger == 100.0  # clamped to max
        assert actor.fatigue == 0.0   # clamped to min
        assert actor.mood == 2.0      # clamped to max
    
    def test_calendar_functionality(self):
        """Test actor calendar methods."""
        actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a"
        )
        
        # Add a time block
        block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 9, 0),
            end_dt=datetime(2024, 1, 1, 10, 0),
            required_state=State.Focused_Work
        )
        actor.calendar.append(block)
        
        # Test getting current time block
        current_time = datetime(2024, 1, 1, 9, 30)
        current_block = actor.get_current_time_block(current_time)
        assert current_block == block
        
        # Test availability check
        assert actor.is_available_at(
            datetime(2024, 1, 1, 8, 0),
            datetime(2024, 1, 1, 8, 30)
        ) is True
        
        assert actor.is_available_at(
            datetime(2024, 1, 1, 9, 30),
            datetime(2024, 1, 1, 10, 30)
        ) is False


class TestWorldState:
    """Test WorldState functionality."""
    
    def test_world_initialization(self):
        """Test initializing a world state."""
        world = initialize_world()
        
        assert world.world_id == "main"
        assert len(world.locations) == 27  # All default locations
        assert len(world.actors) == 0     # No actors initially
        assert world.clock.tick_count == 0
    
    def test_actor_management(self):
        """Test adding and managing actors in the world."""
        world = initialize_world()
        
        # Create and add an actor
        actor = create_sample_actor(world, "Test Actor", "A")
        
        assert len(world.actors) == 1
        assert actor.id in world.actors
        assert actor.world_id == world.world_id
        
        # Test getting actor
        retrieved_actor = world.get_actor(actor.id)
        assert retrieved_actor == actor
        
        # Test getting actors at location
        actors_at_home = world.get_actors_at_location("home_a")
        assert len(actors_at_home) == 1
        assert actors_at_home[0] == actor
        
        # Test getting actors in state
        idle_actors = world.get_actors_in_state(State.Idle)
        assert len(idle_actors) == 1
        assert idle_actors[0] == actor
    
    def test_location_access(self):
        """Test accessing locations in the world."""
        world = initialize_world()
        
        # Test getting a location
        office = world.get_location("public_office")
        assert office is not None
        assert office.name == "Office"
        
        # Test getting non-existent location
        fake_location = world.get_location("fake_location")
        assert fake_location is None


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_basic_simulation_setup(self):
        """Test setting up a basic simulation scenario."""
        # Initialize world
        world = initialize_world(
            start_time=datetime(2024, 1, 1, 9, 0),
            world_id="test_world"
        )
        
        # Create actors
        actor1 = create_sample_actor(world, "Alice", "A")
        actor2 = create_sample_actor(world, "Bob", "B")
        
        # Verify setup
        assert len(world.actors) == 2
        assert world.world_id == "test_world"
        assert world.clock.current_time == datetime(2024, 1, 1, 9, 0)
        
        # Both actors should be at their homes initially
        assert actor1.location_id == "home_a"
        assert actor2.location_id == "home_b"
        assert actor1.state == State.Idle
        assert actor2.state == State.Idle