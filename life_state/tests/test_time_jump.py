"""
Tests for time jump and world forking functionality.
"""

import pytest
from datetime import datetime, timedelta

from life_state.models import WorldState
from life_state.time_jump import (
    gateway_open, fork_world, calculate_time_jump_effects, 
    get_timeline_divergence, WorldManager
)
from life_state.world import initialize_world, create_sample_actor


class TestGatewayConditions:
    """Test time jump gateway conditions."""
    
    def test_gateway_open_correct_conditions(self):
        """Test gateway opens with correct conditions."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 7, 0))  # 7 AM
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Move actor to gateway
        actor.location_id = "time_machine_gateway"
        actor.mood = 0.5  # Positive mood
        
        assert gateway_open(actor, world.clock) is True
    
    def test_gateway_closed_wrong_location(self):
        """Test gateway closed when not at gateway location."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 7, 0))  # 7 AM
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Actor at home, not at gateway
        actor.mood = 0.5  # Positive mood
        
        assert gateway_open(actor, world.clock) is False
    
    def test_gateway_closed_wrong_time(self):
        """Test gateway closed at wrong time of day."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 15, 0))  # 3 PM
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Move actor to gateway
        actor.location_id = "time_machine_gateway"
        actor.mood = 0.5  # Positive mood
        
        assert gateway_open(actor, world.clock) is False
    
    def test_gateway_closed_negative_mood(self):
        """Test gateway closed with negative mood."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 7, 0))  # 7 AM
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Move actor to gateway
        actor.location_id = "time_machine_gateway"
        actor.mood = -0.5  # Negative mood
        
        assert gateway_open(actor, world.clock) is False


