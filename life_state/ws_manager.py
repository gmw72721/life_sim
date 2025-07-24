"""
WebSocket manager for broadcasting simulation updates.

Handles WebSocket connections and real-time data broadcasting for the life_state simulation.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        # world_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Track connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, world_id: str, client_id: Optional[str] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if world_id not in self.active_connections:
            self.active_connections[world_id] = []
        
        self.active_connections[world_id].append(websocket)
        self.connection_metadata[websocket] = {
            'world_id': world_id,
            'client_id': client_id,
            'connected_at': asyncio.get_event_loop().time()
        }
        
        logger.info(f"Client connected to world {world_id}. Total connections: {len(self.active_connections[world_id])}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.connection_metadata:
            world_id = self.connection_metadata[websocket]['world_id']
            
            if world_id in self.active_connections:
                try:
                    self.active_connections[world_id].remove(websocket)
                    logger.info(f"Client disconnected from world {world_id}. Remaining connections: {len(self.active_connections[world_id])}")
                except ValueError:
                    pass  # Connection already removed
            
            del self.connection_metadata[websocket]
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_world(self, world_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections for a specific world."""
        if world_id not in self.active_connections:
            return
        
        disconnected_connections = []
        
        for connection in self.active_connections[world_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to connection: {e}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all active connections."""
        for world_id in self.active_connections:
            await self.broadcast_to_world(world_id, message)
    
    def get_world_connection_count(self, world_id: str) -> int:
        """Get the number of active connections for a world."""
        return len(self.active_connections.get(world_id, []))
    
    def get_total_connection_count(self) -> int:
        """Get the total number of active connections."""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_world_list(self) -> List[str]:
        """Get a list of all worlds with active connections."""
        return list(self.active_connections.keys())


class TickBroadcaster:
    """Handles periodic broadcasting of simulation tick data."""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.broadcast_tasks: Dict[str, asyncio.Task] = {}
        self.broadcast_intervals: Dict[str, float] = {}  # world_id -> interval in seconds
    
    def start_broadcasting(self, world_id: str, interval: float = 1.0):
        """Start periodic broadcasting for a world."""
        if world_id in self.broadcast_tasks:
            self.stop_broadcasting(world_id)
        
        self.broadcast_intervals[world_id] = interval
        self.broadcast_tasks[world_id] = asyncio.create_task(
            self._broadcast_loop(world_id)
        )
        logger.info(f"Started broadcasting for world {world_id} with {interval}s interval")
    
    def stop_broadcasting(self, world_id: str):
        """Stop periodic broadcasting for a world."""
        if world_id in self.broadcast_tasks:
            self.broadcast_tasks[world_id].cancel()
            del self.broadcast_tasks[world_id]
        
        if world_id in self.broadcast_intervals:
            del self.broadcast_intervals[world_id]
        
        logger.info(f"Stopped broadcasting for world {world_id}")
    
    async def _broadcast_loop(self, world_id: str):
        """Internal broadcast loop for a specific world."""
        try:
            while True:
                interval = self.broadcast_intervals.get(world_id, 1.0)
                await asyncio.sleep(interval)
                
                # Check if there are still connections for this world
                if self.connection_manager.get_world_connection_count(world_id) == 0:
                    logger.info(f"No connections for world {world_id}, stopping broadcast")
                    break
                
                # This would be called by the simulation manager
                # For now, we just continue the loop
                
        except asyncio.CancelledError:
            logger.info(f"Broadcast loop cancelled for world {world_id}")
        except Exception as e:
            logger.error(f"Error in broadcast loop for world {world_id}: {e}")
    
    def cleanup(self):
        """Cancel all broadcasting tasks."""
        for world_id in list(self.broadcast_tasks.keys()):
            self.stop_broadcasting(world_id)


# Global connection manager instance
connection_manager = ConnectionManager()
tick_broadcaster = TickBroadcaster(connection_manager)


async def handle_websocket_connection(websocket: WebSocket, world_id: str):
    """Handle a WebSocket connection lifecycle."""
    await connection_manager.connect(websocket, world_id)
    
    # Start broadcasting if this is the first connection to this world
    if connection_manager.get_world_connection_count(world_id) == 1:
        tick_broadcaster.start_broadcasting(world_id)
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_json()
            
            # Handle client messages (e.g., subscription changes, commands)
            if data.get('type') == 'ping':
                await connection_manager.send_personal_message(
                    {'type': 'pong', 'timestamp': asyncio.get_event_loop().time()},
                    websocket
                )
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connection_manager.disconnect(websocket)
        
        # Stop broadcasting if no more connections to this world
        if connection_manager.get_world_connection_count(world_id) == 0:
            tick_broadcaster.stop_broadcasting(world_id)