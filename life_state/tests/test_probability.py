"""
Tests for probability calculation functions.

Tests probability modifiers, linear scaling functions, and action selection logic.
"""

import pytest
from datetime import datetime

from life_state.probability import (
    mood_factor, hunger_factor, fatigue_factor, presence_boost,
    calculate_action_probability, choose_action, validate_probability_inputs
)
from life_state.models import Actor, WorldState, WorldClock, Location
from life_state.actions import STAY_IDLE, EAT_MEAL
from life_state.states import State


class TestLinearScalingFunctions:
    """Test the linear scaling functions for probability modifiers."""
    
    def test_hunger_factor_bounds(self):
        """Test that hunger_factor has correct bounds."""
        # Test boundary values
        assert abs(hunger_factor(0) - 0.8) < 1e-10
        assert abs(hunger_factor(100) - 1.2) < 1e-10
        
        # Test intermediate values
        assert abs(hunger_factor(50) - 1.0) < 1e-10
        assert abs(hunger_factor(25) - 0.9) < 1e-10
        assert abs(hunger_factor(75) - 1.1) < 1e-10
    
    def test_hunger_factor_negative_input_clamping(self):
        """Test that negative hunger inputs are clamped to 0."""
        assert hunger_factor(-10) == 0.8
        assert hunger_factor(-100) == 0.8
    
    def test_hunger_factor_high_input_clamping(self):
        """Test that high hunger inputs are clamped to 100."""
        assert abs(hunger_factor(150) - 1.2) < 1e-10
        assert abs(hunger_factor(200) - 1.2) < 1e-10
    
    def test_fatigue_factor_bounds(self):
        """Test that fatigue_factor has correct bounds."""
        # Test boundary values
        assert abs(fatigue_factor(0) - 0.8) < 1e-10
        assert abs(fatigue_factor(100) - 1.2) < 1e-10
        
        # Test intermediate values
        assert abs(fatigue_factor(50) - 1.0) < 1e-10
        assert abs(fatigue_factor(25) - 0.9) < 1e-10
        assert abs(fatigue_factor(75) - 1.1) < 1e-10
    
    def test_fatigue_factor_negative_input_clamping(self):
        """Test that negative fatigue inputs are clamped to 0."""
        assert fatigue_factor(-10) == 0.8
        assert fatigue_factor(-50) == 0.8
    
    def test_fatigue_factor_high_input_clamping(self):
        """Test that high fatigue inputs are clamped to 100."""
        assert abs(fatigue_factor(150) - 1.2) < 1e-10
        assert abs(fatigue_factor(300) - 1.2) < 1e-10
    
    def test_mood_factor_bounds(self):
        """Test that mood_factor works within valid mood range."""
        # Test boundary values
        assert mood_factor(-2.0) == 1.0 + (0.015 * -2.0)  # 0.97
        assert mood_factor(2.0) == 1.0 + (0.015 * 2.0)    # 1.03
        assert mood_factor(0.0) == 1.0
        
        # Test intermediate values
        assert mood_factor(1.0) == 1.015
        assert mood_factor(-1.0) == 0.985
    
    def test_mood_factor_clamping(self):
        """Test that mood values are clamped to valid range."""
        # Test values outside valid range are clamped
        assert mood_factor(-3.0) == mood_factor(-2.0)  # Clamped to -2.0
        assert mood_factor(5.0) == mood_factor(2.0)    # Clamped to 2.0
    
    def test_presence_boost_bounds(self):
        """Test that presence_boost works correctly."""
        assert abs(presence_boost(0) - 0.0) < 1e-10
        assert abs(presence_boost(1) - 0.2) < 1e-10
        assert abs(presence_boost(2) - 0.4) < 1e-10
        assert abs(presence_boost(3) - 0.6) < 1e-10
        assert abs(presence_boost(4) - 0.6) < 1e-10  # Capped at 3
        assert abs(presence_boost(10) - 0.6) < 1e-10  # Capped at 3
    
    def test_presence_boost_negative_input(self):
        """Test that negative presence inputs are handled."""
        assert presence_boost(-1) == 0.0
        assert presence_boost(-10) == 0.0


