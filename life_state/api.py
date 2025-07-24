"""
FastAPI backend for life_state simulation.

Provides REST API endpoints and WebSocket connections for real-time simulation monitoring.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from .models import WorldState, Actor, Location, WorldClock
from .simulator import run, create_simulation_config, SimulationLogger, SimulationMetrics
from .time_jump import WorldManager
from . import initialize_world, create_sample_actor
from .states import State


# Pydantic models for API responses
class WorldResponse(BaseModel):
    world_id: str
    prob_mass: float

class ActorResponse(BaseModel):
    id: str
    name: str
    state: str
    location: str
    hunger: float
    fatigue: float
    mood: float

class WorldStatsResponse(BaseModel):
    avg_hunger: float
    avg_fatigue: float
    avg_mood: float
    sleeping_cnt: int
    worlds_alive: int

class TickResponse(BaseModel):
    clock: str
    actors: List[ActorResponse]
    world_stats: WorldStatsResponse


# Global state management
class SimulationManager:
    def __init__(self):
        self.worlds: Dict[str, WorldState] = {}
        self.world_manager = WorldManager()
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.simulation_running = False
        self.tick_data: Dict[str, TickResponse] = {}
        
    def get_world(self, world_id: str) -> WorldState:
        if world_id not in self.worlds:
            # Initialize a new world
            world = initialize_world(world_id)
            self.worlds[world_id] = world
        return self.worlds[world_id]
    
    def get_world_stats(self, world: WorldState) -> WorldStatsResponse:
        actors = list(world.actors.values())
        if not actors:
            return WorldStatsResponse(
                avg_hunger=0, avg_fatigue=0, avg_mood=0,
                sleeping_cnt=0, worlds_alive=len(self.worlds)
            )
        
        avg_hunger = sum(a.hunger for a in actors) / len(actors)
        avg_fatigue = sum(a.fatigue for a in actors) / len(actors)
        avg_mood = sum(a.mood for a in actors) / len(actors)
        sleeping_cnt = sum(1 for a in actors if a.state == State.Sleeping)
        
        return WorldStatsResponse(
            avg_hunger=avg_hunger,
            avg_fatigue=avg_fatigue,
            avg_mood=avg_mood,
            sleeping_cnt=sleeping_cnt,
            worlds_alive=len(self.worlds)
        )
    
    def get_tick_data(self, world_id: str, tick_n: int) -> TickResponse:
        world = self.get_world(world_id)
        
        # Convert actors to response format
        actor_responses = []
        for actor in world.actors.values():
            location_name = world.locations.get(actor.location_id, Location(id="unknown", name="Unknown", category="unknown")).name
            actor_responses.append(ActorResponse(
                id=actor.id,
                name=actor.name,
                state=actor.state.name,
                location=location_name,
                hunger=actor.hunger,
                fatigue=actor.fatigue,
                mood=actor.mood
            ))
        
        world_stats = self.get_world_stats(world)
        
        return TickResponse(
            clock=world.clock.current_time.isoformat() + "Z",
            actors=actor_responses,
            world_stats=world_stats
        )
    
    async def broadcast_to_world(self, world_id: str, data: Dict[str, Any]):
        if world_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[world_id]:
                try:
                    await websocket.send_json(data)
                except:
                    disconnected.append(websocket)
            
            # Remove disconnected websockets
            for ws in disconnected:
                self.active_connections[world_id].remove(ws)


# Global simulation manager instance
sim_manager = SimulationManager()

# Create FastAPI app
app = FastAPI(
    title="Life State Simulation API",
    description="API for managing and observing life state simulations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],  # Vite and React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# REST API Endpoints

@app.get("/api/worlds", response_model=List[WorldResponse])
async def get_worlds():
    """Get all available worlds with their probability masses."""
    worlds = []
    for world_id, world in sim_manager.worlds.items():
        # For now, all worlds have equal probability mass
        worlds.append(WorldResponse(world_id=world_id, prob_mass=1.0))
    
    # If no worlds exist, create a default one
    if not worlds:
        default_world = sim_manager.get_world("main")
        worlds.append(WorldResponse(world_id="main", prob_mass=1.0))
    
    return worlds


@app.get("/api/worlds/{world_id}/tick/{tick_n}", response_model=TickResponse)
async def get_world_tick(world_id: str, tick_n: int):
    """Get world state at a specific tick."""
    try:
        tick_data = sim_manager.get_tick_data(world_id, tick_n)
        sim_manager.tick_data[f"{world_id}:{tick_n}"] = tick_data
        return tick_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"World {world_id} not found: {str(e)}")


@app.websocket("/ws/worlds/{world_id}")
async def websocket_world_updates(websocket: WebSocket, world_id: str):
    """WebSocket endpoint for real-time world updates."""
    await websocket.accept()
    
    # Add to active connections
    if world_id not in sim_manager.active_connections:
        sim_manager.active_connections[world_id] = []
    sim_manager.active_connections[world_id].append(websocket)
    
    try:
        # Send initial world state
        world = sim_manager.get_world(world_id)
        initial_data = sim_manager.get_tick_data(world_id, world.clock.tick_count)
        await websocket.send_json(initial_data.dict())
        
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(1.0)  # Send updates every second
            try:
                current_data = sim_manager.get_tick_data(world_id, world.clock.tick_count)
                await websocket.send_json(current_data.dict())
            except Exception as e:
                print(f"Error sending WebSocket update: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Remove from active connections
        if world_id in sim_manager.active_connections:
            sim_manager.active_connections[world_id].remove(websocket)


@app.post("/api/worlds/{world_id}/start")
async def start_simulation(world_id: str, background_tasks: BackgroundTasks):
    """Start simulation for a world."""
    world = sim_manager.get_world(world_id)
    
    if sim_manager.simulation_running:
        raise HTTPException(status_code=400, detail="Simulation already running")
    
    # Start simulation in background
    def run_simulation():
        from datetime import datetime, timedelta
        import time
        
        sim_manager.simulation_running = True
        end_time = datetime.now() + timedelta(hours=24)  # Run for 24 hours
        
        try:
            while world.clock.current_time < end_time and sim_manager.simulation_running:
                # Advance world by one tick
                world.clock.advance_tick()
                
                # Update actors (simplified for now)
                for actor in world.actors.values():
                    # Simple resource updates
                    actor.update_resources(
                        hunger_delta=1.0,  # Hunger increases
                        fatigue_delta=0.5,  # Fatigue increases slowly
                        mood_delta=0.0     # Mood stays stable
                    )
                
                # Broadcast updates to WebSocket clients
                asyncio.create_task(sim_manager.broadcast_to_world(
                    world_id, 
                    sim_manager.get_tick_data(world_id, world.clock.tick_count).dict()
                ))
                
                time.sleep(0.1)  # Small delay between ticks
                
        except Exception as e:
            print(f"Simulation error: {e}")
        finally:
            sim_manager.simulation_running = False
    
    background_tasks.add_task(run_simulation)
    return {"message": f"Simulation started for world {world_id}"}


@app.post("/api/worlds/{world_id}/stop")
async def stop_simulation(world_id: str):
    """Stop simulation for a world."""
    sim_manager.simulation_running = False
    return {"message": f"Simulation stopped for world {world_id}"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Serve React app (when built)
try:
    app.mount("/", StaticFiles(directory="ui/dist", html=True), name="static")
except:
    # If React app isn't built yet, just serve a simple message
    @app.get("/")
    async def root():
        return {"message": "Life State API is running. React frontend not yet built."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)