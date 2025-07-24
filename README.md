# Life State Simulation

A comprehensive actor-based life modeling simulation framework with time-jumping capabilities and multi-world timeline management.

## Overview

Life State is a simulation framework that models autonomous actors living their lives through various states and activities. The system includes:

- **60+ Actions** across work, social, leisure, exercise, shopping, and commuting activities
- **Probability-based decision making** influenced by needs, mood, time, and environment  
- **Calendar scheduling** with hard constraints and emergency overrides
- **Time-jumping mechanics** that create parallel world timelines
- **Multi-world simulation** with probability mass tracking
- **Comprehensive logging** and metrics collection

## Architecture

The system is built in three layers:

### Prompt 1: Foundation (✅ Complete)
- Core data models (Actor, Location, TimeBlock, WorldState)
- Basic state management (8 core states)
- Time system (15-minute ticks)
- Resource tracking (hunger, fatigue, mood, cash, energy, battery)

### Prompt 2: Actions & Simulation (✅ Complete)
- Full action system with 60+ concrete actions
- Probability engine with need-based modifiers
- Time-jump mechanics with world forking
- Calendar enforcement system
- Complete simulation loop with logging

### Prompt 3: API & UI (🚧 Planned)
- FastAPI backend with REST endpoints
- WebSocket real-time updates
- React/Tailwind frontend
- Authentication and user management

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd life_state

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from life_state import initialize_world, create_sample_actor, run
from datetime import datetime, timedelta
from pathlib import Path

# Create a world
world = initialize_world(start_time=datetime(2024, 1, 1, 9, 0))

# Add some actors
alice = create_sample_actor(world, "Alice", "A")
bob = create_sample_actor(world, "Bob", "B")

# Run simulation for 24 hours
end_time = world.clock.current_time + timedelta(hours=24)
log_dir = Path("simulation_logs")

run({"main": world}, end_time, log_dir)
```

### Command Line Interface

```bash
# Run a 24-hour simulation with 3 actors
python -m life_state.cli run --minutes 1440 --actors 3

# Run parallel simulation with time-jumping
python -m life_state.cli parallel --actors 5 --ticks 200

# Show configuration
python -m life_state.cli config
```

## Core Concepts

### States

Actors can be in one of 15 states:

**Core States (Prompt 1):**
- Sleeping, Waking_Up, Idle, Transitioning
- Driving, Walking, Focused_Work, Eating

**Extended States (Prompt 2):**
- Commuting, Socialising, Leisure, Shopping
- Exercising, In_Meeting, TimeJumping

### Actions

60+ actions are available across categories:
- **Work**: Start work, meetings, commuting
- **Social**: Meet colleagues, chat with friends, networking
- **Leisure**: Watch movies, read books, relax at home
- **Exercise**: Gym workouts, jogging, home exercise
- **Shopping**: Grocery shopping, mall visits, window shopping
- **Movement**: Travel between locations
- **Special**: Time jumping between timelines

### Probability System

Action selection uses weighted probability based on:
- **Actor Needs**: Hunger, fatigue, mood levels
- **Environmental Factors**: Location, time of day, other actors present
- **Schedule Constraints**: Calendar commitments and preparation time
- **Random Events**: Weather, equipment failures, social encounters

### Time Jumping

Actors can perform time jumps under specific conditions:
- Must be at TimeMachineGateway location
- Early morning (6-8 AM) or late night (22+ PM)
- Positive or neutral mood
- Creates parallel world timelines with probability mass splitting

### Calendar System

Actors have calendars with hard scheduling constraints:
- **Override System**: Calendar commitments override probability decisions
- **Emergency Breaks**: Critical hunger/fatigue can break schedules
- **Preparation Logic**: Actors prepare for upcoming commitments
- **Conflict Detection**: Identifies and suggests schedule optimizations

## Project Structure

```
life_state/
├── __init__.py              # Main package exports
├── config.yaml              # Configuration parameters
├── models.py                # Core data models (Pydantic)
├── states.py                # State enum and transitions
├── world.py                 # World initialization
├── tick_engine.py           # Basic tick processing
│
├── # Prompt 2 Implementation
├── actions.py               # 60+ action definitions
├── probability.py           # Probability calculation engine
├── calendar_scheduler.py    # Calendar constraint system
├── time_jump.py             # World forking and time travel
├── simulator.py             # Main simulation loop
├── io_utils.py              # Logging and persistence
├── cli.py                   # Command-line interface
│
├── # Prompt 3 Placeholders
├── api.py                   # FastAPI backend (placeholder)
├── ui/README.md             # React frontend plan
│
└── tests/                   # Test suite
    ├── test_models.py       # Model tests
    ├── test_choose_action.py # Action selection tests
    ├── test_time_jump.py    # Time jump tests
    └── test_calendar.py     # Calendar tests
