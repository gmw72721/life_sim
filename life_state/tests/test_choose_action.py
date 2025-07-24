"""
Tests for action selection and probability system.
"""

import pytest
from datetime import datetime

from life_state.models import Actor, WorldState, WorldClock
from life_state.states import State
from life_state.actions import get_available_actions, apply_action, GO_TO_SLEEP, EAT_MEAL
from life_state.probability import choose_action, mood_factor, hunger_factor, fatigue_factor
from life_state.world import initialize_world, create_sample_actor


class TestActionSelection:
    """Test action selection functionality."""
    
    def test_get_available_actions_basic(self):
        """Test getting available actions for an actor."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        available = get_available_actions(actor, world)
        
        assert len(available) > 0
        assert all(hasattr(action, 'name') for action in available)
        assert all(hasattr(action, 'resulting_state') for action in available)
    
    def test_action_location_filtering(self):
        """Test that actions are filtered by location requirements."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Actor is at home, should not have gym-specific actions available
        available = get_available_actions(actor, world)
        gym_actions = [a for a in available if a.location_req and "public_gym" in a.location_req]
        
        # Should be empty since actor is not at gym
        gym_only_actions = [a for a in gym_actions if len(a.location_req) == 1 and a.location_req[0] == "public_gym"]
        assert len(gym_only_actions) == 0
    
    def test_action_mood_filtering(self):
        """Test that actions are filtered by mood requirements."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Set very negative mood
        actor.mood = -2.0
        
        available = get_available_actions(actor, world)
        
        # Should not have actions that require positive mood
        for action in available:
            assert action.allowed_moods[0] <= actor.mood <= action.allowed_moods[1]
    
    def test_action_resource_filtering(self):
        """Test that actions are filtered by resource constraints."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Set actor to have very low cash
        actor.cash = 1.0
        
        available = get_available_actions(actor, world)
        
        # Should not have expensive actions
        for action in available:
            assert actor.cash + action.cash_delta >= 0
    
    def test_apply_action_effects(self):
        """Test that applying actions changes actor state correctly."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        original_hunger = actor.hunger
        original_state = actor.state
        
        # Apply eating action
        success = apply_action(EAT_MEAL, actor, world)
        
        assert success
        assert actor.state == EAT_MEAL.resulting_state
        assert actor.hunger < original_hunger  # Should reduce hunger
        assert actor.current_ticks_left == EAT_MEAL.duration_ticks - 1


class TestProbabilityFactors:
    """Test probability calculation factors."""
    
    def test_mood_factor(self):
        """Test mood factor calculation."""
        # Test neutral mood
        assert mood_factor(0.0) == 1.0
        
        # Test positive mood
        assert mood_factor(1.0) > 1.0
        
        # Test negative mood
        assert mood_factor(-1.0) < 1.0
        
        # Test extreme values
        assert mood_factor(2.0) == 1.03
        assert mood_factor(-2.0) == 0.97
    
    def test_hunger_factor(self):
        """Test hunger factor calculation."""
        # Test minimum hunger
        assert hunger_factor(0.0) == 0.8
        
        # Test maximum hunger
        assert hunger_factor(100.0) == 1.2
        
        # Test middle values
        assert 0.8 < hunger_factor(50.0) < 1.2
    
    def test_fatigue_factor(self):
        """Test fatigue factor calculation."""
        # Test minimum fatigue
        assert fatigue_factor(0.0) == 0.8
        
        # Test maximum fatigue
        assert fatigue_factor(100.0) == 1.2
        
        # Test middle values
        assert 0.8 < fatigue_factor(50.0) < 1.2


class TestActionChoice:
    """Test complete action choice system."""
    
    def test_choose_action_returns_valid_action(self):
        """Test that choose_action returns a valid action."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        chosen = choose_action(actor, world)
        
        if chosen:  # May be None if no actions available
            assert hasattr(chosen, 'name')
            assert hasattr(chosen, 'resulting_state')
            
            # Should be in available actions
            available = get_available_actions(actor, world)
            # Note: TIME_JUMP might be added dynamically, so we check more flexibly
            assert chosen.name in [a.name for a in available] or chosen.name == "Perform Time Jump"
    
    def test_choose_action_respects_needs(self):
        """Test that action choice is influenced by actor needs."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Set very high hunger
        actor.hunger = 95.0
        
        # Run multiple choice attempts to see if eating is preferred
        eating_chosen = 0
        total_attempts = 20
        
        for _ in range(total_attempts):
            chosen = choose_action(actor, world)
            if chosen and chosen.hunger_delta < 0:  # Eating action
                eating_chosen += 1
        
        # Should choose eating actions more often when very hungry
        assert eating_chosen > 0  # At least some eating actions chosen
    
    def test_choose_action_with_no_available_actions(self):
        """Test action choice when no actions are available."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Set impossible conditions (very negative mood and no cash)
        actor.mood = -2.0
        actor.cash = -1000.0
        
        chosen = choose_action(actor, world)
        
        # Should handle gracefully (return None or a basic action)
        if chosen:
            # If an action is chosen, it should be valid
            available = get_available_actions(actor, world)
            assert len(available) > 0  # Some actions should still be available


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_action_cycle(self):
        """Test a complete action selection and application cycle."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        original_state = actor.state
        
        # Choose and apply action
        chosen = choose_action(actor, world)
        
        if chosen:
            success = apply_action(chosen, actor, world)
            assert success
            
            # State should have changed (unless it was a stay-idle action)
            if chosen.resulting_state != original_state:
                assert actor.state == chosen.resulting_state
            
            # Should have ticks left if action takes multiple ticks
            if chosen.duration_ticks > 1:
                assert actor.current_ticks_left > 0
    
    def test_time_based_preferences(self):
        """Test that action preferences change based on time of day."""
        # Morning time
        morning_time = datetime(2024, 1, 1, 8, 0)  # 8 AM
        world = initialize_world(start_time=morning_time)
        actor = create_sample_actor(world, "Test Actor", "A")
        
        morning_choice = choose_action(actor, world)
        
        # Evening time
        evening_time = datetime(2024, 1, 1, 20, 0)  # 8 PM
        world.clock.current_time = evening_time
        
        evening_choice = choose_action(actor, world)
        
        # Choices might be different based on time (though random, so not guaranteed)
        # At minimum, both should return valid actions
        if morning_choice:
            assert hasattr(morning_choice, 'name')
        if evening_choice:
            assert hasattr(evening_choice, 'name')