class TestTimeJumpEffects:
    """Test time jump effect calculations."""
    
    def test_basic_time_jump_effects(self):
        """Test basic time jump effects calculation."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # 2 hour jump forward
        time_delta = timedelta(hours=2)
        effects = calculate_time_jump_effects(actor, time_delta)
        
        assert "fatigue_delta" in effects
        assert "hunger_delta" in effects
        assert "mood_delta" in effects
        assert "energy_delta" in effects
        
        # Should have some penalty
        assert effects["fatigue_delta"] > 0
        assert effects["mood_delta"] < 0
    
    def test_long_jump_penalties(self):
        """Test that long jumps have additional penalties."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Short jump
        short_delta = timedelta(hours=2)
        short_effects = calculate_time_jump_effects(actor, short_delta)
        
        # Long jump
        long_delta = timedelta(hours=48)
        long_effects = calculate_time_jump_effects(actor, long_delta)
        
        # Long jump should have worse effects
        assert long_effects["fatigue_delta"] > short_effects["fatigue_delta"]
        assert long_effects["mood_delta"] < short_effects["mood_delta"]
    
    def test_backward_jump_penalties(self):
        """Test that backward jumps have additional penalties."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Forward jump
        forward_delta = timedelta(hours=6)
        forward_effects = calculate_time_jump_effects(actor, forward_delta)
        
        # Backward jump
        backward_delta = timedelta(hours=-6)
        backward_effects = calculate_time_jump_effects(actor, backward_delta)
        
        # Backward jump should be more difficult
        assert backward_effects["fatigue_delta"] > forward_effects["fatigue_delta"]
        assert backward_effects["mood_delta"] < forward_effects["mood_delta"]


class TestWorldForking:
    """Test world forking functionality."""
    
    def test_fork_world_creates_copy(self):
        """Test that forking creates a proper world copy."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        target_time = world.clock.current_time + timedelta(hours=6)
        forked_world = fork_world(world, actor, target_time)
        
        # Should be different world
        assert forked_world.world_id != world.world_id
        assert "_fork_" in forked_world.world_id
        
        # Should have same actors
        assert len(forked_world.actors) == len(world.actors)
        
        # Clock should be updated
        assert forked_world.clock.current_time == target_time
        
        # All actors should have updated world_id
        for forked_actor in forked_world.actors.values():
            assert forked_actor.world_id == forked_world.world_id
    
    def test_fork_world_applies_effects(self):
        """Test that forking applies time jump effects to the jumping actor."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        original_fatigue = actor.fatigue
        target_time = world.clock.current_time + timedelta(hours=6)
        
        forked_world = fork_world(world, actor, target_time)
        
        # Find the jumping actor in the forked world
        forked_actor = forked_world.actors[actor.id]
        
        # Should have applied time jump effects
        assert forked_actor.fatigue > original_fatigue
        assert forked_actor.substate == "post_time_jump"
        
        # Original actor should be marked as jumped away
        assert actor.substate == "time_jumped_away"


class TestTimelineDivergence:
    """Test timeline divergence calculations."""
    
    def test_identical_worlds_no_divergence(self):
        """Test that identical worlds have zero divergence."""
        world1 = initialize_world()
        create_sample_actor(world1, "Test Actor", "A")
        
        # Same world should have zero divergence
        divergence = get_timeline_divergence(world1, world1)
        assert divergence == 0.0
    
    def test_time_difference_creates_divergence(self):
        """Test that time differences create divergence."""
        world1 = initialize_world()
        actor1 = create_sample_actor(world1, "Test Actor", "A")
        
        world2 = initialize_world()
        actor2 = create_sample_actor(world2, "Test Actor", "A")
        
        # Advance world2 time
        world2.clock.current_time += timedelta(hours=12)
        
        divergence = get_timeline_divergence(world1, world2)
        assert divergence > 0.0
    
    def test_actor_state_differences_create_divergence(self):
        """Test that actor state differences create divergence."""
        world1 = initialize_world()
        actor1 = create_sample_actor(world1, "Test Actor", "A")
        
        world2 = initialize_world()
        actor2 = create_sample_actor(world2, "Test Actor", "A")
        
        # Change actor state in world2
        from life_state.states import State
        list(world2.actors.values())[0].state = State.Sleeping
        
        divergence = get_timeline_divergence(world1, world2)
        assert divergence > 0.0


class TestWorldManager:
    """Test world manager functionality."""
    
    def test_world_manager_initialization(self):
        """Test world manager initialization."""
        manager = WorldManager()
        
        assert len(manager.worlds) == 0
        assert len(manager.active_forks) == 0
        assert manager.main_world_id is None
    
    def test_add_world(self):
        """Test adding worlds to manager."""
        manager = WorldManager()
        world = initialize_world()
        
        manager.add_world(world)
        
        assert len(manager.worlds) == 1
        assert world.world_id in manager.worlds
        assert manager.main_world_id == world.world_id
    
    def test_create_fork(self):
        """Test creating world forks."""
        manager = WorldManager()
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        manager.add_world(world)
        
        target_time = world.clock.current_time + timedelta(hours=6)
        fork_id = manager.create_fork(world.world_id, actor, target_time)
        
        assert len(manager.worlds) == 2
        assert fork_id in manager.worlds
        assert fork_id != world.world_id
        assert fork_id in manager.active_forks
    
    def test_prune_inactive_forks(self):
        """Test pruning inactive forks."""
        manager = WorldManager()
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        manager.add_world(world)
        
        # Create a fork
        target_time = world.clock.current_time + timedelta(hours=6)
        fork_id = manager.create_fork(world.world_id, actor, target_time)
        
        # Set very low probability mass
        fork_world = manager.get_world(fork_id)
        fork_world.prob_mass = 0.0001
        
        # Prune should remove it
        pruned = manager.prune_inactive_forks(min_prob_mass=0.001)
        
        assert fork_id in pruned
        assert fork_id not in manager.worlds
    
    def test_get_summary(self):
        """Test getting world manager summary."""
        manager = WorldManager()
        world = initialize_world()
        create_sample_actor(world, "Test Actor", "A")
        
        manager.add_world(world)
        
        summary = manager.get_summary()
        
        assert "total_worlds" in summary
        assert "active_forks" in summary
        assert "main_world" in summary
        assert "total_actors" in summary
        
        assert summary["total_worlds"] == 1
        assert summary["total_actors"] == 11  # 10 from initialize_world + 1 from create_sample_actor
        assert summary["main_world"] == world.world_id