```

## Configuration

The simulation behavior is controlled via `config.yaml`:

```yaml
# Resource depletion rates (per 15-minute tick)
fatigue_rate:
  sleeping: -5.0      # recovers fatigue
  focused_work: 3.0   # increases fatigue
  
hunger_rate:
  eating: -15.0       # reduces hunger
  walking: 1.5        # increases hunger

mood_modifiers:
  socialising: 0.15   # improves mood
  exercising: 0.05    # slight mood boost
```

## Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest life_state/tests/test_choose_action.py
pytest life_state/tests/test_time_jump.py
pytest life_state/tests/test_calendar.py

# Run with coverage
pytest --cov=life_state
```

## Examples

### Simple Simulation

```python
from life_state import initialize_world, create_sample_actor, advance_world

# Create world and actors
world = initialize_world()
alice = create_sample_actor(world, "Alice", "A")

# Run for 10 ticks manually
for tick in range(10):
    advance_world(world)
    print(f"Tick {tick}: Alice is {alice.state.name} at {alice.location_id}")
```

### Multi-World Time Jumping

```python
from life_state import WorldManager, initialize_world, create_sample_actor
from life_state.simulator import run_parallel_simulation

# Set up world manager
manager = WorldManager()
world = initialize_world()
create_sample_actor(world, "Alice", "A")
manager.add_world(world)

# Run with automatic time-jumping
run_parallel_simulation(manager, num_ticks=100)

# Check resulting timelines
summary = manager.get_summary()
print(f"Created {summary['total_worlds']} worlds")
```

### Custom Action Probability

```python
from life_state.probability import choose_action, calculate_action_probability
from life_state.actions import EAT_MEAL

# Check probability of eating when very hungry
actor.hunger = 95.0
prob = calculate_action_probability(EAT_MEAL, actor, world)
print(f"Eating probability when very hungry: {prob:.2f}")

# Choose action with probability weighting
chosen = choose_action(actor, world)
print(f"Chosen action: {chosen.name}")
```

## Logging and Output

The simulation generates comprehensive logs:

- **Snapshots**: JSON Lines format with actor states per tick
- **Daily Summaries**: Aggregated statistics per simulation day  
- **Final Summary**: Complete simulation metrics and outcomes
- **CSV Export**: Tabular data for analysis
- **Event Logs**: Action executions, state changes, time jumps

## Performance

- **Tick Rate**: ~1000 ticks/second for 5 actors on modern hardware
- **Memory Usage**: ~50MB for 10 actors across 5 worlds
- **Scaling**: Linear with number of actors and worlds
- **Optimization**: Automatic pruning of low-probability timelines

## Development

### Adding New Actions

1. Define action in `actions.py`:
```python
NEW_ACTION = Action(
    name="My New Action",
    resulting_state=State.Leisure,
    duration_ticks=2,
    location_req=["public_park"],
    hunger_delta=5,
    weight=1.3
)
```

2. Add to `ALL_ACTIONS` list
3. Update tests in `test_choose_action.py`

### Extending Probability Factors

Add new modifiers in `probability.py`:
```python
def custom_factor(actor, world_state) -> float:
    # Your probability logic here
    return 1.0

# Use in calculate_action_probability()
prob *= custom_factor(actor, world_state)
```

## Roadmap

### Prompt 3: API & Frontend (Planned)
- [ ] FastAPI REST endpoints
- [ ] WebSocket real-time updates  
- [ ] React dashboard with Tailwind CSS
- [ ] User authentication and management
- [ ] Interactive timeline visualization
- [ ] Real-time actor monitoring

### Future Enhancements
- [ ] Machine learning for actor behavior
- [ ] Complex social interactions
- [ ] Economic simulation layer
- [ ] Weather and environmental systems
- [ ] Persistence and save/load functionality

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built as a foundation for complex life simulation modeling
- Designed for extensibility and real-world applicability
- Inspired by agent-based modeling and discrete event simulation