class TestProbabilityCalculation:
    """Test probability calculation for actions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.clock = WorldClock(current_time=datetime(2024, 1, 1, 12, 0))
        self.world = WorldState(clock=self.clock, world_id="test_world")
        
        # Add a location
        location = Location(id="home_a", name="Home-A", category="home")
        self.world.locations["home_a"] = location
        
        # Create test actor
        self.actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="test_world",
            hunger=50.0,
            fatigue=50.0,
            mood=0.0
        )
        self.world.add_actor(self.actor)
    
    def test_calculate_action_probability_base_weight(self):
        """Test that base weight is used correctly."""
        prob = calculate_action_probability(STAY_IDLE, self.actor, self.world)
        
        # Should be base weight (1.0) modified by factors
        assert prob > 0.0
        assert isinstance(prob, float)
    
    def test_calculate_action_probability_hunger_modifier(self):
        """Test that hunger affects eating action probability."""
        # High hunger should increase eating probability
        self.actor.hunger = 90.0
        high_hunger_prob = calculate_action_probability(EAT_MEAL, self.actor, self.world)
        
        # Low hunger should decrease eating probability
        self.actor.hunger = 10.0
        low_hunger_prob = calculate_action_probability(EAT_MEAL, self.actor, self.world)
        
        assert high_hunger_prob > low_hunger_prob
    
    def test_calculate_action_probability_mood_modifier(self):
        """Test that mood affects action probability."""
        # Good mood
        self.actor.mood = 1.5
        good_mood_prob = calculate_action_probability(STAY_IDLE, self.actor, self.world)
        
        # Bad mood
        self.actor.mood = -1.5
        bad_mood_prob = calculate_action_probability(STAY_IDLE, self.actor, self.world)
        
        assert good_mood_prob > bad_mood_prob
    
    def test_calculate_action_probability_non_negative(self):
        """Test that probability is always non-negative."""
        # Try extreme values that might produce negative results
        self.actor.mood = -2.0
        self.actor.hunger = 0.0
        self.actor.fatigue = 0.0
        
        prob = calculate_action_probability(STAY_IDLE, self.actor, self.world)
        assert prob >= 0.0


class TestActionSelection:
    """Test action selection logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.clock = WorldClock(current_time=datetime(2024, 1, 1, 12, 0))
        self.world = WorldState(clock=self.clock, world_id="test_world")
        
        # Add locations
        for location in Location.create_default_locations():
            self.world.locations[location.id] = location
        
        # Create test actor
        self.actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="test_world",
            hunger=50.0,
            fatigue=50.0,
            mood=0.0
        )
        self.world.add_actor(self.actor)
    
    def test_choose_action_returns_action(self):
        """Test that choose_action returns a valid action."""
        action = choose_action(self.actor, self.world, core_only=True)
        
        assert action is not None
        assert hasattr(action, 'name')
        assert hasattr(action, 'resulting_state')
    
    def test_choose_action_core_only_flag(self):
        """Test that core_only flag works correctly."""
        # Should work with core_only=True
        action = choose_action(self.actor, self.world, core_only=True)
        assert action is not None
        
        # Should also work with core_only=False
        action = choose_action(self.actor, self.world, core_only=False)
        assert action is not None
    
    def test_choose_action_no_valid_actions(self):
        """Test behavior when no valid actions are available."""
        # Create actor with impossible constraints
        impossible_actor = Actor(
            name="Impossible Actor",
            home_id="home_a",
            location_id="nonexistent_location",  # Invalid location
            world_id="test_world",
            cash=0.0  # Minimum valid cash
        )
        
        # This should handle the case gracefully
        action = choose_action(impossible_actor, self.world, core_only=True)
        # Should either return None or a fallback action
        assert action is None or hasattr(action, 'name')


