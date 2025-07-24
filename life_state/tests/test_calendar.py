"""
Tests for calendar scheduling functionality.
"""

import pytest
from datetime import datetime, timedelta

from life_state.calendar_scheduler import (
    override_state, get_upcoming_commitments, should_prepare_for_commitment,
    get_schedule_conflicts, suggest_schedule_optimization, is_valid_schedule_time
)
from life_state.models import TimeBlock
from life_state.states import State
from life_state.world import initialize_world, create_sample_actor


class TestCalendarOverride:
    """Test calendar override functionality."""
    
    def test_no_override_without_schedule(self):
        """Test that no override occurs when actor has no schedule."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # No calendar entries
        result = override_state(actor, world.clock)
        
        assert result is None
    
    def test_override_with_active_schedule(self):
        """Test override when actor has active scheduled commitment."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 10, 0))
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Add work schedule
        work_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 9, 0),
            end_dt=datetime(2024, 1, 1, 17, 0),
            required_state=State.Focused_Work,
            description="Work day"
        )
        actor.calendar.append(work_block)
        
        result = override_state(actor, world.clock)
        
        assert result == State.Focused_Work
    
    def test_emergency_override_critical_fatigue(self):
        """Test that critical fatigue overrides calendar."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 10, 0))
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Add work schedule
        work_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 9, 0),
            end_dt=datetime(2024, 1, 1, 17, 0),
            required_state=State.Focused_Work
        )
        actor.calendar.append(work_block)
        
        # Set critical fatigue
        actor.fatigue = 96.0
        
        result = override_state(actor, world.clock)
        
        # Should override work with idle (allowing sleep choice)
        assert result == State.Idle
    
    def test_emergency_override_critical_hunger(self):
        """Test that critical hunger overrides calendar."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 14, 0))
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Add meeting schedule
        meeting_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 14, 0),
            end_dt=datetime(2024, 1, 1, 15, 0),
            required_state=State.In_Meeting
        )
        actor.calendar.append(meeting_block)
        
        # Set critical hunger
        actor.hunger = 92.0
        
        result = override_state(actor, world.clock)
        
        # Should override meeting with idle (allowing eating choice)
        assert result == State.Idle
    
    def test_location_constraint_override(self):
        """Test that location constraints cause transitioning."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 10, 0))
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Actor is at home, but needs to work
        work_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 9, 0),
            end_dt=datetime(2024, 1, 1, 17, 0),
            required_state=State.Focused_Work
        )
        actor.calendar.append(work_block)
        
        # Actor is at home but work might require office
        # Since work can be done from home, should return work state
        result = override_state(actor, world.clock)
        
        assert result == State.Focused_Work


class TestUpcomingCommitments:
    """Test upcoming commitment detection."""
    
    def test_get_upcoming_commitments_empty(self):
        """Test getting upcoming commitments when none exist."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        upcoming = get_upcoming_commitments(actor, world.clock)
        
        assert len(upcoming) == 0
    
    def test_get_upcoming_commitments_within_window(self):
        """Test getting commitments within time window."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 10, 0))
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Add commitment starting in 1 hour
        future_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 11, 0),
            end_dt=datetime(2024, 1, 1, 12, 0),
            required_state=State.In_Meeting
        )
        actor.calendar.append(future_block)
        
        # Add commitment starting in 3 hours (outside default window)
        far_future_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 13, 0),
            end_dt=datetime(2024, 1, 1, 14, 0),
            required_state=State.In_Meeting
        )
        actor.calendar.append(far_future_block)
        
        upcoming = get_upcoming_commitments(actor, world.clock, hours_ahead=2)
        
        assert len(upcoming) == 1
        assert upcoming[0] == future_block
    
    def test_get_upcoming_commitments_sorted(self):
        """Test that upcoming commitments are sorted by start time."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 10, 0))
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Add commitments in reverse chronological order
        second_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 12, 0),
            end_dt=datetime(2024, 1, 1, 13, 0),
            required_state=State.In_Meeting
        )
        first_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 11, 0),
            end_dt=datetime(2024, 1, 1, 12, 0),
            required_state=State.Focused_Work
        )
        
        actor.calendar.extend([second_block, first_block])
        
        upcoming = get_upcoming_commitments(actor, world.clock)
        
        assert len(upcoming) == 2
        assert upcoming[0] == first_block
        assert upcoming[1] == second_block


class TestPreparationSuggestions:
    """Test preparation suggestion system."""
    
    def test_no_preparation_needed_no_commitments(self):
        """Test no preparation suggested when no commitments."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        suggestion = should_prepare_for_commitment(actor, world.clock)
        
        assert suggestion is None
    
    def test_preparation_for_soon_commitment(self):
        """Test preparation suggested for soon commitment."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 10, 30))
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Meeting in 20 minutes at office
        meeting_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 10, 50),
            end_dt=datetime(2024, 1, 1, 11, 50),
            required_state=State.In_Meeting
        )
        actor.calendar.append(meeting_block)
        
        # Actor is at home, should suggest transitioning to office
        suggestion = should_prepare_for_commitment(actor, world.clock)
        
        assert suggestion == State.Transitioning
    
    def test_no_preparation_if_already_at_location(self):
        """Test no preparation needed if already at suitable location."""
        world = initialize_world(start_time=datetime(2024, 1, 1, 10, 30))
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Move actor to office
        actor.location_id = "public_office"
        
        # Meeting in 20 minutes at office
        meeting_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 10, 50),
            end_dt=datetime(2024, 1, 1, 11, 50),
            required_state=State.In_Meeting
        )
        actor.calendar.append(meeting_block)
        
        suggestion = should_prepare_for_commitment(actor, world.clock)
        
        assert suggestion is None


