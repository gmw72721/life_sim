"""
Calendar enforcement and scheduling system.

Implements hard scheduling constraints that override probability-based decisions
when actors have calendar commitments that must be honored.
"""

from typing import Optional
from datetime import datetime, timedelta
import logging

from .states import State
from .models import Actor, WorldClock

# Configure logging
logger = logging.getLogger(__name__)


def override_state(actor: Actor, clock: WorldClock) -> Optional[State]:
    """
    Return hard-required state if a calendar TimeBlock is active.
    
    This function checks if the actor has a scheduled commitment at the current time
    and returns the required state, overriding normal probability-based decisions.
    
    Args:
        actor: The actor to check for calendar commitments
        clock: The world clock with current time
        
    Returns:
        State: Required state if calendar override is needed, None otherwise
    """
    current_time = clock.current_time
    
    # Check if there's an active time block
    current_block = actor.get_current_time_block(current_time)
    if not current_block:
        return None
    
    required_state = current_block.required_state
    
    # Apply emergency overrides - certain conditions can break calendar constraints
    
    # Critical fatigue override - if actor is extremely tired, they must rest
    if actor.fatigue >= 95:
        logger.debug(f"Actor {actor.name} calling in sick due to extreme fatigue ({actor.fatigue:.1f})")
        # TODO: Prompt 2 - implement proper "CallInSick" action
        return State.Idle  # Allow them to choose sleep instead of scheduled activity
    
    # Critical hunger override - if actor is starving, they must eat
    if actor.hunger >= 90 and required_state not in [State.Eating, State.Sleeping]:
        logger.debug(f"Actor {actor.name} breaking schedule due to extreme hunger ({actor.hunger:.1f})")
        return State.Idle  # Allow them to choose eating instead of scheduled activity
    
    # Health emergency override - very low mood might prevent certain activities
    if actor.mood <= -1.8 and required_state in [State.Socialising, State.In_Meeting]:
        logger.debug(f"Actor {actor.name} too depressed for social activities (mood: {actor.mood:.2f})")
        return State.Idle  # Too depressed for social activities
    
    # Cash constraint override - can't do activities that cost money if broke
    if actor.cash <= 0 and required_state in [State.Shopping, State.Leisure]:
        logger.debug(f"Actor {actor.name} can't afford scheduled activities (cash: ${actor.cash:.2f})")
        return State.Idle  # Can't afford scheduled activities
    
    # Location constraint - if actor can't reach required location, idle instead
    # This is a simplified check - in reality we'd need pathfinding
    if required_state == State.Focused_Work:
        # Work can be done from home or office
        if actor.location_id not in ["public_office"] and not actor.location_id.startswith("home_"):
            logger.debug(f"Actor {actor.name} needs to travel to work location")
            return State.Transitioning  # Need to go somewhere to work
    
    elif required_state == State.In_Meeting:
        # Meetings typically require office or specific locations
        if actor.location_id not in ["public_office", "public_restaurant"]:
            logger.debug(f"Actor {actor.name} needs to travel to meeting location")
            return State.Transitioning  # Need to go to meeting location
    
    elif required_state == State.Exercising:
        # Exercise requires gym, park, or home
        valid_exercise_locations = ["public_gym", "public_park", "public_walking_path"]
        valid_exercise_locations.extend([f"home_{letter}" for letter in "abcdefghijkl"])
        if actor.location_id not in valid_exercise_locations:
            logger.debug(f"Actor {actor.name} needs to travel to exercise location")
            return State.Transitioning  # Need to go to exercise location
    
    elif required_state == State.Shopping:
        # Shopping requires mall or grocery store
        if actor.location_id not in ["public_mall", "public_grocery_store"]:
            logger.debug(f"Actor {actor.name} needs to travel to shopping location")
            return State.Transitioning  # Need to go to shopping location
    
    elif required_state == State.Socialising:
        # Social activities can happen in various public places
        social_locations = ["public_coffee_shop", "public_restaurant", "public_bar", 
                          "public_park", "public_office"]
        if actor.location_id not in social_locations:
            logger.debug(f"Actor {actor.name} needs to travel to social location")
            return State.Transitioning  # Need to go to social location
    
    # If all constraints are satisfied, return the required state
    logger.debug(f"Actor {actor.name} following calendar: {required_state.name}")
    return required_state