class TestProbabilityValidation:
    """Test probability input validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.clock = WorldClock(current_time=datetime(2024, 1, 1, 12, 0))
        self.world = WorldState(clock=self.clock, world_id="test_world")
        
        # Add a location
        location = Location(id="home_a", name="Home-A", category="home")
        self.world.locations["home_a"] = location
    
    def test_validate_probability_inputs_valid_actor(self):
        """Test validation with valid actor."""
        actor = Actor(
            name="Valid Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="test_world",
            hunger=50.0,
            fatigue=50.0,
            mood=0.0
        )
        
        errors = validate_probability_inputs(actor, self.world)
        assert len(errors) == 0
    
    def test_validate_probability_inputs_invalid_hunger(self):
        """Test validation with invalid hunger."""
        actor = Actor(
            name="Invalid Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="test_world",
            hunger=50.0,
            fatigue=50.0,
            mood=0.0
        )
        
        # Manually set invalid hunger (bypassing validation)
        actor.__dict__['hunger'] = 150.0
        
        errors = validate_probability_inputs(actor, self.world)
        assert len(errors) > 0
        assert any("hunger" in error.lower() for error in errors)
    
    def test_validate_probability_inputs_invalid_location(self):
        """Test validation with invalid location."""
        actor = Actor(
            name="Invalid Actor",
            home_id="home_a",
            location_id="nonexistent_location",
            world_id="test_world",
            hunger=50.0,
            fatigue=50.0,
            mood=0.0
        )
        
        errors = validate_probability_inputs(actor, self.world)
        assert len(errors) > 0
        assert any("location" in error.lower() for error in errors)
    
    def test_validate_probability_inputs_missing_clock(self):
        """Test validation with missing world clock."""
        actor = Actor(
            name="Valid Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="test_world"
        )
        
        # Create world with a temporary clock, then set to None
        from life_state.models import WorldClock
        temp_clock = WorldClock(current_time=datetime(2024, 1, 1, 12, 0))
        world_no_clock = WorldState(actors={}, locations={}, world_id="test", clock=temp_clock)
        world_no_clock.clock = None
        
        errors = validate_probability_inputs(actor, world_no_clock)
        assert len(errors) > 0
        assert any("clock" in error.lower() for error in errors)


class TestProbabilityWeights:
    """Test that probability weights sum correctly."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.clock = WorldClock(current_time=datetime(2024, 1, 1, 12, 0))
        self.world = WorldState(clock=self.clock, world_id="test_world")
        
        # Add all locations
        for location in Location.create_default_locations():
            self.world.locations[location.id] = location
        
        # Create test actor
        self.actor = Actor(
            name="Test Actor",
            home_id="home_a",
            location_id="home_a",
            world_id="test_world"
        )
        self.world.add_actor(self.actor)
    
    def test_probability_weights_positive(self):
        """Test that all probability weights are positive."""
        from life_state.actions import get_available_actions
        
        available_actions = get_available_actions(self.actor, self.world, core_only=True)
        
        for action in available_actions:
            prob = calculate_action_probability(action, self.actor, self.world)
            assert prob >= 0.0, f"Action {action.name} has negative probability: {prob}"
    
    def test_probability_weights_not_all_zero(self):
        """Test that not all probability weights are zero."""
        from life_state.actions import get_available_actions
        
        available_actions = get_available_actions(self.actor, self.world, core_only=True)
        probabilities = [
            calculate_action_probability(action, self.actor, self.world)
            for action in available_actions
        ]
        
        # At least one probability should be positive
        assert any(prob > 0.0 for prob in probabilities), "All probabilities are zero"
        
        # Total probability should be positive
        total_prob = sum(probabilities)
        assert total_prob > 0.0, f"Total probability is {total_prob}"