class TestScheduleConflicts:
    """Test schedule conflict detection."""
    
    def test_no_conflicts_empty_schedule(self):
        """Test no conflicts with empty schedule."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        conflicts = get_schedule_conflicts(actor)
        
        assert len(conflicts) == 0
    
    def test_detect_overlapping_blocks(self):
        """Test detection of overlapping time blocks."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Add overlapping blocks
        block1 = TimeBlock(
            start_dt=datetime(2024, 1, 1, 10, 0),
            end_dt=datetime(2024, 1, 1, 12, 0),
            required_state=State.Focused_Work
        )
        block2 = TimeBlock(
            start_dt=datetime(2024, 1, 1, 11, 0),
            end_dt=datetime(2024, 1, 1, 13, 0),
            required_state=State.In_Meeting
        )
        
        actor.calendar.extend([block1, block2])
        
        conflicts = get_schedule_conflicts(actor)
        
        assert len(conflicts) == 1
        assert (block1, block2) in conflicts or (block2, block1) in conflicts
    
    def test_no_conflicts_adjacent_blocks(self):
        """Test that adjacent (non-overlapping) blocks don't conflict."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Add adjacent blocks
        block1 = TimeBlock(
            start_dt=datetime(2024, 1, 1, 10, 0),
            end_dt=datetime(2024, 1, 1, 12, 0),
            required_state=State.Focused_Work
        )
        block2 = TimeBlock(
            start_dt=datetime(2024, 1, 1, 12, 0),
            end_dt=datetime(2024, 1, 1, 14, 0),
            required_state=State.In_Meeting
        )
        
        actor.calendar.extend([block1, block2])
        
        conflicts = get_schedule_conflicts(actor)
        
        assert len(conflicts) == 0


class TestScheduleOptimization:
    """Test schedule optimization suggestions."""
    
    def test_suggest_optimization_basic(self):
        """Test basic optimization suggestion generation."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        suggestions = suggest_schedule_optimization(actor, world.clock)
        
        assert "conflicts" in suggestions
        assert "gaps" in suggestions
        assert "efficiency_tips" in suggestions
        assert isinstance(suggestions["conflicts"], list)
        assert isinstance(suggestions["gaps"], list)
        assert isinstance(suggestions["efficiency_tips"], list)
    
    def test_detect_large_gaps(self):
        """Test detection of large gaps in schedule."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Add blocks with large gap
        morning_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 9, 0),
            end_dt=datetime(2024, 1, 1, 10, 0),
            required_state=State.Focused_Work
        )
        afternoon_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 15, 0),
            end_dt=datetime(2024, 1, 1, 16, 0),
            required_state=State.In_Meeting
        )
        
        actor.calendar.extend([morning_block, afternoon_block])
        
        suggestions = suggest_schedule_optimization(actor, world.clock)
        
        assert len(suggestions["gaps"]) > 0
        gap = suggestions["gaps"][0]
        assert gap["duration_hours"] == 5.0  # 5 hour gap


class TestScheduleValidation:
    """Test schedule validation functionality."""
    
    def test_valid_schedule_time_empty_calendar(self):
        """Test that any time is valid with empty calendar."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        start_time = datetime(2024, 1, 1, 10, 0)
        is_valid = is_valid_schedule_time(actor, start_time, 60)
        
        assert is_valid is True
    
    def test_invalid_schedule_time_overlap(self):
        """Test that overlapping time is invalid."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Add existing block
        existing_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 10, 0),
            end_dt=datetime(2024, 1, 1, 12, 0),
            required_state=State.Focused_Work
        )
        actor.calendar.append(existing_block)
        
        # Try to schedule overlapping time
        start_time = datetime(2024, 1, 1, 11, 0)
        is_valid = is_valid_schedule_time(actor, start_time, 60)
        
        assert is_valid is False
    
    def test_valid_schedule_time_no_overlap(self):
        """Test that non-overlapping time is valid."""
        world = initialize_world()
        actor = create_sample_actor(world, "Test Actor", "A")
        
        # Add existing block
        existing_block = TimeBlock(
            start_dt=datetime(2024, 1, 1, 10, 0),
            end_dt=datetime(2024, 1, 1, 12, 0),
            required_state=State.Focused_Work
        )
        actor.calendar.append(existing_block)
        
        # Try to schedule non-overlapping time
        start_time = datetime(2024, 1, 1, 13, 0)
        is_valid = is_valid_schedule_time(actor, start_time, 60)
        
        assert is_valid is True