def is_weekend(clock: WorldClock) -> bool:
    """
    Check if current time is weekend using WorldClock timezone.
    
    Args:
        clock: The world clock with current time
        
    Returns:
        bool: True if weekend (Saturday or Sunday)
    """
    # Use the clock's current time (assumed to be in correct timezone)
    current_time = clock.current_time
    
    # Get weekday (0=Monday, 6=Sunday)
    weekday = current_time.weekday()
    
    # Weekend is Saturday (5) and Sunday (6)
    is_weekend_day = weekday in [5, 6]
    
    logger.debug(f"Time: {current_time.strftime('%A %Y-%m-%d %H:%M')}, Weekend: {is_weekend_day}")
    return is_weekend_day


def is_business_hours(clock: WorldClock) -> bool:
    """
    Check if current time is during business hours.
    
    Args:
        clock: The world clock with current time
        
    Returns:
        bool: True if during business hours (9 AM - 5 PM, weekdays)
    """
    current_time = clock.current_time
    hour = current_time.hour
    
    # Business hours: 9 AM to 5 PM
    in_business_hours = 9 <= hour < 17
    
    # Must also be a weekday
    is_weekday = not is_weekend(clock)
    
    return in_business_hours and is_weekday


def get_upcoming_commitments(actor: Actor, clock: WorldClock, hours_ahead: int = 2) -> list:
    """
    Get upcoming calendar commitments within the specified time window.
    
    Args:
        actor: The actor to check commitments for
        clock: The world clock with current time
        hours_ahead: How many hours ahead to look for commitments
        
    Returns:
        List of upcoming TimeBlocks
    """
    current_time = clock.current_time
    end_time = current_time + timedelta(hours=hours_ahead)
    
    upcoming = []
    for block in actor.calendar:
        # Check if block starts within our time window
        if current_time <= block.start_dt <= end_time:
            upcoming.append(block)
        # Check if block is already active and extends into our window
        elif block.start_dt <= current_time < block.end_dt:
            upcoming.append(block)
    
    # Sort by start time
    upcoming.sort(key=lambda b: b.start_dt)
    return upcoming


def should_prepare_for_commitment(actor: Actor, clock: WorldClock) -> Optional[State]:
    """
    Check if actor should prepare for an upcoming commitment.
    
    This can suggest transitional states to help actors get ready for
    scheduled activities (e.g., traveling to the location).
    
    Args:
        actor: The actor to check
        clock: The world clock with current time
        
    Returns:
        State: Suggested preparatory state, or None
    """
    upcoming = get_upcoming_commitments(actor, clock, hours_ahead=1)
    
    if not upcoming:
        return None
    
    next_commitment = upcoming[0]
    time_until = (next_commitment.start_dt - clock.current_time).total_seconds() / 60  # minutes
    
    # If commitment is very soon (within 30 minutes), suggest preparation
    if time_until <= 30:
        required_state = next_commitment.required_state
        
        # Suggest transitioning if actor needs to move for the commitment
        if required_state in [State.Focused_Work, State.In_Meeting, State.Exercising, 
                            State.Shopping, State.Socialising]:
            # Check if actor is already in a suitable location
            current_location = actor.location_id
            
            # Work locations
            if required_state == State.Focused_Work:
                if current_location not in ["public_office"] and not current_location.startswith("home_"):
                    logger.debug(f"Actor {actor.name} should prepare to travel for work")
                    return State.Transitioning
            
            # Meeting locations  
            elif required_state == State.In_Meeting:
                if current_location not in ["public_office", "public_restaurant"]:
                    logger.debug(f"Actor {actor.name} should prepare to travel for meeting")
                    return State.Transitioning
            
            # Exercise locations
            elif required_state == State.Exercising:
                exercise_locations = ["public_gym", "public_park", "public_walking_path"]
                exercise_locations.extend([f"home_{letter}" for letter in "abcdefghijkl"])
                if current_location not in exercise_locations:
                    logger.debug(f"Actor {actor.name} should prepare to travel for exercise")
                    return State.Transitioning
            
            # Shopping locations
            elif required_state == State.Shopping:
                if current_location not in ["public_mall", "public_grocery_store"]:
                    logger.debug(f"Actor {actor.name} should prepare to travel for shopping")
                    return State.Transitioning
            
            # Social locations
            elif required_state == State.Socialising:
                social_locations = ["public_coffee_shop", "public_restaurant", "public_bar",
                                  "public_park", "public_office"]
                if current_location not in social_locations:
                    logger.debug(f"Actor {actor.name} should prepare to travel for social activity")
                    return State.Transitioning
    
    return None


