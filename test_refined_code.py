#!/usr/bin/env python3
"""
Simple test script to verify the refined code works.
Tests basic functionality without requiring pytest.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_probability_functions():
    """Test the refined probability functions."""
    print("Testing probability functions...")
    
    # Test without pydantic for now - just the pure functions
    try:
        from life_state.probability import hunger_factor, fatigue_factor, mood_factor, presence_boost
        
        # Test hunger_factor bounds
        assert hunger_factor(0) == 0.8, f"Expected 0.8, got {hunger_factor(0)}"
        assert hunger_factor(100) == 1.2, f"Expected 1.2, got {hunger_factor(100)}"
        assert hunger_factor(50) == 1.0, f"Expected 1.0, got {hunger_factor(50)}"
        
        # Test negative input clamping
        assert hunger_factor(-10) == 0.8, f"Expected 0.8, got {hunger_factor(-10)}"
        
        # Test fatigue_factor bounds  
        assert fatigue_factor(0) == 0.8, f"Expected 0.8, got {fatigue_factor(0)}"
        assert fatigue_factor(100) == 1.2, f"Expected 1.2, got {fatigue_factor(100)}"
        
        # Test mood_factor
        assert mood_factor(0.0) == 1.0, f"Expected 1.0, got {mood_factor(0.0)}"
        assert mood_factor(-2.0) == 0.97, f"Expected 0.97, got {mood_factor(-2.0)}"
        
        # Test presence_boost
        assert presence_boost(0) == 0.0, f"Expected 0.0, got {presence_boost(0)}"
        assert presence_boost(3) == 0.6, f"Expected 0.6, got {presence_boost(3)}"
        assert presence_boost(10) == 0.6, f"Expected 0.6 (capped), got {presence_boost(10)}"
        
        print("✓ Probability functions work correctly")
        return True
        
    except Exception as e:
        print(f"✗ Probability functions failed: {e}")
        return False

def test_states_enum():
    """Test that states enum works correctly."""
    print("Testing states enum...")
    
    try:
        from life_state.states import State, is_core_state, get_state_priority
        
        # Test core states
        assert is_core_state(State.Idle), "Idle should be a core state"
        assert is_core_state(State.Sleeping), "Sleeping should be a core state"
        assert not is_core_state(State.TimeJumping), "TimeJumping should not be a core state"
        
        # Test string representation
        assert str(State.Idle) == "Idle", f"Expected 'Idle', got '{str(State.Idle)}'"
        
        # Test priority system
        sleep_priority = get_state_priority(State.Sleeping)
        idle_priority = get_state_priority(State.Idle)
        assert sleep_priority > idle_priority, "Sleep should have higher priority than idle"
        
        print("✓ States enum works correctly")
        return True
        
    except Exception as e:
        print(f"✗ States enum failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading."""
    print("Testing configuration loading...")
    
    try:
        from life_state.world import load_config, get_resource_rates
        
        config = load_config()
        assert 'fatigue_rate' in config, "Config should have fatigue_rate"
        assert 'hunger_rate' in config, "Config should have hunger_rate"
        assert 'mood_modifiers' in config, "Config should have mood_modifiers"
        
        rates = get_resource_rates(config)
        assert 'fatigue_rate' in rates, "Rates should have fatigue_rate"
        
        print("✓ Configuration loading works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Testing Refined Life State Code ===")
    print()
    
    tests = [
        test_probability_functions,
        test_states_enum, 
        test_config_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All tests passed! The refined code is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())