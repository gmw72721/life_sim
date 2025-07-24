"""
Tests for core data models.

Tests model validation, resource bounds, and world state management.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from life_state.models import Actor, WorldState, WorldClock, Location, TimeBlock
from life_state.states import State


class TestActor:
    """Test Actor model validation and functionality."""
    
    def test_actor_creation_with_defaults(self):
        """Test creating an actor with default values."""
        actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="test_world"
        )
        
        assert actor.name == "Test Actor"
        assert actor.home_id == "home_a"
        assert actor.location_id == "home_a"
        assert actor.world_id == "test_world"
        assert actor.state == State.Idle
        assert actor.hunger == 20.0
        assert actor.fatigue == 20.0
        assert actor.mood == 0.0
        assert actor.cash == 1000.0
        assert actor.energy == 100.0
        assert actor.battery == 100.0
    
    def test_actor_resource_validation_bounds(self):
        """Test that actor resources are validated within bounds."""
        # Valid resources should work
        actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="test_world",
            hunger=50.0,
            fatigue=75.0,
            mood=1.5
        )
        assert actor.hunger == 50.0
        assert actor.fatigue == 75.0
        assert actor.mood == 1.5
    
    def test_actor_hunger_out_of_bounds(self):
        """Test that out-of-range hunger values are rejected."""
        with pytest.raises(ValidationError):
            Actor(
                name="Test Actor",
                home_id="home_a",
                location_id="home_a",
                world_id="test_world",
                hunger=150.0  # Out of bounds
            )
        
        with pytest.raises(ValidationError):
            Actor(
                name="Test Actor",
                home_id="home_a",
                location_id="home_a",
                world_id="test_world",
                hunger=-10.0  # Out of bounds
            )
    
    def test_actor_fatigue_out_of_bounds(self):
        """Test that out-of-range fatigue values are rejected."""
        with pytest.raises(ValidationError):
            Actor(
                name="Test Actor",
                home_id="home_a",
                location_id="home_a",
                world_id="test_world",
                fatigue=150.0  # Out of bounds
            )
        
        with pytest.raises(ValidationError):
            Actor(
                name="Test Actor",
                home_id="home_a",
                location_id="home_a",
                world_id="test_world",
                fatigue=-5.0  # Out of bounds
            )
    
    def test_actor_mood_out_of_bounds(self):
        """Test that out-of-range mood values are rejected."""
        with pytest.raises(ValidationError):
            Actor(
                name="Test Actor",
                home_id="home_a",
                location_id="home_a",
                world_id="test_world",
                mood=3.0  # Out of bounds
            )
        
        with pytest.raises(ValidationError):
            Actor(
                name="Test Actor",
                home_id="home_a",
                location_id="home_a",
                world_id="test_world",
                mood=-3.0  # Out of bounds
            )
    
    def test_actor_update_resources_clamping(self):
        """Test that update_resources properly clamps values to bounds."""
        actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="test_world",
            hunger=50.0,
            fatigue=50.0,
            mood=0.0
        )
        
        # Test clamping to upper bounds
        actor.update_resources(hunger_delta=100.0, fatigue_delta=100.0, mood_delta=5.0)
        assert actor.hunger == 100.0  # Clamped to max
        assert actor.fatigue == 100.0  # Clamped to max
        assert actor.mood == 2.0  # Clamped to max
        
        # Test clamping to lower bounds
        actor.update_resources(hunger_delta=-200.0, fatigue_delta=-200.0, mood_delta=-10.0)
        assert actor.hunger == 0.0  # Clamped to min
        assert actor.fatigue == 0.0  # Clamped to min
        assert actor.mood == -2.0  # Clamped to min
    
    def test_actor_world_id_required(self):
        """Test that world_id is required for actors."""
        actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="test_world"
        )
        assert actor.world_id == "test_world"


class TestTimeBlock:
    """Test TimeBlock model validation."""
    
    def test_timeblock_creation(self):
        """Test creating a valid time block."""
        start_time = datetime(2024, 1, 1, 9, 0)
        end_time = datetime(2024, 1, 1, 17, 0)
        
        block = TimeBlock(
            start_dt=start_time,
            end_dt=end_time,
            required_state=State.Focused_Work,
            description="Work day"
        )
        
        assert block.start_dt == start_time
        assert block.end_dt == end_time
        assert block.required_state == State.Focused_Work
        assert block.description == "Work day"
        assert block.duration_minutes() == 480  # 8 hours
    
    def test_timeblock_end_before_start_validation(self):
        """Test that end_dt must be after start_dt."""
        start_time = datetime(2024, 1, 1, 17, 0)
        end_time = datetime(2024, 1, 1, 9, 0)  # Before start
        
        with pytest.raises(ValidationError):
            TimeBlock(
                start_dt=start_time,
                end_dt=end_time,
                required_state=State.Focused_Work
            )
    
    def test_timeblock_overlaps_with(self):
        """Test time block overlap detection."""
        block1 = TimeBlock(
            start_dt=datetime(2024, 1, 1, 9, 0),
            end_dt=datetime(2024, 1, 1, 12, 0),
            required_state=State.Focused_Work
        )
        
        # Overlapping block
        block2 = TimeBlock(
            start_dt=datetime(2024, 1, 1, 11, 0),
            end_dt=datetime(2024, 1, 1, 14, 0),
            required_state=State.Eating
        )
        
        # Non-overlapping block
        block3 = TimeBlock(
            start_dt=datetime(2024, 1, 1, 13, 0),
            end_dt=datetime(2024, 1, 1, 16, 0),
            required_state=State.Leisure
        )
        
        assert block1.overlaps_with(block2)
        assert block2.overlaps_with(block1)
        assert not block1.overlaps_with(block3)
        assert not block3.overlaps_with(block1)


class TestWorldClock:
    """Test WorldClock model validation."""
    
    def test_worldclock_creation(self):
        """Test creating a world clock."""
        start_time = datetime(2024, 1, 1, 9, 0)
        clock = WorldClock(current_time=start_time)
        
        assert clock.current_time == start_time
        assert clock.tick_duration_minutes == 15
        assert clock.tick_count == 0
    
    def test_worldclock_advance_tick(self):
        """Test advancing the world clock."""
        start_time = datetime(2024, 1, 1, 9, 0)
        clock = WorldClock(current_time=start_time)
        
        clock.advance_tick()
        
        assert clock.current_time == datetime(2024, 1, 1, 9, 15)
        assert clock.tick_count == 1
        
        clock.advance_tick()
        
        assert clock.current_time == datetime(2024, 1, 1, 9, 30)
        assert clock.tick_count == 2
    
    def test_worldclock_tick_duration_validation(self):
        """Test that tick duration is validated."""
        start_time = datetime(2024, 1, 1, 9, 0)
        
        # Valid duration
        clock = WorldClock(current_time=start_time, tick_duration_minutes=30)
        assert clock.tick_duration_minutes == 30
        
        # Invalid durations
        with pytest.raises(ValidationError):
            WorldClock(current_time=start_time, tick_duration_minutes=0)
        
        with pytest.raises(ValidationError):
            WorldClock(current_time=start_time, tick_duration_minutes=120)


class TestWorldState:
    """Test WorldState model and functionality."""
    
    def test_worldstate_creation(self):
        """Test creating a world state."""
        clock = WorldClock(current_time=datetime(2024, 1, 1, 9, 0))
        world = WorldState(clock=clock, world_id="test_world")
        
        assert world.world_id == "test_world"
        assert world.clock == clock
        assert len(world.actors) == 0
        assert len(world.locations) == 0
    
    def test_worldstate_add_actor(self):
        """Test adding an actor to the world."""
        clock = WorldClock(current_time=datetime(2024, 1, 1, 9, 0))
        world = WorldState(clock=clock, world_id="test_world")
        
        actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="different_world"  # Will be overridden
        )
        
        world.add_actor(actor)
        
        assert len(world.actors) == 1
        assert actor.id in world.actors
        assert actor.world_id == "test_world"  # Should be updated
    
    def test_worldstate_remove_actor(self):
        """Test removing an actor from the world."""
        clock = WorldClock(current_time=datetime(2024, 1, 1, 9, 0))
        world = WorldState(clock=clock, world_id="test_world")
        
        actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="test_world"
        )
        
        world.add_actor(actor)
        assert len(world.actors) == 1
        
        # Remove actor
        result = world.remove_actor(actor.id)
        assert result is True
        assert len(world.actors) == 0
        
        # Try to remove non-existent actor
        result = world.remove_actor("non_existent")
        assert result is False
    
    def test_worldstate_get_actors_at_location(self):
        """Test getting actors at a specific location."""
        clock = WorldClock(current_time=datetime(2024, 1, 1, 9, 0))
        world = WorldState(clock=clock, world_id="test_world")
        
        actor1 = Actor(name="Actor1", home_id="home_a", location_id="home_a", world_id="test_world")
        actor2 = Actor(name="Actor2", home_id="home_b", location_id="home_a", world_id="test_world")
        actor3 = Actor(name="Actor3", home_id="home_c", location_id="public_office", world_id="test_world")
        
        world.add_actor(actor1)
        world.add_actor(actor2)
        world.add_actor(actor3)
        
        actors_at_home_a = world.get_actors_at_location("home_a")
        assert len(actors_at_home_a) == 2
        assert actor1 in actors_at_home_a
        assert actor2 in actors_at_home_a
        
        actors_at_office = world.get_actors_at_location("public_office")
        assert len(actors_at_office) == 1
        assert actor3 in actors_at_office
    
    def test_worldstate_get_actors_in_state(self):
        """Test getting actors in a specific state."""
        clock = WorldClock(current_time=datetime(2024, 1, 1, 9, 0))
        world = WorldState(clock=clock, world_id="test_world")
        
        actor1 = Actor(name="Actor1", home_id="home_a", location_id="home_a", 
                      world_id="test_world", state=State.Idle)
        actor2 = Actor(name="Actor2", home_id="home_b", location_id="home_b", 
                      world_id="test_world", state=State.Sleeping)
        actor3 = Actor(name="Actor3", home_id="home_c", location_id="home_c", 
                      world_id="test_world", state=State.Idle)
        
        world.add_actor(actor1)
        world.add_actor(actor2)
        world.add_actor(actor3)
        
        idle_actors = world.get_actors_in_state(State.Idle)
        assert len(idle_actors) == 2
        assert actor1 in idle_actors
        assert actor3 in idle_actors
        
        sleeping_actors = world.get_actors_in_state(State.Sleeping)
        assert len(sleeping_actors) == 1
        assert actor2 in sleeping_actors


class TestLocation:
    """Test Location model functionality."""
    
    def test_location_creation(self):
        """Test creating a location."""
        location = Location(
            id="test_location",
            name="Test Location",
            category="test"
        )
        
        assert location.id == "test_location"
        assert location.name == "Test Location"
        assert location.category == "test"
    
    def test_create_default_locations(self):
        """Test creating the default set of locations."""
        locations = Location.create_default_locations()
        
        # Should have 14 public + 12 home + 1 special = 27 locations
        assert len(locations) == 27
        
        # Check categories
        public_locations = [loc for loc in locations if loc.category == "public"]
        home_locations = [loc for loc in locations if loc.category == "home"]
        special_locations = [loc for loc in locations if loc.category == "special"]
        
        assert len(public_locations) == 14
        assert len(home_locations) == 12
        assert len(special_locations) == 1
        
        # Check specific locations exist
        location_ids = [loc.id for loc in locations]
        assert "public_office" in location_ids
        assert "home_a" in location_ids
        assert "time_machine_gateway" in location_ids