def get_schedule_conflicts(actor: Actor) -> list:
    """
    Identify overlapping time blocks in an actor's calendar.
    
    Args:
        actor: The actor to check for conflicts
        
    Returns:
        List of tuples containing conflicting TimeBlock pairs
    """
    conflicts = []
    calendar = actor.calendar
    
    for i, block1 in enumerate(calendar):
        for block2 in calendar[i+1:]:
            if block1.overlaps_with(block2):
                conflicts.append((block1, block2))
                logger.warning(f"Schedule conflict for actor {actor.name}: "
                             f"{block1.description or block1.required_state.name} overlaps with "
                             f"{block2.description or block2.required_state.name}")
    
    return conflicts


def suggest_schedule_optimization(actor: Actor, clock: WorldClock) -> dict:
    """
    Suggest optimizations to an actor's schedule.
    
    Args:
        actor: The actor whose schedule to optimize
        clock: Current world clock
        
    Returns:
        Dict containing optimization suggestions
    """
    suggestions = {
        "conflicts": [],
        "gaps": [],
        "efficiency_tips": []
    }
    
    # Find conflicts
    conflicts = get_schedule_conflicts(actor)
    for conflict in conflicts:
        suggestions["conflicts"].append({
            "block1": conflict[0].description or f"{conflict[0].required_state.name}",
            "block2": conflict[1].description or f"{conflict[1].required_state.name}",
            "overlap_start": max(conflict[0].start_dt, conflict[1].start_dt),
            "overlap_end": min(conflict[0].end_dt, conflict[1].end_dt)
        })
    
    # Find large gaps (more than 3 hours with no scheduled activities)
    sorted_blocks = sorted(actor.calendar, key=lambda b: b.start_dt)
    for i in range(len(sorted_blocks) - 1):
        gap_start = sorted_blocks[i].end_dt
        gap_end = sorted_blocks[i + 1].start_dt
        gap_duration = (gap_end - gap_start).total_seconds() / 3600  # hours
        
        if gap_duration > 3:
            suggestions["gaps"].append({
                "start": gap_start,
                "end": gap_end,
                "duration_hours": gap_duration
            })
    
    # Efficiency tips based on location clustering
    location_changes = 0
    prev_location = None
    for block in sorted_blocks:
        # Estimate location for activity type
        if block.required_state == State.Focused_Work:
            location = "office"
        elif block.required_state == State.Shopping:
            location = "shopping"
        elif block.required_state == State.Exercising:
            location = "gym"
        else:
            location = "general"
        
        if prev_location and prev_location != location:
            location_changes += 1
        prev_location = location
    
    if location_changes > 5:  # Arbitrary threshold
        suggestions["efficiency_tips"].append(
            "Consider grouping activities by location to reduce travel time"
        )
    
    # Weekend vs weekday balance
    weekend_blocks = 0
    weekday_blocks = 0
    
    for block in sorted_blocks:
        if block.start_dt.weekday() in [5, 6]:  # Saturday, Sunday
            weekend_blocks += 1
        else:
            weekday_blocks += 1
    
    if weekend_blocks == 0 and weekday_blocks > 5:
        suggestions["efficiency_tips"].append(
            "Consider scheduling some leisure activities on weekends"
        )
    
    return suggestions


def is_valid_schedule_time(actor: Actor, start_time: datetime, duration_minutes: int) -> bool:
    """
    Check if a time slot is available in an actor's schedule.
    
    Args:
        actor: The actor to check
        start_time: Proposed start time
        duration_minutes: Duration of the proposed activity
        
    Returns:
        bool: True if the time slot is available
    """
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Check against existing calendar entries
    for block in actor.calendar:
        if (start_time < block.end_dt) and (end_time > block.start_dt):
            return False  # Overlaps with existing commitment
    
    return True


def add_emergency_override(actor: Actor, clock: WorldClock, reason: str) -> bool:
    """
    Add an emergency override to skip scheduled activities.
    
    Args:
        actor: The actor needing the override
        clock: Current world clock
        reason: Reason for the override
        
    Returns:
        bool: True if override was applied
    """
    current_block = actor.get_current_time_block(clock.current_time)
    if current_block:
        logger.warning(f"Emergency override for actor {actor.name}: {reason}")
        # In a full implementation, this might modify the calendar
        # For now, just log the override
        return True
    return False