"""
Core data models for life_state simulation.

Defines all the fundamental data structures used throughout the system.
Built with Pydantic for validation and serialization support.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from uuid import uuid4

from .states import State


class TimeBlock(BaseModel):
    """A calendar entry representing a scheduled time period."""
    
    start_dt: datetime = Field(description="Start datetime for this time block")
    end_dt: datetime = Field(description="End datetime for this time block")
    required_state: State = Field(description="State the actor should be in during this time")
    description: Optional[str] = Field(default=None, description="Optional description of the activity")
    
    def duration_minutes(self) -> int:
        """Get the duration of this time block in minutes."""
        return int((self.end_dt - self.start_dt).total_seconds() / 60)
    
    def overlaps_with(self, other: "TimeBlock") -> bool:
        """Check if this time block overlaps with another."""
        return (self.start_dt < other.end_dt) and (self.end_dt > other.start_dt)


class Location(BaseModel):
    """A location where actors can be present."""
    
    id: str = Field(description="Unique identifier for the location")
    name: str = Field(description="Human-readable name of the location")
    category: str = Field(description="Category of location (public, home, special)")
    
    @classmethod
    def create_default_locations(cls) -> List["Location"]:
        """Create the standard set of locations for the simulation."""
        locations = []
        
        # Public locations (14)
        public_locations = [
            "Office", "Coffee Shop", "Restaurant", "Mall", "Gym", "Park", 
            "Library", "Cinema", "Bar", "Clinic", "Bus", "Grocery Store", 
            "Car", "Walking-Path"
        ]
        
        for name in public_locations:
            locations.append(cls(
                id=f"public_{name.lower().replace(' ', '_').replace('-', '_')}",
                name=name,
                category="public"
            ))
        
        # Home locations (12)
        for letter in "ABCDEFGHIJKL":
            locations.append(cls(
                id=f"home_{letter.lower()}",
                name=f"Home-{letter}",
                category="home"
            ))
        
        # Special location
        locations.append(cls(
            id="time_machine_gateway",
            name="TimeMachineGateway",
            category="special"
        ))
        
        return locations


class WorldClock(BaseModel):
    """Global time management for the simulation."""
    
    current_time: datetime = Field(description="Current simulation time (UTC)")
    tick_duration_minutes: int = Field(default=15, description="Duration of each tick in minutes")
    tick_count: int = Field(default=0, description="Number of ticks elapsed since start")
    
    def advance_tick(self) -> None:
        """Advance the world clock by one tick."""
        self.current_time += timedelta(minutes=self.tick_duration_minutes)
        self.tick_count += 1
    
    def get_tick_start_time(self) -> datetime:
        """Get the start time of the current tick."""
        return self.current_time
    
    def get_tick_end_time(self) -> datetime:
        """Get the end time of the current tick."""
        return self.current_time + timedelta(minutes=self.tick_duration_minutes)


class Actor(BaseModel):
    """An actor in the simulation with state, resources, and scheduling."""
    
    # Identity
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique actor identifier")
    name: str = Field(description="Human-readable name of the actor")
    home_id: str = Field(description="ID of the actor's home location")
    
    # Scheduling (used by Prompt 2 scheduler)
    calendar: List[TimeBlock] = Field(default_factory=list, description="Scheduled time blocks")
    
    # Current state
    state: State = Field(default=State.Idle, description="Current state of the actor")
    substate: Optional[str] = Field(default=None, description="Optional substate for fine-grained control")
    location_id: str = Field(description="Current location ID")
    
    # Resources (0-100 scale)
    hunger: float = Field(default=20.0, ge=0.0, le=100.0, description="Hunger level (0=not hungry, 100=starving)")
    fatigue: float = Field(default=20.0, ge=0.0, le=100.0, description="Fatigue level (0=rested, 100=exhausted)")
    mood: float = Field(default=0.0, ge=-2.0, le=2.0, description="Mood level (-2=very sad, +2=very happy)")
    
    # Resource counters (to be expanded in Prompt 2)
    cash: float = Field(default=1000.0, description="Available money")
    energy: float = Field(default=100.0, ge=0.0, le=100.0, description="Physical energy level")
    battery: float = Field(default=100.0, ge=0.0, le=100.0, description="Device battery level")
    
    # Multi-world support (added for Prompt 2)
    world_id: str = Field(default="main", description="Identifies which forked world this actor belongs to")
    
    # Action duration tracking (added for Prompt 2)
    current_ticks_left: int = Field(default=0, description="Remaining ticks for current action")
    
    def update_resources(self, hunger_delta: float, fatigue_delta: float, mood_delta: float) -> None:
        """Update actor resources, clamping to valid ranges."""
        self.hunger = max(0.0, min(100.0, self.hunger + hunger_delta))
        self.fatigue = max(0.0, min(100.0, self.fatigue + fatigue_delta))
        self.mood = max(-2.0, min(2.0, self.mood + mood_delta))
    
    def get_current_time_block(self, current_time: datetime) -> Optional[TimeBlock]:
        """Get the time block that should be active at the current time."""
        for block in self.calendar:
            if block.start_dt <= current_time < block.end_dt:
                return block
        return None
    
    def is_available_at(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if the actor is available during a given time period."""
        test_block = TimeBlock(start_dt=start_time, end_dt=end_time, required_state=State.Idle)
        return not any(block.overlaps_with(test_block) for block in self.calendar)


class WorldState(BaseModel):
    """Complete state of the simulation world."""
    
    actors: Dict[str, Actor] = Field(default_factory=dict, description="All actors in the world")
    locations: Dict[str, Location] = Field(default_factory=dict, description="All locations in the world")
    clock: WorldClock = Field(description="World time management")
    world_id: str = Field(default="main", description="Unique identifier for this world instance")
    
    def add_actor(self, actor: Actor) -> None:
        """Add an actor to the world."""
        actor.world_id = self.world_id
        self.actors[actor.id] = actor
    
    def get_actor(self, actor_id: str) -> Optional[Actor]:
        """Get an actor by ID."""
        return self.actors.get(actor_id)
    
    def get_location(self, location_id: str) -> Optional[Location]:
        """Get a location by ID."""
        return self.locations.get(location_id)
    
    def get_actors_at_location(self, location_id: str) -> List[Actor]:
        """Get all actors currently at a specific location."""
        return [actor for actor in self.actors.values() if actor.location_id == location_id]
    
    def get_actors_in_state(self, state: State) -> List[Actor]:
        """Get all actors currently in a specific state."""
        return [actor for actor in self.actors.values() if actor.state == state]
    
    # TODO: Prompt 2 will add methods for:
    # - World forking/cloning for time-jump scenarios
    # - Action execution and probability calculations
    # - Advanced resource management
    
    # TODO: Prompt 3 will add methods for:
    # - Serialization for API responses
    # - Real-time state streaming
    # - Persistence layer integration